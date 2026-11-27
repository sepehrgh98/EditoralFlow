---
title: ADR 0010 - Fact-check as a subgraph
summary: The fact-check graph is one compiled subgraph used alone via /fact-check and as an optional branch of the review graph.
status: accepted
updated: 2026-11-27
---

# ADR 0010: Fact-check as a subgraph

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

The target design runs fact-checking as one branch of the editorial desk. Fact-checking is also slow (many model calls) and still unreliable in Phase 1.

## Options considered

1. A separate graph and endpoint until Phase 5.
2. **One compiled subgraph used in both places, with the review-graph branch behind a setting.**
3. Fact-check always inside `/review`.

## Decision

Option 2. `POST /fact-check` runs the subgraph alone. The review graph includes it as a `fact_check` node when `REVIEW_INCLUDE_FACT_CHECK=true` (off by default).

## Consequences

- Same code in both places; already the target shape.
- `/review` stays fast by default; the flag can be turned on once Phase 4 makes fact-checking reliable.
- The review response gains an optional `fact_check_result` field.
