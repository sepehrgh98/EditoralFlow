import pytest
from pydantic import BaseModel

from app.llm.base import LLMClient, LLMError, LLMOutputError, LLMResponse, Usage
from tests.fakes import FakeCall, FakeLLM


class Verdict(BaseModel):
    score: int
    summary: str


def test_fake_is_an_llm_client() -> None:
    assert isinstance(FakeLLM(), LLMClient)


def test_llm_client_cannot_be_used_without_implementing_methods() -> None:
    with pytest.raises(TypeError):
        LLMClient()  # type: ignore[abstract]


async def test_generate_returns_answers_in_order() -> None:
    llm = FakeLLM(["first", "second"])

    one = await llm.generate("a")
    two = await llm.generate("b")

    assert (one.content, two.content) == ("first", "second")
    assert isinstance(one, LLMResponse)


async def test_generate_structured_accepts_dict_json_and_model() -> None:
    llm = FakeLLM(
        [
            {"score": 8, "summary": "dict"},
            '{"score": 7, "summary": "json"}',
            Verdict(score=6, summary="model"),
        ]
    )

    results = [(await llm.generate_structured("p", Verdict)).content for _ in range(3)]

    assert all(isinstance(r, Verdict) for r in results)
    assert [r.score for r in results] == [8, 7, 6]


async def test_wrong_shape_raises_output_error() -> None:
    llm = FakeLLM([{"score": "not a number", "summary": "x"}, '{"broken json'])

    with pytest.raises(LLMOutputError, match="Verdict"):
        await llm.generate_structured("p", Verdict)
    with pytest.raises(LLMOutputError):
        await llm.generate_structured("p", Verdict)


async def test_records_calls() -> None:
    llm = FakeLLM(["text", {"score": 1, "summary": "s"}])

    await llm.generate("hello", system="be brief")
    await llm.generate_structured("judge this", Verdict, tier="strong")

    assert llm.calls == [
        FakeCall("generate", "hello", "be brief", "fast"),
        FakeCall("generate_structured", "judge this", None, "strong", Verdict),
    ]


async def test_raises_queued_exception() -> None:
    llm = FakeLLM([LLMError("rate limited"), "ok"])

    with pytest.raises(LLMError, match="rate limited"):
        await llm.generate("p")
    assert (await llm.generate("p")).content == "ok"


async def test_no_answers_left_is_clear() -> None:
    llm = FakeLLM()

    with pytest.raises(LLMError, match="no answers left"):
        await llm.generate("p")


async def test_add_queues_more_answers() -> None:
    llm = FakeLLM()
    llm.add("later")

    assert (await llm.generate("p")).content == "later"


async def test_generate_rejects_non_text_answer() -> None:
    llm = FakeLLM([{"score": 1, "summary": "s"}])

    with pytest.raises(TypeError, match="str answer"):
        await llm.generate("p")


async def test_usage_is_recorded_with_tier() -> None:
    llm = FakeLLM(["x"])

    usage = (await llm.generate("p", tier="strong")).usage

    assert usage == Usage(
        model="fake-strong", input_tokens=0, output_tokens=0, latency_ms=0.0, cost_usd=0.0
    )
    assert usage.total_tokens == 0


def test_usage_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        Usage(model="m", input_tokens=-1, output_tokens=0, latency_ms=0)


async def test_responder_picks_answer_from_the_call() -> None:
    async def responder(call: FakeCall) -> str:
        return "for grammar" if "grammar" in call.prompt else "for style"

    llm = FakeLLM(responder=responder)

    assert (await llm.generate("check style")).content == "for style"
    assert (await llm.generate("check grammar")).content == "for grammar"
    assert len(llm.calls) == 2


async def test_responder_can_raise() -> None:
    async def responder(call: FakeCall) -> Exception:
        return LLMError("down")

    with pytest.raises(LLMError, match="down"):
        await FakeLLM(responder=responder).generate("p")
