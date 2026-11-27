"""Agents with FakeLLM: checks what they send and what they return. No real model."""

import pytest

from app.agents.base import BaseAgent, load_prompt
from app.agents.grammar import GrammarAgent
from app.agents.style import StyleAgent
from app.llm.base import LLMError, LLMOutputError
from app.models.review import AgentResult, ReviewResponse
from tests.fakes import FakeLLM

ARTICLE = "Their going home after the meeting."
ANSWER = {
    "score": 90,
    "issues": [
        {
            "type": "grammar",
            "text": "Their going",
            "issue": "Wrong word: 'their' is possessive.",
            "suggestion": "They're going",
        }
    ],
    "summary": "One grammar error.",
}


@pytest.mark.parametrize("agent", ["grammar", "style"])
def test_prompt_files_exist(agent: str) -> None:
    assert load_prompt(agent, "system")
    assert "{article}" in load_prompt(agent, "user")


def test_missing_prompt_fails_when_agent_is_created() -> None:
    class Missing(BaseAgent):
        name = "does-not-exist"

    with pytest.raises(FileNotFoundError, match="does-not-exist"):
        Missing(FakeLLM())


@pytest.mark.parametrize("agent_class", [GrammarAgent, StyleAgent])
async def test_agent_sends_system_prompt_and_article(agent_class: type[BaseAgent]) -> None:
    llm = FakeLLM([ANSWER])
    agent = agent_class(llm)

    await agent.review(ARTICLE)

    call = llm.calls[0]
    assert call.system == load_prompt(agent.name, "system")
    assert f"<article>\n{ARTICLE}\n</article>" in call.prompt
    assert "{article}" not in call.prompt
    assert call.schema is AgentResult
    assert call.tier == "fast"


async def test_agents_use_their_own_prompts() -> None:
    llm = FakeLLM([ANSWER, ANSWER])

    await GrammarAgent(llm).review(ARTICLE)
    await StyleAgent(llm).review(ARTICLE)

    grammar_call, style_call = llm.calls
    assert "grammar" in grammar_call.prompt
    assert "style" in style_call.prompt
    assert grammar_call.system != style_call.system


async def test_agent_returns_result_and_usage() -> None:
    response = await GrammarAgent(FakeLLM([ANSWER])).review(ARTICLE)

    assert response.content == AgentResult.model_validate(ANSWER)
    assert response.content.issues[0].suggestion == "They're going"
    assert response.usage.model == "fake-fast"


async def test_article_with_braces_is_kept_as_is() -> None:
    llm = FakeLLM([ANSWER])

    await GrammarAgent(llm).review("Code like {x} and {article} stays.")

    assert "Code like {x} and {article} stays." in llm.calls[0].prompt


async def test_score_out_of_range_is_rejected() -> None:
    agent = GrammarAgent(FakeLLM([{**ANSWER, "score": 150}]))

    with pytest.raises(LLMOutputError):
        await agent.review(ARTICLE)


async def test_llm_errors_pass_through() -> None:
    agent = StyleAgent(FakeLLM([LLMError("Ollama is not reachable")]))

    with pytest.raises(LLMError, match="not reachable"):
        await agent.review(ARTICLE)


def test_review_response_keeps_the_frontend_shape() -> None:
    result = AgentResult.model_validate(ANSWER)

    data = ReviewResponse(grammar_result=result, style_result=result).model_dump()

    assert set(data) == {"grammar_result", "style_result"}
    assert set(data["grammar_result"]) == {"score", "issues", "summary"}
    assert set(data["grammar_result"]["issues"][0]) == {"type", "text", "issue", "suggestion"}
