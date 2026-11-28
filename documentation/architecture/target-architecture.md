---
title: Target architecture
summary: The end-state system design after Phase 7: components and how they connect.
status: agreed
updated: 2026-11-27
---

# Target architecture

This is where the system is heading, not what exists today (see `current-state.md`). One shared retrieval layer serves every review agent.

```mermaid
flowchart TD
    web[Editor web app<br/>Next.js review screen] --> api
    mcp[MCP clients<br/>Claude, Cursor, any tool] --> api
    evals[Eval harness<br/>runs in CI on SciFact] --> api
    api[FastAPI + job queue + workers] --> wf

    subgraph wf[LangGraph editorial workflow, checkpointed and resumable]
        grammar[Grammar] --> eic
        style[Style guide] --> eic
        dup[Duplicates] --> eic
        fact[Fact-check]:::core --> eic
        eic[Editor-in-chief proposes a decision] --> human[Editor approves]
    end

    wf --> retrieval[Hybrid retrieval<br/>BM25 + vectors + reranker]
    wf --> llm[LLM gateway<br/>routing, retries, cost]
    wf --> db[(Postgres<br/>checkpoints, jobs, audit log)]
    retrieval --> corpus[(Source corpus<br/>SciFact first, then customer documents)]

    classDef core stroke-width:3px
```

- **Clients:** the editor web app, MCP clients and the eval harness all call the same API.
- **Workflow:** four review agents run in parallel; fact-checking is the deep one. The editor-in-chief proposes a decision, then the workflow pauses for the human editor.
- **Shared services:** hybrid retrieval (used by fact-check, style-guide and duplicate agents), an LLM gateway (routing, retries, cost tracking) and Postgres (checkpoints, jobs, audit log).

## Planned stack

Each tool is added only in the phase that needs it. Recorded in [ADR 0002](../decisions/0002-tech-stack.md).

| Layer | Choice | Phase |
| --- | --- | --- |
| API | Python 3.12, FastAPI, Pydantic v2 | existing |
| Tooling | uv, ruff, pyright, pytest, pre-commit, GitHub Actions | 0 |
| LLM | Internal `LLMClient` interface; Ollama local models by default for development, Claude (Anthropic SDK) by setting ([ADR 0006](../decisions/0006-local-models-with-ollama.md)); fast tier for extraction/grammar, strong tier for verification | 0–1 |
| Keyword search | bm25s | 1 |
| Datasets | Hugging Face `datasets` (SciFact, later FEVER) | 1 |
| Evals and tracing | Own runner + LangSmith (tracing, optional experiments), see ADR 0013 | 1.5, 2 |
| Vector store | Qdrant | 3 |
| Embeddings and reranker | Local open models via sentence-transformers | 3 |
| Orchestration | LangGraph (graph from Phase 0, Postgres checkpointer from Phase 5) | 0, 5 |
| Database | Postgres (SQLAlchemy 2 + Alembic) | 5 |
| MCP | Hand-written JSON-RPC server | 6 |
| Queue | Redis + arq | 7 |
| Frontend | Next.js + TypeScript + Tailwind | existing |
| Deploy | Docker Compose locally; Vercel + Fly/Render + managed Postgres + Qdrant Cloud | 7 |

LangChain is deliberately not used for the RAG pipeline: retrieval, fusion and reranking are written by hand because that is the skill being shown.
