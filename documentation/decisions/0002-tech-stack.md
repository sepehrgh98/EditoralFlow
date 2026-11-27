---
title: ADR 0002 - Tech stack
summary: The languages, libraries and services used, and the phase each one enters.
status: accepted
updated: 2026-11-27
---

# ADR 0002: Tech stack

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

The project needs a stack that is industry-standard for AI engineering roles, cheap to run, and lets the core skills (retrieval, verification, evaluation) be built by hand rather than hidden in a framework.

## Decision

Keep what exists (Python, FastAPI, Pydantic, Next.js) and add each tool only in the phase that needs it.

| Layer | Choice | Phase |
| --- | --- | --- |
| API | Python 3.12, FastAPI, Pydantic v2 | existing |
| Tooling | uv, ruff, pyright, pytest, pre-commit, GitHub Actions | 0 |
| LLM | Anthropic SDK behind an internal `LLMClient` interface (OpenAI optional); small model for extraction and grammar, strong model for verification | 0 |
| Orchestration | LangGraph (graph from Phase 0, Postgres checkpointer from Phase 5) | 0, 5 |
| Keyword search | bm25s | 1 |
| Datasets | Hugging Face `datasets` (SciFact, later FEVER) | 1 |
| Evals and tracing | Own runner on pytest + Langfuse | 2 |
| Vector store | Qdrant | 3 |
| Embeddings and reranker | Local open models via sentence-transformers | 3 |
| Database | Postgres (SQLAlchemy 2 + Alembic) | 5 |
| MCP | Hand-written JSON-RPC server | 6 |
| Queue | Redis + arq | 7 |
| Frontend | Next.js + TypeScript + Tailwind | existing |
| Deploy | Docker Compose locally; Vercel + Fly/Render + managed Postgres + Qdrant Cloud | 7 |

LangChain is not used for the RAG pipeline: retrieval, fusion and reranking are written by hand.

## Consequences

- Few moving parts early; each service arrives with a reason.
- Choices marked for Phase 3 (embeddings, Qdrant vs. pgvector) are confirmed in that phase's design and may be superseded.
- Open: monthly API budget, which sets the size of the CI eval subset (decided in Phase 2).
