"""The real app (routing, graph, agents) with only the model faked."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.llm.base import LLMError, LLMOutputError
from app.main import create_app
from tests.fakes import FakeAnswer, FakeCall, FakeLLM

GRAMMAR = {
    "score": 85,
    "issues": [
        {"type": "grammar", "text": "Their", "issue": "Wrong word.", "suggestion": "They're"}
    ],
    "summary": "One error.",
}
STYLE = {"score": 70, "issues": [], "summary": "Readable."}


async def by_agent(call: FakeCall) -> FakeAnswer:
    return GRAMMAR if "grammar, spelling and punctuation" in call.prompt else STYLE


def client_with(llm: FakeLLM) -> TestClient:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    return TestClient(create_app(settings=settings, llm=llm))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with client_with(FakeLLM(responder=by_agent)) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "provider": "ollama"}


def test_review_returns_the_shape_the_frontend_reads(client: TestClient) -> None:
    response = client.post("/review", json={"article": "Their going home."})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"grammar_result", "style_result"}
    assert body["grammar_result"] == GRAMMAR
    assert body["style_result"] == STYLE


@pytest.mark.parametrize("article", ["", "   \n  "])
def test_blank_article_is_rejected(client: TestClient, article: str) -> None:
    assert client.post("/review", json={"article": article}).status_code == 422


def test_missing_article_is_rejected(client: TestClient) -> None:
    assert client.post("/review", json={}).status_code == 422


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (LLMError("Ollama is not reachable at http://localhost:11434"), 503),
        (LLMOutputError("answer did not match AgentResult"), 502),
    ],
)
def test_llm_errors_become_clear_http_errors(error: Exception, status_code: int) -> None:
    async def fails(call: FakeCall) -> FakeAnswer:
        return error

    with client_with(FakeLLM(responder=fails)) as client:
        response = client.post("/review", json={"article": "Text."})

    assert response.status_code == status_code
    assert response.json() == {"detail": str(error)}


def test_cors_allows_the_frontend(client: TestClient) -> None:
    response = client.options(
        "/review",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_create_app_builds_the_configured_client() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    with TestClient(create_app(settings=settings)) as client:
        assert client.get("/health").json()["provider"] == "ollama"
