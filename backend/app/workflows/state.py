"""The state of the review graph: the shared notebook every node reads and writes."""

import operator
from typing import Annotated, TypedDict

from app.llm.base import Usage
from app.models.review import AgentResult, ReviewResponse


class ReviewInput(TypedDict):
    """What a review starts with."""

    article: str


class ReviewState(ReviewInput):
    """The full state. Each key is filled in by the node that produces it."""

    grammar_result: AgentResult
    style_result: AgentResult
    # Reducer: when nodes write `usage` (even at the same time), the lists are added
    # together instead of one replacing the other.
    usage: Annotated[list[Usage], operator.add]
    response: ReviewResponse


class ReviewUpdate(TypedDict, total=False):
    """What a node returns: only the keys it changes. LangGraph merges it into the state."""

    article: str
    grammar_result: AgentResult
    style_result: AgentResult
    usage: list[Usage]
    response: ReviewResponse
