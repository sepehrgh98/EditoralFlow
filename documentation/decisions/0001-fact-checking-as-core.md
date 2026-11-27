---
title: ADR 0001: Fact-checking is the core
summary: Decision to keep the editorial desk and make a fact-check agent its evaluated centrepiece.
status: accepted
updated: 2026-11-27
---

# ADR 0001: Fact-checking is the core of EditoralFlow

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

EditoralFlow started as an editorial quality desk: grammar, style and structure agents, style-guide RAG, duplicate detection, affiliate links and production infrastructure (see `Expert.docx`). Grammar and style review is a crowded space (Grammarly, Writer, Acrolinx) and its scores are subjective, so they are hard to evaluate with numbers.

## Options considered

1. Keep the original plan unchanged.
2. Pivot fully to a standalone fact-checker.
3. Keep the editorial desk and make fact-checking its deep core. **(chosen)**

## Decision

Keep the editorial desk, and make a fact-check agent its deep, evaluated centrepiece. It extracts claims, retrieves evidence from a trusted corpus with hybrid retrieval and reranking, and returns *supported*, *contradicted* or *can't tell* with a quoted source passage. Style-guide and duplicate agents reuse the same retrieval layer. A human editor approves every article.

## Consequences

- Measurable on public labelled datasets (SciFact first, then FEVER, HoVer, AVeriTeC).
- Covers all Tier 1 and Tier 2 concepts naturally.
- Fact-checking is harder than style review, so scope stays tight: one domain and a fixed corpus first.
- The affiliate agent and AWS migration are deferred.
