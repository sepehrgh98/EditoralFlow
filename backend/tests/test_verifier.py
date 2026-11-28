"""Verifier with FakeLLM on the fixture abstracts: numbering, citations and the guard."""

import pytest

from app.agents.base import load_prompt
from app.agents.verifier import NO_SOURCE_EXPLANATION, Verifier, VerifierAnswer, number_sources
from app.llm.base import LLMError
from app.models.fact_check import Citation, Claim
from app.retrieval.base import Passage
from app.retrieval.corpus import Corpus
from tests.fakes import FakeLLM

CLAIM = Claim(id="c1", text="Statins reduce cardiovascular deaths.", source_sentence="s")


@pytest.fixture
def passages(corpus: Corpus) -> list[Passage]:
    """Abstract 101 (statins, 4 sentences) then 102 (vitamin D, 4 sentences)."""
    return [
        Passage(document=doc, score=1.0)
        for doc in (corpus.get("101"), corpus.get("102"))
        if doc is not None
    ]


def answer(label: str, numbers: list[int], explanation: str = "Because.") -> dict[str, object]:
    return {"explanation": explanation, "sentence_numbers": numbers, "label": label}


def test_prompt_files_exist_with_both_slots() -> None:
    assert "only from the numbered source sentences" in load_prompt("verifier", "system")
    user = load_prompt("verifier", "user")
    assert "{claim}" in user and "{passages}" in user


def test_sources_are_numbered_across_abstracts(passages: list[Passage]) -> None:
    sources = number_sources(passages)

    assert sources.text.startswith('Source A: "Statin therapy')
    assert '\n\nSource B: "Vitamin D' in sources.text
    assert "[1] Statins are widely prescribed" in sources.text
    assert "[5] Vitamin D is often recommended" in sources.text  # numbering continues in B
    assert len(sources.sentences) == 8
    document, index = sources.sentences[6]
    assert (document.doc_id, index) == ("102", 1)


def test_answer_fields_are_in_reasoning_order() -> None:
    assert list(VerifierAnswer.model_fields) == ["explanation", "sentence_numbers", "label"]


async def test_sends_claim_and_numbered_sources_on_the_strong_tier(
    passages: list[Passage],
) -> None:
    llm = FakeLLM([answer("supported", [2])])

    await Verifier(llm).verify(CLAIM, passages)

    call = llm.calls[0]
    assert call.prompt.startswith("Claim:\nStatins reduce cardiovascular deaths.\n\nSources:\n")
    assert "[2] In this randomised trial" in call.prompt
    assert call.schema is VerifierAnswer
    assert call.tier == "strong"


async def test_numbers_become_exact_citations_from_the_corpus(passages: list[Passage]) -> None:
    result = await Verifier(FakeLLM([answer("supported", [2])])).verify(CLAIM, passages)

    assert result.verdict.label == "supported"
    assert result.verdict.citations == [
        Citation(
            doc_id="101",
            title="Statin therapy and cardiovascular mortality in adults with heart disease",
            sentence_index=1,
            text=(
                "In this randomised trial of 4,000 adults, statin therapy reduced "
                "cardiovascular mortality by 25 percent over five years."
            ),
        )
    ]
    assert result.usage is not None


async def test_citations_can_span_abstracts_and_repeats_are_removed(
    passages: list[Passage],
) -> None:
    result = await Verifier(FakeLLM([answer("contradicted", [7, 2, 7])])).verify(CLAIM, passages)

    assert [(c.doc_id, c.sentence_index) for c in result.verdict.citations] == [
        ("102", 2),
        ("101", 1),
    ]


async def test_numbers_that_do_not_exist_are_dropped(passages: list[Passage]) -> None:
    result = await Verifier(FakeLLM([answer("supported", [0, 2, 99, -1])])).verify(CLAIM, passages)

    assert [c.sentence_index for c in result.verdict.citations] == [1]


@pytest.mark.parametrize("label", ["supported", "contradicted"])
@pytest.mark.parametrize("numbers", [[], [42]])
async def test_a_verdict_without_valid_proof_becomes_cant_tell(
    passages: list[Passage], label: str, numbers: list[int]
) -> None:
    llm = FakeLLM([answer(label, numbers, "The trial shows it.")])

    verdict = (await Verifier(llm).verify(CLAIM, passages)).verdict

    assert verdict.label == "not_enough_info"
    assert verdict.citations == []
    assert f"Downgraded from {label}" in verdict.explanation
    assert "The trial shows it." in verdict.explanation


async def test_cant_tell_never_carries_citations(passages: list[Passage]) -> None:
    verdict = (
        await Verifier(FakeLLM([answer("not_enough_info", [2])])).verify(CLAIM, passages)
    ).verdict

    assert verdict.label == "not_enough_info"
    assert verdict.citations == []


async def test_no_passages_means_cant_tell_without_a_model_call() -> None:
    llm = FakeLLM()

    result = await Verifier(llm).verify(CLAIM, [])

    assert result.verdict.label == "not_enough_info"
    assert result.verdict.explanation == NO_SOURCE_EXPLANATION
    assert result.usage is None
    assert llm.calls == []


async def test_llm_errors_pass_through(passages: list[Passage]) -> None:
    with pytest.raises(LLMError, match="timed out"):
        await Verifier(FakeLLM([LLMError("Ollama call timed out")])).verify(CLAIM, passages)
