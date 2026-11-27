"""OllamaClient with the Ollama SDK replaced by a stand-in: no server needed."""

from typing import Any

import httpx
import ollama
import pytest
from ollama import ChatResponse
from pydantic import BaseModel

from app.core.config import Settings
from app.llm.base import LLMError, LLMOutputError
from app.llm.ollama import OllamaClient


class Verdict(BaseModel):
    score: int
    summary: str


def reply(
    content: str, done_reason: str = "stop", tokens: tuple[int, int] = (50, 10)
) -> ChatResponse:
    return ChatResponse.model_validate(
        {
            "model": "qwen3:8b",
            "message": {"role": "assistant", "content": content},
            "done": True,
            "done_reason": done_reason,
            "prompt_eval_count": tokens[0],
            "eval_count": tokens[1],
        }
    )


class FakeOllama:
    def __init__(self, replies: list[ChatResponse | Exception]) -> None:
        self.replies = replies
        self.requests: list[dict[str, Any]] = []

    async def chat(self, **kwargs: Any) -> ChatResponse:
        self.requests.append(kwargs)
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make_client(
    replies: list[ChatResponse | Exception], **settings: Any
) -> tuple[OllamaClient, FakeOllama]:
    sdk = FakeOllama(replies)
    client = OllamaClient(Settings(_env_file=None, **settings), sdk=sdk)  # type: ignore[arg-type,call-arg]
    return client, sdk


async def test_generate_returns_text_and_free_usage() -> None:
    client, sdk = make_client([reply("Hello")])

    response = await client.generate("hi", system="be brief")

    assert response.content == "Hello"
    assert response.usage.model == "qwen3:8b"
    assert (response.usage.input_tokens, response.usage.output_tokens) == (50, 10)
    assert response.usage.cost_usd == 0.0
    assert sdk.requests[0]["messages"][0] == {"role": "system", "content": "be brief"}
    assert sdk.requests[0]["format"] is None


async def test_sends_settings_to_ollama() -> None:
    client, sdk = make_client(
        [reply("x")], ollama_num_ctx=8192, llm_max_tokens=500, ollama_think=True
    )

    await client.generate("hi", tier="strong")

    request = sdk.requests[0]
    assert request["model"] == "qwen3:14b"
    assert request["options"] == {"num_ctx": 8192, "num_predict": 500}
    assert request["think"] is True


async def test_structured_sends_schema_and_validates() -> None:
    client, sdk = make_client([reply('{"score": 7, "summary": "fine"}')])

    response = await client.generate_structured("judge", Verdict)

    assert response.content == Verdict(score=7, summary="fine")
    assert sdk.requests[0]["format"]["properties"].keys() == {"score", "summary"}


async def test_structured_retries_once_then_fails() -> None:
    client, sdk = make_client([reply("nope"), reply('{"score": 1}')])

    with pytest.raises(LLMOutputError, match="Verdict"):
        await client.generate_structured("judge", Verdict)
    assert len(sdk.requests) == 2


async def test_structured_retry_can_succeed() -> None:
    client, _ = make_client([reply("nope"), reply('{"score": 2, "summary": "s"}')])

    response = await client.generate_structured("judge", Verdict)

    assert response.content.score == 2
    assert response.usage.input_tokens == 100  # both attempts counted


async def test_cut_off_answer_raises_output_error() -> None:
    client, _ = make_client([reply('{"score": 1, "su', done_reason="length")])

    with pytest.raises(LLMOutputError, match="cut off"):
        await client.generate_structured("judge", Verdict)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ConnectionError("Failed to connect to Ollama"), "not reachable"),
        (ollama.ResponseError("model 'qwen3:8b' not found", 404), "ollama pull qwen3:8b"),
        (ollama.ResponseError("boom", 500), "500"),
        (httpx.ReadTimeout("slow"), "timed out"),
    ],
)
async def test_errors_become_llm_errors(error: Exception, expected: str) -> None:
    client, _ = make_client([error])

    with pytest.raises(LLMError, match=expected):
        await client.generate("hi")
