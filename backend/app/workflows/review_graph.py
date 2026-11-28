"""The review graph: Prepare draft -> Grammar and Style (and optionally Fact-check) in
parallel -> Merge results."""

import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.grammar import GrammarAgent
from app.agents.style import StyleAgent
from app.core.tracing import graph_tracing
from app.llm.base import LLMClient, Usage
from app.models.review import ReviewResponse
from app.workflows.fact_check_graph import (
    DEFAULT_MAX_CONCURRENCY,
    FactCheckGraph,
    run_fact_check,
)
from app.workflows.state import ReviewInput, ReviewState, ReviewUpdate

logger = logging.getLogger(__name__)

type ReviewGraph = CompiledStateGraph[ReviewState, None, ReviewInput, ReviewState]


def prepare_draft(state: ReviewInput) -> ReviewUpdate:
    """Tidy the article before the agents see it."""
    article = state["article"].replace("\r\n", "\n").replace("\r", "\n").strip()
    return {"article": article}


def merge_results(state: ReviewState) -> ReviewUpdate:
    """Combine the agents' results into the response and log the review's total cost."""
    usage = state["usage"]
    cost = sum(u.cost_usd or 0.0 for u in usage)
    logger.info(
        "review done calls=%d tokens=%d llm_time=%.0fms cost=$%.6f",
        len(usage),
        sum(u.total_tokens for u in usage),
        sum(u.latency_ms for u in usage),
        cost,
    )
    response = ReviewResponse(
        grammar_result=state["grammar_result"],
        style_result=state["style_result"],
        fact_check_result=state.get("fact_check_result"),
    )
    return {"response": response}


def build_review_graph(
    llm: LLMClient,
    fact_check: FactCheckGraph | None = None,
    *,
    fact_check_max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
) -> ReviewGraph:
    """Build and compile the graph once; it can then run any number of reviews.

    With `fact_check`, the fact-check graph runs as a third parallel branch (ADR 0010).
    """
    grammar_agent = GrammarAgent(llm)
    style_agent = StyleAgent(llm)

    async def grammar(state: ReviewState) -> ReviewUpdate:
        result = await grammar_agent.review(state["article"])
        return {"grammar_result": result.content, "usage": [result.usage]}

    async def style(state: ReviewState) -> ReviewUpdate:
        result = await style_agent.review(state["article"])
        return {"style_result": result.content, "usage": [result.usage]}

    graph = StateGraph(ReviewState, input_schema=ReviewInput)
    graph.add_node("prepare_draft", prepare_draft)
    graph.add_node("grammar", grammar)
    graph.add_node("style", style)
    graph.add_node("merge_results", merge_results)
    branches = ["grammar", "style"]

    if fact_check is not None:
        fact_check_graph = fact_check

        async def fact_check_branch(state: ReviewState) -> ReviewUpdate:
            result, usage = await run_fact_check(
                fact_check_graph, state["article"], max_concurrency=fact_check_max_concurrency
            )
            return {"fact_check_result": result, "usage": usage}

        graph.add_node("fact_check", fact_check_branch)
        branches.append("fact_check")

    graph.add_edge(START, "prepare_draft")
    # Several edges out of one node: LangGraph runs the branches at the same time
    for branch in branches:
        graph.add_edge("prepare_draft", branch)
    # merge_results waits until every branch has finished
    graph.add_edge(branches, "merge_results")
    graph.add_edge("merge_results", END)

    return graph.compile()


async def run_review(graph: ReviewGraph, article: str) -> tuple[ReviewResponse, list[Usage]]:
    """Run one review. Returns the response and the usage of every LLM call."""
    with graph_tracing():
        final = await graph.ainvoke(
            {"article": article}, config={"run_name": "EditoralFlow Review"}
        )
    return final["response"], final["usage"]
