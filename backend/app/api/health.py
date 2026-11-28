"""GET /health: is the backend up, which LLM provider it uses, and is fact-checking ready."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    state = request.app.state
    return {
        "status": "ok",
        "provider": state.settings.llm_provider,
        "fact_check": "ready" if state.fact_check_graph is not None else "unavailable",
    }
