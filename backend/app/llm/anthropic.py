"""LLM client for Claude via the Anthropic API (paid per token)."""

import logging
import time

import anthropic
from anthropic import AsyncAnthropic, transform_schema
from anthropic.types import Message
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
from app.llm.pricing import estimate_cost

logger = logging.getLogger(__name__)


class AnthropicClient(LLMClient):
    """Calls Claude.

    Retries and timeouts: the Anthropic SDK retries rate limits (429), server errors (5xx)
    and network errors with exponential backoff, `llm_max_retries` times, and stops each
    attempt after `llm_timeout_seconds`.

    Structured output: JSON outputs (`output_config.format`). The API makes Claude answer
    in the schema's shape; we still validate with Pydantic and retry once if it fails.
    """

    def __init__(self, settings: Settings, sdk: AsyncAnthropic | None = None) -> None:
        if sdk is None:
            if settings.anthropic_api_key is None:
                raise LLMError("ANTHROPIC_API_KEY is not set")
            sdk = AsyncAnthropic(
                api_key=settings.anthropic_api_key.get_secret_value(),
                timeout=settings.llm_timeout_seconds,
                max_retries=settings.llm_max_retries,
            )
        self._sdk = sdk
        self._max_tokens = settings.llm_max_tokens
        self._models: dict[ModelTier, str] = {
            "fast": settings.anthropic_fast_model,
            "strong": settings.anthropic_strong_model,
        }

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        tier: ModelTier = "fast",
    ) -> LLMResponse[str]:
        model = self._models[tier]
        message, latency_ms = await self._call(model, prompt, system, output_format=None)
        usage = self._usage(model, [message], latency_ms)
        log_usage(logger, usage)
        return LLMResponse(content=_text_of(message), usage=usage)

    async def generate_structured[S: BaseModel](
        self,
        prompt: str,
        schema: type[S],
        *,
        system: str | None = None,
        tier: ModelTier = "fast",
    ) -> LLMResponse[S]:
        model = self._models[tier]
        output_format = {"type": "json_schema", "schema": transform_schema(schema)}
        messages: list[Message] = []
        total_latency_ms = 0.0

        for attempt in (1, 2):  # one retry if the answer does not fit the schema
            message, latency_ms = await self._call(model, prompt, system, output_format)
            messages.append(message)
            total_latency_ms += latency_ms
            try:
                content = schema.model_validate_json(_text_of(message))
            except ValidationError as exc:
                logger.warning(
                    "answer does not match %s (attempt %d): %s", schema.__name__, attempt, exc
                )
                continue
            usage = self._usage(model, messages, total_latency_ms)
            log_usage(logger, usage)
            return LLMResponse(content=content, usage=usage)

        log_usage(logger, self._usage(model, messages, total_latency_ms))
        raise LLMOutputError(f"Claude's answer did not match {schema.__name__} after 2 attempts")

    async def _call(
        self,
        model: str,
        prompt: str,
        system: str | None,
        output_format: dict[str, object] | None,
    ) -> tuple[Message, float]:
        """Send one request. Returns the message and its latency; raises LLMError on failure."""
        kwargs: dict[str, object] = {
            "model": model,
            "max_tokens": self._max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        if output_format:
            kwargs["output_config"] = {"format": output_format}

        start = time.perf_counter()
        try:
            message = await self._sdk.messages.create(**kwargs)  # type: ignore[call-overload]
        except anthropic.AuthenticationError as exc:
            raise LLMError("Anthropic rejected the API key (check ANTHROPIC_API_KEY)") from exc
        except anthropic.RateLimitError as exc:
            raise LLMError("Anthropic rate limit hit; retries exhausted") from exc
        except anthropic.APITimeoutError as exc:
            raise LLMError("Anthropic request timed out; retries exhausted") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMError("Could not connect to the Anthropic API") from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"Anthropic API error {exc.status_code}: {exc.message}") from exc
        latency_ms = (time.perf_counter() - start) * 1000

        if message.stop_reason == "refusal":
            raise LLMError("Claude declined to answer this request (stop_reason=refusal)")
        if message.stop_reason == "max_tokens":
            raise LLMOutputError(
                f"Claude's answer was cut off at {self._max_tokens} tokens (raise LLM_MAX_TOKENS)"
            )
        return message, latency_ms

    @staticmethod
    def _usage(model: str, messages: list[Message], latency_ms: float) -> Usage:
        """Add up tokens over all attempts, so a retried call shows its full cost."""
        input_tokens = sum(m.usage.input_tokens for m in messages)
        output_tokens = sum(m.usage.output_tokens for m in messages)
        return Usage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=estimate_cost(model, input_tokens, output_tokens),
        )


def _text_of(message: Message) -> str:
    """Join the text blocks of a reply (thinking blocks are skipped)."""
    return "".join(block.text for block in message.content if block.type == "text")
