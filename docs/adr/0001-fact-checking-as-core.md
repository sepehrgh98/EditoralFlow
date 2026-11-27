# ADR 0001: Fact-checking is the core of EditoralFlow

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

EditoralFlow started as an editorial quality desk: grammar, style and structure agents, style-guide RAG, duplicate detection, affiliate links and production infrastructure (see `Expert.docx`). Grammar and style review is a crowded space (Grammarly, Writer, Acrolinx) and its scores are subjective, so they are hard to evaluate with numbers.

## Decision

Keep the editorial desk, and make a fact-check agent its deep, evaluated centrepiece. The agent extracts claims from a draft, retrieves evidence from a trusted corpus with hybrid retrieval and reranking, and returns *supported*, *contradicted* or *can't tell* with a quoted source passage. The style-guide and duplicate agents reuse the same retrieval layer. A human editor approves every article.

Options considered: keep the original plan unchanged; pivot fully to a standalone fact-checker; editorial desk with a fact-check core (chosen).

## Consequences

- The project can be measured on public labelled datasets (SciFact first, then FEVER, HoVer, AVeriTeC).
- It covers all Tier 1 and Tier 2 concepts from `concept-priorities.md` naturally.
- Fact-checking is harder than style review, so scope stays tight: one domain and a fixed corpus first.
- The affiliate agent and AWS migration are deferred.
