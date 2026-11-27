"""The fact-check graph (ADR 0010):

    extract_claims --Send, one per claim--> check_claim (retrieve -> verify) --> collect

`check_claim` is its own small graph, so Phase 4 can add its "is the evidence enough?"
loop between retrieve and verify.
"""

import logging
from collections import Counter

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Send

from app.agents.claim_extractor import DEFAULT_MAX_CLAIMS, ClaimExtractor
from app.agents.verifier import Verifier
from app.llm.base import LLMClient, Usage
from app.models.fact_check import ClaimResult, FactCheckResponse
from app.retrieval.base import Retriever
from app.workflows.fact_check_state import (
    ClaimInput,
    ClaimOutput,
    ClaimState,
    ClaimUpdate,
    FactCheckInput,
    FactCheckState,
    FactCheckUpdate,
)

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 3
# Claims checked at the same time; local models serve one request at a time anyway
DEFAULT_MAX_CONCURRENCY = 4

type FactCheckGraph = CompiledStateGraph[FactCheckState, None, FactCheckInput, FactCheckState]


def build_fact_check_graph(
    llm: LLMClient,
    retriever: Retriever,
    *,
    top_k: int = DEFAULT_TOP_K,
    max_claims: int = DEFAULT_MAX_CLAIMS,
) -> FactCheckGraph:
    """Build and compile the graph once; it can then run any number of fact-checks."""
    extractor = ClaimExtractor(llm, max_claims=max_claims)
    verifier = Verifier(llm)

    # --- one claim: retrieve -> verify ---
    async def retrieve(state: ClaimState) -> ClaimUpdate:
        return {"passages": await retriever.search(state["claim"].text, k=top_k)}

    async def verify(state: ClaimState) -> ClaimUpdate:
        passages = state["passages"]
        checked = await verifier.verify(state["claim"], passages)
        result = ClaimResult(
            claim=state["claim"],
            verdict=checked.verdict,
            retrieved_doc_ids=[p.document.doc_id for p in passages],
        )
        return {"results": [result], "usage": [checked.usage] if checked.usage else []}

    check_claim = StateGraph(ClaimState, input_schema=ClaimInput, output_schema=ClaimOutput)
    check_claim.add_node("retrieve", retrieve)
    check_claim.add_node("verify", verify)
    check_claim.add_edge(START, "retrieve")
    check_claim.add_edge("retrieve", "verify")
    check_claim.add_edge("verify", END)

    # --- the whole draft ---
    async def extract_claims(state: FactCheckState) -> FactCheckUpdate:
        extracted = await extractor.extract(state["article"])
        return {"claims": extracted.content, "usage": [extracted.usage]}

    def send_each_claim(state: FactCheckState) -> list[Send] | str:
        """One branch per claim. With no claims, go straight to collect: zero branches
        would otherwise never reach it."""
        if not state["claims"]:
            return "collect"
        return [Send("check_claim", {"claim": claim}) for claim in state["claims"]]

    graph = StateGraph(FactCheckState, input_schema=FactCheckInput)
    graph.add_node("extract_claims", extract_claims)
    graph.add_node("check_claim", check_claim.compile())
    graph.add_node("collect", collect)
    graph.add_edge(START, "extract_claims")
    graph.add_conditional_edges("extract_claims", send_each_claim, ["check_claim", "collect"])
    graph.add_edge("check_claim", "collect")
    graph.add_edge("collect", END)
    return graph.compile()


def collect(state: FactCheckState) -> FactCheckUpdate:
    """Put the results back in claim order (branches finish in any order) and log a summary."""
    order = {claim.id: position for position, claim in enumerate(state["claims"])}
    results = sorted(state.get("results", []), key=lambda r: order[r.claim.id])
    usage = state.get("usage", [])
    labels = Counter(r.verdict.label for r in results)
    logger.info(
        "fact-check done claims=%d supported=%d contradicted=%d not_enough_info=%d "
        "calls=%d tokens=%d llm_time=%.0fms cost=$%.6f",
        len(results),
        labels["supported"],
        labels["contradicted"],
        labels["not_enough_info"],
        len(usage),
        sum(u.total_tokens for u in usage),
        sum(u.latency_ms for u in usage),
        sum(u.cost_usd or 0.0 for u in usage),
    )
    return {"response": FactCheckResponse(results=results)}


async def run_fact_check(
    graph: FactCheckGraph, article: str, *, max_concurrency: int = DEFAULT_MAX_CONCURRENCY
) -> tuple[FactCheckResponse, list[Usage]]:
    """Run one fact-check. Returns the response and the usage of every LLM call."""
    final = await graph.ainvoke({"article": article}, config={"max_concurrency": max_concurrency})
    return final["response"], final.get("usage", [])
