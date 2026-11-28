---
title: ADR 0014 - Step-wise evaluation with oracle mode
summary: Each fact-check step (extract, retrieve, verify, cite) is scored separately; an oracle mode feeds the gold abstract to the verifier; one narrow LLM judge matches claims and is spot-checked by hand.
status: accepted
updated: 2026-11-27
---

# ADR 0014: Step-wise evaluation with oracle mode

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

The fact-checker is a pipeline. An end-to-end accuracy number can show that quality dropped but not which step caused it. SciFact provides gold abstracts, rationale sentences and labels, so each step can be graded on its own.

## Options considered

1. **Score each step separately, plus an oracle mode that skips retrieval.** **(chosen)**
2. End-to-end accuracy only.
3. An LLM judge grading whole answers on a 1-10 scale.

## Decision

- Retrieval: recall@1/3/10 and MRR (no LLM).
- Verification: accuracy, macro-F1, confusion matrix, flip rate (supported vs. contradicted swaps) and abstention rate.
- Citations: precision and recall against gold rationale sentences.
- Extraction and end-to-end: on assembled paragraphs; one LLM judge answers only "does extracted claim A mean the same as gold claim B?", at temperature 0 with the strong tier, spot-checked by hand on 20 pairs.
- Oracle mode gives the verifier the gold abstract so verifier errors can be separated from retrieval misses.
- Grammar is evaluated lightly with seeded injected errors; style is not scored until Phase 5.

## Consequences

- A score drop points to a step, and oracle vs. normal mode shows whether Phase 3 (retrieval) or prompt work will help more.
- More runners to maintain than a single end-to-end score.
- The judge's agreement rate with hand labels must be recorded and re-checked if its prompt or model changes.
