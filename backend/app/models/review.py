"""Data shapes of a review. The JSON the frontend receives is built from these."""

from pydantic import BaseModel, Field

from app.models.fact_check import FactCheckResponse


class Issue(BaseModel):
    """One problem found in the article."""

    type: str = Field(description="Category of the problem, e.g. grammar, spelling, tone.")
    text: str = Field(description="The exact words from the article that have the problem.")
    issue: str = Field(description="Short explanation of what is wrong.")
    suggestion: str = Field(description="The corrected or improved text.")


class AgentResult(BaseModel):
    """What one review agent returns."""

    score: int = Field(ge=0, le=100, description="0 to 100; 100 means no problems found.")
    issues: list[Issue] = Field(description="Every problem found; empty if there are none.")
    summary: str = Field(description="One or two sentences on the overall result.")


class ReviewResponse(BaseModel):
    """The response of POST /review."""

    grammar_result: AgentResult
    style_result: AgentResult
    # Only when fact-checking is part of the review (ADR 0010); left out of the JSON
    # entirely otherwise, so the default response is unchanged
    fact_check_result: FactCheckResponse | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
