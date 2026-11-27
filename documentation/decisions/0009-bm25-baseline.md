---
title: ADR 0009 - BM25 baseline
summary: Phase 1 searches with BM25 keyword search only, as the measured baseline for Phase 3's hybrid search.
status: accepted
updated: 2026-11-27
---

# ADR 0009: BM25 baseline

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

Hybrid retrieval with reranking is a Tier 1 concept for this project. Showing its value needs a measured baseline.

## Options considered

1. **BM25 only in Phase 1**, hybrid in Phase 3.
2. Vector search or hybrid from Phase 1.

## Decision

Phase 1 uses BM25 (`bm25s`, in memory, abstract-level) behind a `Retriever` interface. Phase 2 measures it; Phase 3 adds vector search and a reranker behind the same interface.

## Consequences

- A clear before/after comparison for Phase 3.
- No embedding model or vector database yet: free and simple.
- Claims phrased with different words from their source may be missed until Phase 3.
