"""Verifier: judges one claim against retrieved abstracts, citing sentence numbers.

The model sees every sentence of the given abstracts numbered 1..N and answers with
numbers only. The code turns numbers into citations from the corpus, so a quote can
never be invented, and applies the proof-or-abstain guard (ADR 0008).
"""

import string
from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.llm.base import Usage
from app.models.fact_check import Citation, Claim, Label, Verdict
from app.retrieval.base import Passage
from app.retrieval.corpus import Document

NO_SOURCE_EXPLANATION = "No relevant source was found in the library."


class VerifierAnswer(BaseModel):
    """The model's answer. Field order is the order the model writes them: reason first,
    then the evidence, then the label."""

    explanation: str = Field(description="One sentence on what the sources say about the claim.")
    sentence_numbers: list[int] = Field(
        description="Numbers of the source sentences the verdict relies on; empty if none."
    )
    label: Label = Field(
        description="supported, contradicted, or not_enough_info if the sources do not settle it."
    )


@dataclass(frozen=True)
class NumberedSources:
    """The sources as the model sees them, and what each number points to."""

    text: str
    sentences: dict[int, tuple[Document, int]]  # number -> (document, sentence index)


@dataclass(frozen=True)
class VerifyResult:
    verdict: Verdict
    usage: Usage | None  # None when no model call was needed


def number_sources(passages: list[Passage]) -> NumberedSources:
    """Label abstracts A, B, C... and number all their sentences 1..N in one sequence."""
    if len(passages) > len(string.ascii_uppercase):
        raise ValueError("At most 26 passages can be numbered")
    blocks: list[str] = []
    sentences: dict[int, tuple[Document, int]] = {}
    for letter, passage in zip(string.ascii_uppercase, passages, strict=False):
        document = passage.document
        lines = [f'Source {letter}: "{document.title}"']
        for index, sentence in enumerate(document.sentences):
            number = len(sentences) + 1
            sentences[number] = (document, index)
            lines.append(f"[{number}] {sentence}")
        blocks.append("\n".join(lines))
    return NumberedSources(text="\n\n".join(blocks), sentences=sentences)


class Verifier(BaseAgent[VerifierAnswer]):
    """Strong tier: judging evidence is the hard part."""

    name = "verifier"
    output_schema = VerifierAnswer
    slots = ("claim", "passages")
    tier = "strong"

    async def verify(self, claim: Claim, passages: list[Passage]) -> VerifyResult:
        if not passages:
            # Nothing to judge against: abstain without asking the model
            verdict = Verdict(label="not_enough_info", explanation=NO_SOURCE_EXPLANATION)
            return VerifyResult(verdict=verdict, usage=None)

        sources = number_sources(passages)
        response = await self.run(claim=claim.text, passages=sources.text)
        return VerifyResult(verdict=self._guard(response.content, sources), usage=response.usage)

    @staticmethod
    def _guard(answer: VerifierAnswer, sources: NumberedSources) -> Verdict:
        """Proof or abstain: a verdict must rest on real sentences, or it becomes can't tell."""
        valid = list(dict.fromkeys(n for n in answer.sentence_numbers if n in sources.sentences))

        if answer.label == "not_enough_info":
            return Verdict(label="not_enough_info", explanation=answer.explanation)

        if not valid:
            return Verdict(
                label="not_enough_info",
                explanation=(
                    f"Downgraded from {answer.label}: no valid source sentence was cited. "
                    f"Model's reason: {answer.explanation}"
                ),
            )

        citations = [
            Citation(
                doc_id=document.doc_id,
                title=document.title,
                sentence_index=index,
                text=document.sentences[index],
            )
            for document, index in (sources.sentences[n] for n in valid)
        ]
        return Verdict(label=answer.label, explanation=answer.explanation, citations=citations)
