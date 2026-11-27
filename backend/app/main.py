"""App factory. Start with: uvicorn --factory app.main:create_app

Nothing is built when this module is imported. `create_app()` reads the settings, and
at startup the LLM client and the review graph are built once and shared by all requests.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, review
from app.core.config import Settings, get_settings
from app.core.logging import setup_logging
from app.llm.base import LLMClient
from app.llm.factory import build_llm_client
from app.workflows.review_graph import build_review_graph

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, llm: LLMClient | None = None) -> FastAPI:
    """Build the FastAPI app. Tests pass their own settings and a FakeLLM."""
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = llm or build_llm_client(settings)
        app.state.settings = settings
        app.state.graph = build_review_graph(client)
        logger.info("EditoralFlow ready, LLM provider=%s", settings.llm_provider)
        yield

    app = FastAPI(title="EditoralFlow", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(review.router)
    app.include_router(health.router)
    return app
