"""POST /review: review an article with the grammar and style agents."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_graph
from app.api.errors import llm_errors_as_http
from app.api.schemas import ArticleRequest
from app.models.review import ReviewResponse
from app.workflows.review_graph import ReviewGraph, run_review

router = APIRouter()


@router.post("/review")
async def review(
    body: ArticleRequest, graph: Annotated[ReviewGraph, Depends(get_graph)]
) -> ReviewResponse:
    with llm_errors_as_http("review"):
        response, _usage = await run_review(graph, body.article)
    return response
