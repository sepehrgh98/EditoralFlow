"""Data shapes of a fact-check, as the API returns them (ADR 0007, ADR 0008).

The models' own answers are simpler (the extractor writes no ids, the verifier writes
sentence numbers, not citations); the code builds these shapes from them.
"""

from typing import Literal

from pydantic import BaseModel, Field, computed_field

# supported / contradicted / not_enough_info ("can't tell" in the frontend)
Label = Literal["supported", "contradicted", "not_enough_info"]


class Claim(BaseModel):
    """One atomic, self-contained fact taken from the draft."""

    id: str = Field(description="Claim id within this fact-check, e.g. c1.")
    text: str = Field(description="The claim as one self-contained statement.")
    source_sentence: str = Field(description="The draft sentence it came from, word for word.")


class Citation(BaseModel):
    """One source sentence. Its text is looked up in the corpus, never written by a model."""

    doc_id: str
    title: str
    sentence_index: int = Field(ge=0, description="Position of the sentence in the abstract.")
    text: str


class Verdict(BaseModel):
    label: Label
    explanation: str = Field(description="One sentence on why.")
    citations: list[Citation] = Field(default_factory=list)


class ClaimResult(BaseModel):
    claim: Claim
    verdict: Verdict
    retrieved_doc_ids: list[str] = Field(
        default_factory=list, description="Abstracts search returned, best first."
    )


class LabelCounts(BaseModel):
    supported: int = 0
    contradicted: int = 0
    not_enough_info: int = 0


class FactCheckResponse(BaseModel):
    """The response of POST /fact-check."""

    results: list[ClaimResult]

    @computed_field
    @property
    def counts(self) -> LabelCounts:
        """How many claims got each label. Calculated from results, so they always agree."""
        counts = LabelCounts()
        for result in self.results:
            label = result.verdict.label
            setattr(counts, label, getattr(counts, label) + 1)
        return counts
