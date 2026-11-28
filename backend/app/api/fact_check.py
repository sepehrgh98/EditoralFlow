"""POST /fact-check: check every factual claim of an article against the corpus."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_fact_check_graph, get_settings_from_app
from app.api.errors import llm_errors_as_http
from app.api.schemas import ArticleRequest
from app.core.config import Settings
from app.models.fact_check import FactCheckResponse
from app.workflows.fact_check_graph import FactCheckGraph, run_fact_check

router = APIRouter()


@router.post("/fact-check")
async def fact_check(
    body: ArticleRequest,
    graph: Annotated[FactCheckGraph, Depends(get_fact_check_graph)],
    settings: Annotated[Settings, Depends(get_settings_from_app)],
) -> FactCheckResponse:
    with llm_errors_as_http("fact-check"):
        response, _usage = await run_fact_check(
            graph, body.article, max_concurrency=settings.fact_check_max_concurrency
        )
    return response
