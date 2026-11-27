"""LLM client for local models served by Ollama (free, runs on this machine)."""

import logging
import time
from typing import Any

import httpx
import ollama
from ollama import AsyncClient, ChatResponse
from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.llm.base import (
    LLMClient,
    LLMError,
    LLMOutputError,
    LLMResponse,
    ModelTier,
    Usage,
    log_usage,
)

logger = logging.getLogger(__name__)


class OllamaClient(LLMClient):
    """Calls a model on a local Ollama server.

    Structured output: Ollama's `format` parameter takes the JSON schema and constrains the
    model's answer to it. We still validate with Pydantic and retry once if it fails.

    Retries: a local server has no rate limits, so there is no backoff. If Ollama is not
    running, the call fails at once with a clear message.
    """

    def __init__(self, settings: Settings, sdk: AsyncClient | None = None) -> None:
        self._sdk = sdk or AsyncClient(
            host=settings.ollama_host, timeout=settings.llm_timeout_seconds
        )
        self._host = settings.ollama_host
        self._options = {"num_ctx": settings.ollama_num_ctx, "num_predict": settings.llm_max_tokens}
        self._think = settings.ollama_think
        self._models: dict[ModelTier, str] = {
            "fast": settings.ollama_fast_model,
            "strong": settings.ollama_strong_model,
        }

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        tier: ModelTier = "fast",
    ) -> LLMResponse[str]:
        model = self._models[tier]
        response, latency_ms = await self._call(model, prompt, system, json_schema=None)
        usage = _usage(model, [response], latency_ms)
        log_usage(logger, usage)
        return LLMResponse(content=response.message.content or "", usage=usage)

    async def generate_structured[S: BaseModel](
        self,
        prompt: str,
        schema: type[S],
        *,
        system: str | None = None,
        tier: ModelTier = "fast",
    ) -> LLMResponse[S]:
        model = self._models[tier]
        json_schema = schema.model_json_schema()
        responses: list[ChatResponse] = []
        total_latency_ms = 0.0

        for attempt in (1, 2):  # one retry if the answer does not fit the schema
            response, latency_ms = await self._call(model, prompt, system, json_schema)
            responses.append(response)
            total_latency_ms += latency_ms
            try:
                content = schema.model_validate_json(response.message.content or "")
            except ValidationError as exc:
                logger.warning(
                    "answer does not match %s (attempt %d): %s", schema.__name__, attempt, exc
                )
                continue
            usage = _usage(model, responses, total_latency_ms)
            log_usage(logger, usage)
            return LLMResponse(content=content, usage=usage)

        log_usage(logger, _usage(model, responses, total_latency_ms))
        raise LLMOutputError(f"{model}'s answer did not match {schema.__name__} after 2 attempts")

    async def _call(
        self,
        model: str,
        prompt: str,
        system: str | None,
        json_schema: dict[str, Any] | None,
    ) -> tuple[ChatResponse, float]:
        """Send one request. Returns the response and its latency; raises LLMError on failure."""
        messages = [{"role": "system", "content": system}] if system else []
        messages.append({"role": "user", "content": prompt})

        start = time.perf_counter()
        try:
            response = await self._sdk.chat(
                model=model,
                messages=messages,
                format=json_schema,
                options=self._options,
                think=self._think,
            )
        except ConnectionError as exc:
            raise LLMError(
                f"Ollama is not reachable at {self._host}. Is it running? (start the Ollama app "
                "or run `ollama serve`)"
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMError(f"Ollama call to {model} timed out") from exc
        except ollama.ResponseError as exc:
            if exc.status_code == 404:
                raise LLMError(
                    f"Model {model} is not downloaded. Run: ollama pull {model}"
                ) from exc
            raise LLMError(f"Ollama error {exc.status_code}: {exc.error}") from exc
        latency_ms = (time.perf_counter() - start) * 1000

        if response.done_reason == "length":
            raise LLMOutputError(f"{model}'s answer was cut off (raise LLM_MAX_TOKENS)")
        return response, latency_ms


def _usage(model: str, responses: list[ChatResponse], latency_ms: float) -> Usage:
    """Add up tokens over all attempts. Local models cost nothing."""
    return Usage(
        model=model,
        input_tokens=sum(r.prompt_eval_count or 0 for r in responses),
        output_tokens=sum(r.eval_count or 0 for r in responses),
        latency_ms=latency_ms,
        cost_usd=0.0,
    )
