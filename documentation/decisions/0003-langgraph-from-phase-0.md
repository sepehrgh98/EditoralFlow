---
title: ADR 0003 - LangGraph from Phase 0
summary: Run agents as LangGraph nodes from Phase 0 instead of adopting LangGraph only in Phase 5.
status: accepted
updated: 2026-11-27
---

# ADR 0003: LangGraph from Phase 0

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

The roadmap originally introduced LangGraph in Phase 5, with plain Python calls before that. The product is agentic at its core (the fact-check loop decides whether to search again), and every phase adds agents or steps.

## Options considered

1. **Phase 0, minimal graph:** existing agents become nodes with typed state; later phases add nodes and edges. **(chosen)**
2. **Phase 5, as planned:** plain function calls until orchestration is needed, then migrate.

## Decision

Introduce LangGraph in Phase 0 with a minimal graph: Prepare draft → Grammar and Style in parallel → Merge results. No checkpointer, human pause or loops until their phases.

## Consequences

- The graph is the backbone from day one; no rewrite in Phase 5.
- LangGraph is learned gradually, one feature per phase.
- One more dependency early; agent logic stays framework-free in `agents/`, so nodes are thin wrappers and agents remain testable on their own.
