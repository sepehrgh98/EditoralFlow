"""Test doubles. `FakeLLM` is a stand-in LLM: returns canned answers and records every call.

Lives in tests/ because only tests use it; production code never imports from here.
"""

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from app.llm.base import LLMClient, LLMError, LLMOutputError, LLMResponse, ModelTier, Usage

# A canned answer: text, a model instance, a dict, or an exception to raise.
FakeAnswer = str | BaseModel | dict[str, Any] | Exception


@dataclass(frozen=True)
class FakeCall:
    """One recorded call, so tests can check what an agent sent."""

    method: Literal["generate", "generate_structured"]
    prompt: str
    system: str | None
    tier: ModelTier
    schema: type[BaseModel] | None = None


class FakeLLM(LLMClient):
    """Returns the given answers in order, one per call.

    Structured answers are validated against the requested schema, exactly like a real
    client would, so a test with wrongly shaped data fails.
    """

    def __init__(self, answers: Iterable[FakeAnswer] = ()) -> None:
        self._answers: deque[FakeAnswer] = deque(answers)
        self.calls: list[FakeCall] = []

    def add(self, *answers: FakeAnswer) -> None:
        """Queue more answers."""
        self._answers.extend(answers)

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        tier: ModelTier = "fast",
    ) -> LLMResponse[str]:
        self.calls.append(FakeCall("generate", prompt, system, tier))
        answer = self._next_answer()
        if not isinstance(answer, str):
            raise TypeError(f"generate() needs a str answer, got {type(answer).__name__}")
        return LLMResponse(content=answer, usage=self._usage(tier))

    async def generate_structured[S: BaseModel](
        self,
        prompt: str,
        schema: type[S],
        *,
        system: str | None = None,
        tier: ModelTier = "fast",
    ) -> LLMResponse[S]:
        self.calls.append(FakeCall("generate_structured", prompt, system, tier, schema))
        answer = self._next_answer()
        try:
            if isinstance(answer, str):
                content = schema.model_validate_json(answer)
            elif isinstance(answer, BaseModel):
                content = schema.model_validate(answer.model_dump())
            else:
                content = schema.model_validate(answer)
        except ValidationError as exc:
            raise LLMOutputError(f"Answer does not match {schema.__name__}: {exc}") from exc
        return LLMResponse(content=content, usage=self._usage(tier))

    def _next_answer(self) -> FakeAnswer:
        if not self._answers:
            raise LLMError(f"FakeLLM has no answers left (call #{len(self.calls)})")
        answer = self._answers.popleft()
        if isinstance(answer, Exception):
            raise answer
        return answer

    @staticmethod
    def _usage(tier: ModelTier) -> Usage:
        return Usage(
            model=f"fake-{tier}", input_tokens=0, output_tokens=0, latency_ms=0.0, cost_usd=0.0
        )
