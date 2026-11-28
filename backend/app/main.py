"""App factory. Start with: uvicorn --factory app.main:create_app

Nothing is built when this module is imported. `create_app()` reads the settings, and at
startup the LLM client, the corpus search index and the graphs are built once and shared
by all requests.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import fact_check, health, review
from app.core.config import Settings, get_settings
from app.core.logging import setup_logging
from app.llm.base import LLMClient
from app.llm.factory import build_llm_client
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.corpus import CorpusError, load_corpus
from app.workflows.fact_check_graph import FactCheckGraph, build_fact_check_graph
from app.workflows.review_graph import build_review_graph

logger = logging.getLogger(__name__)


def build_fact_check(settings: Settings, llm: LLMClient) -> FactCheckGraph:
    """Load the corpus, index it and build the fact-check graph. Raises CorpusError."""
    corpus = load_corpus(settings.corpus_path)
    graph = build_fact_check_graph(
        llm,
        BM25Retriever(corpus),
        top_k=settings.fact_check_top_k,
        max_claims=settings.fact_check_max_claims,
    )
    logger.info("Fact-check ready: %d abstracts indexed", len(corpus))
    return graph


def create_app(settings: Settings | None = None, llm: LLMClient | None = None) -> FastAPI:
    """Build the FastAPI app. Tests pass their own settings and a FakeLLM."""
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = llm or build_llm_client(settings)

        fact_check_graph: FactCheckGraph | None = None
        fact_check_error = ""
        try:
            fact_check_graph = build_fact_check(settings, client)
        except CorpusError as exc:
            if settings.review_include_fact_check:
                # The review itself would not work, so refuse to start
                raise RuntimeError(f"REVIEW_INCLUDE_FACT_CHECK is true, but: {exc}") from exc
            # Grammar and style do not need the corpus: start, without fact-checking
            fact_check_error = str(exc)
            logger.warning("Fact-checking unavailable: %s", exc)

        app.state.settings = settings
        app.state.fact_check_graph = fact_check_graph
        app.state.fact_check_error = fact_check_error
        app.state.graph = build_review_graph(
            client,
            fact_check=fact_check_graph if settings.review_include_fact_check else None,
            fact_check_max_concurrency=settings.fact_check_max_concurrency,
        )
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
    app.include_router(fact_check.router)
    app.include_router(health.router)
    return app
