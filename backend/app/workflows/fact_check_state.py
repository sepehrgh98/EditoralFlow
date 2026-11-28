"""State of the fact-check graph and of each per-claim branch."""

import operator
from typing import Annotated, TypedDict

from app.llm.base import Usage
from app.models.fact_check import Claim, ClaimResult, FactCheckResponse
from app.retrieval.base import Passage


class FactCheckInput(TypedDict):
    """What a fact-check starts with."""

    article: str


class FactCheckState(FactCheckInput):
    claims: list[Claim]
    # Reducers: every claim branch adds its result and usage; none overwrites another
    results: Annotated[list[ClaimResult], operator.add]
    usage: Annotated[list[Usage], operator.add]
    response: FactCheckResponse


class FactCheckUpdate(TypedDict, total=False):
    """What a node of the fact-check graph returns."""

    claims: list[Claim]
    results: list[ClaimResult]
    usage: list[Usage]
    response: FactCheckResponse


class ClaimInput(TypedDict):
    """What one claim branch starts with (sent by `Send`)."""

    claim: Claim


class ClaimOutput(TypedDict):
    """What one claim branch hands back to the fact-check graph."""

    results: Annotated[list[ClaimResult], operator.add]
    usage: Annotated[list[Usage], operator.add]


class ClaimState(ClaimInput, ClaimOutput):
    passages: list[Passage]


class ClaimUpdate(TypedDict, total=False):
    """What a node of a claim branch returns."""

    passages: list[Passage]
    results: list[ClaimResult]
    usage: list[Usage]
