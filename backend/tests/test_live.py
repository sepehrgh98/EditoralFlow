"""Live tests: call the real model from your settings (Ollama by default).

Skipped by `make check` and CI. Run on purpose with `make test-live`.
With Ollama they are free; with LLM_PROVIDER=anthropic they cost a little.
"""

import pytest

from app.agents.grammar import GrammarAgent
from app.core.config import Settings
from app.llm.factory import build_llm_client
from app.workflows.review_graph import build_review_graph, run_review

pytestmark = pytest.mark.live

ARTICLE = "Their going to announce the results tomorow. The CEO have said profits was good."


@pytest.fixture
def settings() -> Settings:
    return Settings()  # reads backend/.env, like the app


async def test_model_returns_a_valid_structured_answer(settings: Settings) -> None:
    agent = GrammarAgent(build_llm_client(settings))

    response = await agent.review(ARTICLE)

    assert 0 <= response.content.score <= 100
    assert response.content.issues, "an article with obvious errors should have issues"
    assert response.usage.input_tokens > 0
    assert response.usage.output_tokens > 0


async def test_full_review_runs_end_to_end(settings: Settings) -> None:
    graph = build_review_graph(build_llm_client(settings))

    response, usage = await run_review(graph, ARTICLE)

    assert response.grammar_result.summary
    assert response.style_result.summary
    assert len(usage) == 2
