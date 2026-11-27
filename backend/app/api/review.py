"""POST /review: review an article with the grammar and style agents."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.api.deps import get_graph
from app.llm.base import LLMError, LLMOutputError
from app.models.review import ReviewResponse
from app.workflows.review_graph import ReviewGraph, run_review

logger = logging.getLogger(__name__)

router = APIRouter()


class ReviewRequest(BaseModel):
    article: str = Field(min_length=1, description="The article text to review.")

    @field_validator("article")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("article must not be blank")
        return value


@router.post("/review")
async def review(
    body: ReviewRequest, graph: Annotated[ReviewGraph, Depends(get_graph)]
) -> ReviewResponse:
    try:
        response, _usage = await run_review(graph, body.article)
    except LLMOutputError as exc:
        # The model answered, but not in the required shape (after a retry)
        logger.error("review failed, bad model output: %s", exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except LLMError as exc:
        # The model could not be reached or the call failed (Ollama down, timeout, ...)
        logger.error("review failed, LLM unavailable: %s", exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return response
