"""Shared objects the routes need, taken from the app's state (built at startup)."""

from fastapi import HTTPException, Request, status

from app.core.config import Settings
from app.workflows.fact_check_graph import FactCheckGraph
from app.workflows.review_graph import ReviewGraph


def get_settings_from_app(request: Request) -> Settings:
    return request.app.state.settings


def get_graph(request: Request) -> ReviewGraph:
    return request.app.state.graph


def get_fact_check_graph(request: Request) -> FactCheckGraph:
    """The fact-check graph, or 503 with the reason if it could not be built at startup."""
    graph: FactCheckGraph | None = request.app.state.fact_check_graph
    if graph is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail=request.app.state.fact_check_error
        )
    return graph
