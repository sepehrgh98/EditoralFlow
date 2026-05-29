from pydantic import BaseModel


class Issue(BaseModel):
    type: str
    text: str
    issue: str
    suggestion: str


class AgentResult(BaseModel):
    score: int
    issues: list[Issue]
    summary: str