"""The fact-check graph with FakeLLM, real BM25 and the 5-abstract fixture corpus."""

import asyncio
import logging

import pytest

from app.llm.base import LLMError
from app.models.fact_check import LabelCounts
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.corpus import Corpus
from app.workflows.fact_check_graph import build_fact_check_graph, run_fact_check
from app.workflows.review_graph import build_review_graph, run_review
from tests.fakes import FakeAnswer, FakeCall, FakeLLM

DRAFT = "Statins cut heart deaths. Vitamin D prevents fractures. Gluons bind quarks."

# What the extractor "finds" in the draft
CLAIMS = {
    "claims": [
        {
            "text": "Statin therapy reduces cardiovascular mortality.",
            "source_sentence": "Statins cut heart deaths.",
        },
        {
            "text": "Vitamin D supplementation prevents hip fractures.",
            "source_sentence": "Vitamin D prevents fractures.",
        },
        # No word in common with the fixture corpus: search finds nothing
        {"text": "Gluons bind quarks.", "source_sentence": "Gluons bind quarks."},
    ]
}
# Verifier answers per claim. Sentence [2] of the top abstract is the key result in both.
VERDICTS = {
    "Statin": {"explanation": "Trial shows it.", "sentence_numbers": [2], "label": "supported"},
    "Vitamin": {"explanation": "No effect.", "sentence_numbers": [3], "label": "contradicted"},
}
GRAMMAR = {"score": 90, "issues": [], "summary": "ok"}


def is_extraction(call: FakeCall) -> bool:
    return "<draft>" in call.prompt


def is_verification(call: FakeCall) -> bool:
    return call.prompt.startswith("Claim:")


async def by_step(call: FakeCall) -> FakeAnswer:
    if is_extraction(call):
        return CLAIMS
    if is_verification(call):
        claim_line = call.prompt.splitlines()[1]
        return next(answer for key, answer in VERDICTS.items() if claim_line.startswith(key))
    return GRAMMAR  # grammar and style, in the review graph


@pytest.fixture
def retriever(corpus: Corpus) -> BM25Retriever:
    return BM25Retriever(corpus)


async def test_each_claim_gets_its_own_result_in_claim_order(retriever: BM25Retriever) -> None:
    graph = build_fact_check_graph(FakeLLM(responder=by_step), retriever)

    response, _ = await run_fact_check(graph, DRAFT)

    assert [r.claim.id for r in response.results] == ["c1", "c2", "c3"]
    assert [r.verdict.label for r in response.results] == [
        "supported",
        "contradicted",
        "not_enough_info",
    ]
    assert response.counts == LabelCounts(supported=1, contradicted=1, not_enough_info=1)


async def test_citations_and_retrieved_ids_come_from_search(retriever: BM25Retriever) -> None:
    graph = build_fact_check_graph(FakeLLM(responder=by_step), retriever)

    response, _ = await run_fact_check(graph, DRAFT)

    statins, vitamin_d, gluons = response.results
    assert statins.retrieved_doc_ids[0] == "101"
    assert [(c.doc_id, c.sentence_index) for c in statins.verdict.citations] == [("101", 1)]
    assert vitamin_d.retrieved_doc_ids[0] == "102"
    assert vitamin_d.verdict.citations[0].text.startswith("Vitamin D supplementation did not")
    assert gluons.retrieved_doc_ids == []
    assert gluons.verdict.citations == []


async def test_a_claim_with_no_search_results_is_not_sent_to_the_verifier(
    retriever: BM25Retriever,
) -> None:
    llm = FakeLLM(responder=by_step)

    _, usage = await run_fact_check(build_fact_check_graph(llm, retriever), DRAFT)

    verified = [c.prompt.splitlines()[1] for c in llm.calls if is_verification(c)]
    assert sorted(verified) == [
        "Statin therapy reduces cardiovascular mortality.",
        "Vitamin D supplementation prevents hip fractures.",
    ]
    assert len(usage) == 3  # 1 extraction + 2 verifications


async def test_tiers_fast_for_extraction_strong_for_verification(
    retriever: BM25Retriever,
) -> None:
    llm = FakeLLM(responder=by_step)

    await run_fact_check(build_fact_check_graph(llm, retriever), DRAFT)

    assert {c.tier for c in llm.calls if is_extraction(c)} == {"fast"}
    assert {c.tier for c in llm.calls if is_verification(c)} == {"strong"}


async def test_results_stay_in_claim_order_when_branches_finish_out_of_order(
    retriever: BM25Retriever,
) -> None:
    async def statins_slow(call: FakeCall) -> FakeAnswer:
        if is_verification(call) and "Statin" in call.prompt.splitlines()[1]:
            await asyncio.sleep(0.05)  # c1 finishes last
        return await by_step(call)

    graph = build_fact_check_graph(FakeLLM(responder=statins_slow), retriever)

    response, _ = await run_fact_check(graph, DRAFT)

    assert [r.claim.id for r in response.results] == ["c1", "c2", "c3"]


async def test_claims_are_checked_at_the_same_time(retriever: BM25Retriever) -> None:
    started = {"Statin": asyncio.Event(), "Vitamin": asyncio.Event()}

    async def wait_for_each_other(call: FakeCall) -> FakeAnswer:
        if is_verification(call):
            mine = next(k for k in started if call.prompt.splitlines()[1].startswith(k))
            started[mine].set()
            # If the claims were checked one after the other, this would time out
            await asyncio.wait_for(asyncio.gather(*(e.wait() for e in started.values())), 2)
        return await by_step(call)

    graph = build_fact_check_graph(FakeLLM(responder=wait_for_each_other), retriever)

    response, _ = await run_fact_check(graph, DRAFT)

    assert len(response.results) == 3


async def test_a_draft_without_claims_gives_an_empty_result(retriever: BM25Retriever) -> None:
    llm = FakeLLM([{"claims": []}])

    response, usage = await run_fact_check(build_fact_check_graph(llm, retriever), "Wow!")

    assert response.results == []
    assert response.counts == LabelCounts()
    assert len(usage) == 1


async def test_top_k_limits_the_abstracts_per_claim(retriever: BM25Retriever) -> None:
    llm = FakeLLM(responder=by_step)

    response, _ = await run_fact_check(build_fact_check_graph(llm, retriever, top_k=1), DRAFT)

    assert all(len(r.retrieved_doc_ids) <= 1 for r in response.results)


async def test_one_failed_claim_fails_the_whole_fact_check(retriever: BM25Retriever) -> None:
    async def vitamin_fails(call: FakeCall) -> FakeAnswer:
        if is_verification(call) and "Vitamin" in call.prompt:
            return LLMError("Ollama call to qwen3:14b timed out")
        return await by_step(call)

    graph = build_fact_check_graph(FakeLLM(responder=vitamin_fails), retriever)

    with pytest.raises(LLMError, match="timed out"):
        await run_fact_check(graph, DRAFT)


async def test_summary_is_logged(
    retriever: BM25Retriever, caplog: pytest.LogCaptureFixture
) -> None:
    graph = build_fact_check_graph(FakeLLM(responder=by_step), retriever)

    with caplog.at_level(logging.INFO, logger="app.workflows.fact_check_graph"):
        await run_fact_check(graph, DRAFT)

    assert "fact-check done claims=3 supported=1 contradicted=1 not_enough_info=1" in caplog.text


async def test_review_with_fact_check_includes_it_and_its_usage(retriever: BM25Retriever) -> None:
    llm = FakeLLM(responder=by_step)
    graph = build_review_graph(llm, fact_check=build_fact_check_graph(llm, retriever))

    response, usage = await run_review(graph, DRAFT)

    assert response.fact_check_result is not None
    assert response.fact_check_result.counts.supported == 1
    assert len(usage) == 2 + 3  # grammar, style + extraction, 2 verifications
    assert "fact_check_result" in response.model_dump()


async def test_review_without_fact_check_is_unchanged() -> None:
    graph = build_review_graph(FakeLLM(responder=by_step))

    response, usage = await run_review(graph, DRAFT)

    assert response.fact_check_result is None
    assert set(response.model_dump()) == {"grammar_result", "style_result"}
    assert '"fact_check_result"' not in response.model_dump_json()
    assert len(usage) == 2
