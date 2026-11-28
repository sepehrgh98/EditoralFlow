"""ClaimExtractor with FakeLLM: what it sends and how it cleans the answer."""

import pytest

from app.agents.base import load_prompt
from app.agents.claim_extractor import ClaimExtractor, ExtractedClaims
from app.llm.base import LLMError, LLMOutputError
from app.models.fact_check import Claim
from tests.fakes import FakeLLM

DRAFT = "Statins cut deaths by a quarter. Vitamin D did not prevent fractures."


def answer(*claims: tuple[str, str]) -> dict[str, object]:
    return {"claims": [{"text": text, "source_sentence": source} for text, source in claims]}


def test_prompt_files_exist_with_the_article_slot() -> None:
    assert "atomic" in load_prompt("claim_extractor", "system").lower()
    assert "{article}" in load_prompt("claim_extractor", "user")


async def test_sends_the_draft_on_the_fast_tier() -> None:
    llm = FakeLLM([answer()])

    await ClaimExtractor(llm).extract(DRAFT)

    call = llm.calls[0]
    assert f"<draft>\n{DRAFT}\n</draft>" in call.prompt
    assert call.system == load_prompt("claim_extractor", "system")
    assert call.schema is ExtractedClaims
    assert call.tier == "fast"


async def test_claims_get_ids_in_order_and_keep_their_source_sentence() -> None:
    llm = FakeLLM(
        [
            answer(
                ("Statins reduced deaths by 25 percent.", "Statins cut deaths by a quarter."),
                ("Vitamin D did not prevent fractures.", "Vitamin D did not prevent fractures."),
            )
        ]
    )

    response = await ClaimExtractor(llm).extract(DRAFT)

    assert response.content == [
        Claim(
            id="c1",
            text="Statins reduced deaths by 25 percent.",
            source_sentence="Statins cut deaths by a quarter.",
        ),
        Claim(
            id="c2",
            text="Vitamin D did not prevent fractures.",
            source_sentence="Vitamin D did not prevent fractures.",
        ),
    ]
    assert response.usage.model == "fake-fast"


async def test_empty_and_repeated_claims_are_removed() -> None:
    llm = FakeLLM(
        [
            answer(
                ("Statins reduce deaths.", "s1"),
                ("   ", "s1"),
                ("statins  reduce DEATHS.", "s1"),  # same claim, different case and spaces
                ("Vitamin D does not prevent fractures.", "s2"),
            )
        ]
    )

    claims = (await ClaimExtractor(llm).extract(DRAFT)).content

    assert [(c.id, c.text) for c in claims] == [
        ("c1", "Statins reduce deaths."),
        ("c2", "Vitamin D does not prevent fractures."),
    ]


async def test_at_most_max_claims_are_kept() -> None:
    llm = FakeLLM([answer(*[(f"Fact number {i}.", "s") for i in range(30)])])

    claims = (await ClaimExtractor(llm, max_claims=20).extract(DRAFT)).content

    assert len(claims) == 20
    assert claims[-1].id == "c20"


async def test_source_sentence_not_in_the_draft_is_kept() -> None:
    llm = FakeLLM([answer(("Statins reduce deaths.", "A sentence the draft does not contain."))])

    claims = (await ClaimExtractor(llm).extract(DRAFT)).content

    assert claims[0].source_sentence == "A sentence the draft does not contain."


async def test_a_draft_without_claims_gives_an_empty_list() -> None:
    assert (await ClaimExtractor(FakeLLM([answer()])).extract("What a day!")).content == []


async def test_wrongly_shaped_answer_is_rejected() -> None:
    with pytest.raises(LLMOutputError):
        await ClaimExtractor(FakeLLM([{"claims": [{"text": "no source"}]}])).extract(DRAFT)


async def test_llm_errors_pass_through() -> None:
    with pytest.raises(LLMError, match="not reachable"):
        await ClaimExtractor(FakeLLM([LLMError("Ollama is not reachable")])).extract(DRAFT)
