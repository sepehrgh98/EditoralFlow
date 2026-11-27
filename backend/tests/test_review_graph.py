"""The review graph run end to end with FakeLLM: no real model."""

import asyncio
import logging

import pytest

from app.llm.base import LLMError
from app.models.review import AgentResult
from app.workflows.review_graph import build_review_graph, prepare_draft, run_review
from tests.fakes import FakeAnswer, FakeCall, FakeLLM

GRAMMAR = {"score": 80, "issues": [], "summary": "grammar ok"}
STYLE = {"score": 60, "issues": [], "summary": "style needs work"}


def is_grammar(call: FakeCall) -> bool:
    return "grammar, spelling and punctuation" in call.prompt


async def by_agent(call: FakeCall) -> FakeAnswer:
    return GRAMMAR if is_grammar(call) else STYLE


async def test_review_puts_each_result_in_its_place() -> None:
    graph = build_review_graph(FakeLLM(responder=by_agent))

    response, usage = await run_review(graph, "Some article.")

    assert response.grammar_result == AgentResult.model_validate(GRAMMAR)
    assert response.style_result == AgentResult.model_validate(STYLE)
    assert len(usage) == 2  # one record per agent, none overwritten


async def test_grammar_and_style_run_at_the_same_time() -> None:
    grammar_started, style_started = asyncio.Event(), asyncio.Event()

    async def wait_for_each_other(call: FakeCall) -> FakeAnswer:
        mine, other = (
            (grammar_started, style_started)
            if is_grammar(call)
            else (style_started, grammar_started)
        )
        mine.set()
        # If the agents ran one after the other, this would time out
        await asyncio.wait_for(other.wait(), timeout=2)
        return await by_agent(call)

    graph = build_review_graph(FakeLLM(responder=wait_for_each_other))

    response, _ = await run_review(graph, "Some article.")

    assert response.grammar_result.summary == "grammar ok"


async def test_agents_see_the_tidied_article() -> None:
    llm = FakeLLM(responder=by_agent)

    await run_review(build_review_graph(llm), "  Line one.\r\nLine two.  \n")

    assert all("<article>\nLine one.\nLine two.\n</article>" in call.prompt for call in llm.calls)


def test_prepare_draft_tidies_text() -> None:
    assert prepare_draft({"article": "\r\n a\rb \n"}) == {"article": "a\nb"}


async def test_an_agent_error_stops_the_review() -> None:
    async def style_fails(call: FakeCall) -> FakeAnswer:
        return GRAMMAR if is_grammar(call) else LLMError("Ollama call timed out")

    graph = build_review_graph(FakeLLM(responder=style_fails))

    with pytest.raises(LLMError, match="timed out"):
        await run_review(graph, "Some article.")


async def test_graph_is_reusable() -> None:
    graph = build_review_graph(FakeLLM(responder=by_agent))

    first, _ = await run_review(graph, "One.")
    second, usage = await run_review(graph, "Two.")

    assert first == second
    assert len(usage) == 2  # usage does not pile up across reviews


async def test_review_logs_total(caplog: pytest.LogCaptureFixture) -> None:
    graph = build_review_graph(FakeLLM(responder=by_agent))

    with caplog.at_level(logging.INFO, logger="app.workflows.review_graph"):
        await run_review(graph, "Some article.")

    assert "review done calls=2" in caplog.text
