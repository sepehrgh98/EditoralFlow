"""Data shapes of a review. The JSON the frontend receives is built from these."""

from pydantic import BaseModel, Field


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
