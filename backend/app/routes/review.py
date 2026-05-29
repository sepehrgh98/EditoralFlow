from fastapi import APIRouter
from pydantic import BaseModel

from app.workflows.review_workflow import ReviewWorkflow

router = APIRouter()

workflow = ReviewWorkflow()


class ReviewRequest(BaseModel):
    article: str


@router.post("/review")
async def review(request: ReviewRequest):

    return workflow.run(request.article)