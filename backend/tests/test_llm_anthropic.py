"""AnthropicClient with the SDK replaced by a stand-in: no network, no cost."""

import logging
from typing import Any

import anthropic
import httpx2
import pytest
from anthropic.types import Message
from pydantic import BaseModel

from app.core.config import Settings
from app.llm.anthropic import AnthropicClient
from app.llm.base import LLMError, LLMOutputError

REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


class Verdict(BaseModel):
    score: int
    summary: str


def message(
    text: str, stop_reason: str = "end_turn", tokens: tuple[int, int] = (100, 20)
) -> Message:
    return Message.model_validate(
        {
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "model": "claude-haiku-5-5",
            "content": [{"type": "text", "text": text}],
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {"input_tokens": tokens[0], "output_tokens": tokens[1]},
        }
    )


class FakeMessages:
    def __init__(self, replies: list[Message | Exception]) -> None:
        self.replies = replies
        self.requests: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Message:
        self.requests.append(kwargs)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


class FakeSDK:
    def __init__(self, replies: list[Message | Exception]) -> None:
        self.messages = FakeMessages(replies)


def anthropic_settings(**overrides: Any) -> Settings:
    """Settings for the Anthropic provider, without reading backend/.env."""
    values = {"llm_provider": "anthropic", "anthropic_api_key": "k", **overrides}
    return Settings(_env_file=None, **values)  # type: ignore[call-arg]


def make_client(replies: list[Message | Exception]) -> tuple[AnthropicClient, FakeMessages]:
    settings = anthropic_settings()
    sdk = FakeSDK(replies)
    return AnthropicClient(settings, sdk=sdk), sdk.messages  # type: ignore[arg-type]


async def test_generate_returns_text_and_usage() -> None:
    client, sdk = make_client([message("Hello", tokens=(1_000_000, 1_000_000))])

    response = await client.generate("hi", system="be brief")

    assert response.content == "Hello"
    assert response.usage.model == "claude-haiku-5-5"
    assert response.usage.cost_usd == pytest.approx(0.10 + 0.50)  # Haiku 5.5 list price
    assert sdk.requests[0]["system"] == "be brief"
    assert "output_config" not in sdk.requests[0]


async def test_tier_picks_model_from_settings() -> None:
    client, sdk = make_client([message("x")])

    await client.generate("hi", tier="strong")

    assert sdk.requests[0]["model"] == "claude-sonnet-5-5"


async def test_structured_sends_schema_and_validates() -> None:
    client, sdk = make_client([message('{"score": 8, "summary": "ok"}')])

    response = await client.generate_structured("judge", Verdict)

    assert response.content == Verdict(score=8, summary="ok")
    sent_format = sdk.requests[0]["output_config"]["format"]
    assert sent_format["type"] == "json_schema"
    assert set(sent_format["schema"]["properties"]) == {"score", "summary"}


async def test_structured_retries_once_then_succeeds() -> None:
    client, sdk = make_client(
        [
            message('{"score": "bad"}', tokens=(10, 5)),
            message('{"score": 1, "summary": "s"}', tokens=(10, 5)),
        ]
    )

    response = await client.generate_structured("judge", Verdict)

    assert response.content.score == 1
    assert len(sdk.requests) == 2
    assert (response.usage.input_tokens, response.usage.output_tokens) == (20, 10)  # both attempts


async def test_structured_fails_after_two_bad_answers() -> None:
    client, sdk = make_client([message("not json"), message('{"score": 1}')])

    with pytest.raises(LLMOutputError, match="Verdict"):
        await client.generate_structured("judge", Verdict)
    assert len(sdk.requests) == 2


async def test_refusal_raises_without_retry() -> None:
    client, sdk = make_client([message("", stop_reason="refusal")])

    with pytest.raises(LLMError, match="declined"):
        await client.generate_structured("judge", Verdict)
    assert len(sdk.requests) == 1


async def test_cut_off_answer_raises_output_error() -> None:
    client, _ = make_client([message('{"score": 1, "sum', stop_reason="max_tokens")])

    with pytest.raises(LLMOutputError, match="cut off"):
        await client.generate_structured("judge", Verdict)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            anthropic.RateLimitError(
                "r", response=httpx2.Response(429, request=REQUEST), body=None
            ),
            "rate limit",
        ),
        (
            anthropic.AuthenticationError(
                "a", response=httpx2.Response(401, request=REQUEST), body=None
            ),
            "API key",
        ),
        (
            anthropic.InternalServerError(
                "s", response=httpx2.Response(500, request=REQUEST), body=None
            ),
            "500",
        ),
        (anthropic.APITimeoutError(request=REQUEST), "timed out"),
        (anthropic.APIConnectionError(request=REQUEST), "connect"),
    ],
)
async def test_sdk_errors_become_llm_errors(error: Exception, expected: str) -> None:
    client, _ = make_client([error])

    with pytest.raises(LLMError, match=expected):
        await client.generate("hi")


def test_real_sdk_gets_timeout_and_retries_from_settings() -> None:
    settings = anthropic_settings(llm_timeout_seconds=7, llm_max_retries=5)

    sdk = AnthropicClient(settings)._sdk

    assert sdk.timeout == 7
    assert sdk.max_retries == 5


async def test_each_call_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    client, _ = make_client([message("x")])

    with caplog.at_level(logging.INFO, logger="app.llm.anthropic"):
        await client.generate("hi")

    assert "model=claude-haiku-5-5 in=100 out=20" in caplog.text
    assert "cost=$" in caplog.text
