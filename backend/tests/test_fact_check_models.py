import pytest
from pydantic import ValidationError

from app.models.fact_check import (
    Citation,
    Claim,
    ClaimResult,
    FactCheckResponse,
    LabelCounts,
    Verdict,
)

CLAIM = Claim(id="c1", text="Statins reduce deaths.", source_sentence="Statins cut deaths.")
CITATION = Citation(doc_id="101", title="Statins", sentence_index=1, text="Deaths fell 25%.")


def result(label: str) -> ClaimResult:
    return ClaimResult(
        claim=CLAIM, verdict=Verdict.model_validate({"label": label, "explanation": "Why."})
    )


@pytest.mark.parametrize("label", ["supported", "contradicted", "not_enough_info"])
def test_the_three_labels_are_accepted(label: str) -> None:
    assert result(label).verdict.label == label


@pytest.mark.parametrize("label", ["partly_supported", "true", "can't tell", ""])
def test_any_other_label_is_rejected(label: str) -> None:
    with pytest.raises(ValidationError):
        Verdict.model_validate({"label": label, "explanation": "Why."})


def test_verdict_defaults_to_no_citations() -> None:
    assert Verdict(label="not_enough_info", explanation="No source.").citations == []


def test_sentence_index_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        Citation(doc_id="1", title="T", sentence_index=-1, text="x")


def test_counts_are_calculated_from_results() -> None:
    response = FactCheckResponse(
        results=[result("supported"), result("supported"), result("not_enough_info")]
    )

    assert response.counts == LabelCounts(supported=2, contradicted=0, not_enough_info=1)


def test_empty_response_counts_zero() -> None:
    assert FactCheckResponse(results=[]).counts == LabelCounts()


def test_json_shape() -> None:
    verdict = Verdict(label="supported", explanation="Why.", citations=[CITATION])
    response = FactCheckResponse(
        results=[ClaimResult(claim=CLAIM, verdict=verdict, retrieved_doc_ids=["101", "103"])]
    )

    data = response.model_dump()

    assert set(data) == {"results", "counts"}
    assert data["counts"] == {"supported": 1, "contradicted": 0, "not_enough_info": 0}
    first = data["results"][0]
    assert set(first) == {"claim", "verdict", "retrieved_doc_ids"}
    assert set(first["claim"]) == {"id", "text", "source_sentence"}
    assert set(first["verdict"]["citations"][0]) == {"doc_id", "title", "sentence_index", "text"}
