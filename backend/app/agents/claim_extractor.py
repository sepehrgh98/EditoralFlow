"""ClaimExtractor: turns a draft into atomic, self-contained factual claims (ADR 0007)."""

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.llm.base import LLMClient, LLMResponse
from app.models.fact_check import Claim

DEFAULT_MAX_CLAIMS = 20


class ExtractedClaim(BaseModel):
    """One claim as the model writes it (the code adds the id)."""

    text: str = Field(description="One checkable fact, understandable on its own.")
    source_sentence: str = Field(
        description="The sentence of the draft it comes from, copied word for word."
    )


class ExtractedClaims(BaseModel):
    """The model's whole answer."""

    claims: list[ExtractedClaim] = Field(
        description="Every factual claim in the draft; empty if there are none."
    )


class ClaimExtractor(BaseAgent[ExtractedClaims]):
    """Fast tier: finding claims is simpler than judging them."""

    name = "claim_extractor"
    output_schema = ExtractedClaims
    slots = ("article",)
    tier = "fast"

    def __init__(self, llm: LLMClient, max_claims: int = DEFAULT_MAX_CLAIMS) -> None:
        super().__init__(llm)
        self.max_claims = max_claims

    async def extract(self, article: str) -> LLMResponse[list[Claim]]:
        """Return the draft's claims with ids c1, c2, ... and the usage of the call."""
        response = await self.run(article=article)
        return LLMResponse(content=self._clean(response.content), usage=response.usage)

    def _clean(self, answer: ExtractedClaims) -> list[Claim]:
        """Drop empty and repeated claims, keep at most max_claims, number them."""
        claims: list[Claim] = []
        seen: set[str] = set()
        for extracted in answer.claims:
            text = extracted.text.strip()
            key = " ".join(text.lower().split())
            if not text or key in seen:
                continue
            seen.add(key)
            claims.append(
                Claim(
                    id=f"c{len(claims) + 1}",
                    text=text,
                    # Kept even if not found word for word; the frontend lists those apart
                    source_sentence=extracted.source_sentence.strip(),
                )
            )
            if len(claims) == self.max_claims:
                break
        return claims
