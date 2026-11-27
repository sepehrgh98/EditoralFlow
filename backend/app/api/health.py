"""GET /health: is the backend up, and which LLM provider does it use."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_settings_from_app
from app.core.config import Settings

router = APIRouter()


@router.get("/health")
async def health(settings: Annotated[Settings, Depends(get_settings_from_app)]) -> dict[str, str]:
    return {"status": "ok", "provider": settings.llm_provider}
