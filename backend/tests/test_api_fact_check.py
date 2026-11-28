"""POST /fact-check and the fact-check startup wiring, with FakeLLM and the fixture corpus."""

from pathlib import Path

import pytest

from app.llm.base import LLMError, LLMOutputError
from tests.fakes import FakeAnswer, FakeCall, FakeLLM
from tests.test_api import STYLE, by_agent, client_with

CLAIMS = {
    "claims": [
        {
            "text": "Statin therapy reduces cardiovascular mortality.",
            "source_sentence": "Statins cut heart deaths.",
        }
    ]
}
SUPPORTED = {"explanation": "Trial shows it.", "sentence_numbers": [2], "label": "supported"}


async def fact_check_steps(call: FakeCall) -> FakeAnswer:
    if "<draft>" in call.prompt:
        return CLAIMS
    if call.prompt.startswith("Claim:"):
        return SUPPORTED
    return await by_agent(call)  # grammar and style


def test_fact_check_returns_claims_verdicts_and_citations() -> None:
    with client_with(FakeLLM(responder=fact_check_steps)) as client:
        response = client.post("/fact-check", json={"article": "Statins cut heart deaths."})

    assert response.status_code == 200
    body = response.json()
    assert body["counts"] == {"supported": 1, "contradicted": 0, "not_enough_info": 0}
    result = body["results"][0]
    assert result["claim"]["id"] == "c1"
    assert result["claim"]["source_sentence"] == "Statins cut heart deaths."
    assert result["verdict"]["label"] == "supported"
    assert result["verdict"]["citations"][0]["doc_id"] == "101"
    assert result["verdict"]["citations"][0]["text"].startswith("In this randomised trial")
    assert result["retrieved_doc_ids"][0] == "101"


def test_settings_reach_the_graph() -> None:
    llm = FakeLLM(responder=fact_check_steps)

    with client_with(llm, fact_check_top_k=1) as client:
        body = client.post("/fact-check", json={"article": "Statins."}).json()

    assert len(body["results"][0]["retrieved_doc_ids"]) == 1


@pytest.mark.parametrize("article", ["", "  \n "])
def test_blank_article_is_rejected(article: str) -> None:
    with client_with(FakeLLM()) as client:
        assert client.post("/fact-check", json={"article": article}).status_code == 422


@pytest.mark.parametrize(
    ("error", "status_code"),
    [(LLMError("Ollama is not reachable"), 503), (LLMOutputError("bad answer"), 502)],
)
def test_llm_errors_become_clear_http_errors(error: Exception, status_code: int) -> None:
    async def fails(call: FakeCall) -> FakeAnswer:
        return error

    with client_with(FakeLLM(responder=fails)) as client:
        response = client.post("/fact-check", json={"article": "Statins."})

    assert response.status_code == status_code
    assert response.json() == {"detail": str(error)}


def test_review_does_not_fact_check_by_default() -> None:
    llm = FakeLLM(responder=fact_check_steps)

    with client_with(llm) as client:
        body = client.post("/review", json={"article": "Statins cut heart deaths."}).json()

    assert set(body) == {"grammar_result", "style_result"}
    assert not any("<draft>" in call.prompt for call in llm.calls)


def test_review_includes_fact_check_when_enabled() -> None:
    with client_with(FakeLLM(responder=fact_check_steps), review_include_fact_check=True) as client:
        body = client.post("/review", json={"article": "Statins cut heart deaths."}).json()

    assert set(body) == {"grammar_result", "style_result", "fact_check_result"}
    assert body["style_result"] == STYLE
    assert body["fact_check_result"]["counts"]["supported"] == 1


def test_without_corpus_review_works_and_fact_check_says_why(tmp_path: Path) -> None:
    missing = tmp_path / "corpus.jsonl"

    with client_with(FakeLLM(responder=fact_check_steps), corpus_path=missing) as client:
        health = client.get("/health").json()
        review = client.post("/review", json={"article": "Text."})
        fact_check = client.post("/fact-check", json={"article": "Text."})

    assert health["fact_check"] == "unavailable"
    assert review.status_code == 200
    assert fact_check.status_code == 503
    assert "run `make data`" in fact_check.json()["detail"]


def test_without_corpus_the_app_refuses_to_start_if_review_needs_it(tmp_path: Path) -> None:
    client = client_with(
        FakeLLM(), corpus_path=tmp_path / "corpus.jsonl", review_include_fact_check=True
    )

    with pytest.raises(RuntimeError, match="REVIEW_INCLUDE_FACT_CHECK is true, but"), client:
        pass
