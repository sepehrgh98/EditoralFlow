"""The interface every LLM client implements, and the data shapes it returns.

Agents depend only on `LLMClient`, never on a provider SDK. That makes the provider a
settings choice and lets tests swap in `FakeLLM`.
"""

import logging
from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

# Agents ask for a tier; each client maps it to a model name from settings.
ModelTier = Literal["fast", "strong"]


class Usage(BaseModel):
    """What one LLM call cost: tokens, time and money."""

    model: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    latency_ms: float = Field(ge=0)
    cost_usd: float | None = Field(default=None, ge=0)  # None when the price is unknown

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


def log_usage(logger: logging.Logger, usage: Usage) -> None:
    """Write one log line per LLM call, so every call's cost is visible."""
    cost = "unknown" if usage.cost_usd is None else f"${usage.cost_usd:.6f}"
    logger.info(
        "llm call model=%s in=%d out=%d latency=%.0fms cost=%s",
        usage.model,
        usage.input_tokens,
        usage.output_tokens,
        usage.latency_ms,
        cost,
    )


class LLMResponse[T](BaseModel):
    """The answer of one LLM call plus its usage record."""

    content: T
    usage: Usage


class LLMError(Exception):
    """An LLM call failed (network, rate limit, timeout, ...)."""


class LLMOutputError(LLMError):
    """The model answered, but not in the requested shape."""


class LLMClient(ABC):
    """Talks to one AI model provider. All calls are async."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        tier: ModelTier = "fast",
    ) -> LLMResponse[str]:
        """Return a free-text answer."""

    @abstractmethod
    async def generate_structured[S: BaseModel](
        self,
        prompt: str,
        schema: type[S],
        *,
        system: str | None = None,
        tier: ModelTier = "fast",
    ) -> LLMResponse[S]:
        """Return an answer validated against `schema`.

        Raises `LLMOutputError` if the answer does not fit the schema.
        """
