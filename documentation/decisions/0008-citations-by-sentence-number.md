---
title: ADR 0008 - Citations by sentence number
summary: The verifier cites sentence numbers; the code looks up the text, so quotes can never be invented.
status: accepted
updated: 2026-11-27
---

# ADR 0008: Citations by sentence number

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

A fact-checker that invents its quotes is worse than none. Free-text quotes from a model need a separate check that they exist in the source.

## Options considered

1. The verifier writes quotes; a citation guard checks them word for word.
2. **The verifier returns sentence numbers of the given abstracts; the code looks up the text.**

## Decision

Option 2. SciFact abstracts come split into sentences; the verifier sees them numbered and returns numbers. The code builds each `Citation` from the corpus. A `supported` or `contradicted` verdict with no valid numbers is downgraded to `not_enough_info`; invalid numbers are dropped.

## Consequences

- Every displayed quote exists word for word in the corpus, by construction.
- Works only for sources split into sentences; customer documents will need sentence splitting at indexing time.
- The Phase 4 citation guard becomes a check on relevance rather than existence.
