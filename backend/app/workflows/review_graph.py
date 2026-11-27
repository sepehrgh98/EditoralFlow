"""The review graph: Prepare draft -> Grammar and Style in parallel -> Merge results."""

import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.grammar import GrammarAgent
from app.agents.style import StyleAgent
from app.llm.base import LLMClient, Usage
from app.models.review import ReviewResponse
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
        grammar_result=state["grammar_result"], style_result=state["style_result"]
    )
    return {"response": response}


def build_review_graph(llm: LLMClient) -> ReviewGraph:
    """Build and compile the graph once; it can then run any number of reviews."""
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

    graph.add_edge(START, "prepare_draft")
    # Two edges out of one node: LangGraph runs grammar and style at the same time
    graph.add_edge("prepare_draft", "grammar")
    graph.add_edge("prepare_draft", "style")
    # merge_results waits until both have finished
    graph.add_edge(["grammar", "style"], "merge_results")
    graph.add_edge("merge_results", END)

    return graph.compile()


async def run_review(graph: ReviewGraph, article: str) -> tuple[ReviewResponse, list[Usage]]:
    """Run one review. Returns the response and the usage of every LLM call."""
    final = await graph.ainvoke({"article": article})
    return final["response"], final["usage"]
