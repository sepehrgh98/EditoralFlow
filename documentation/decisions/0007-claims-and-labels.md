---
title: ADR 0007 - Claims and labels
summary: Fact-checking starts with SciFact (science and health), atomic self-contained claims and three verdict labels.
status: accepted
updated: 2026-11-27
---

# ADR 0007: Claims and labels

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

Phase 1 needs a domain, a definition of a "claim", and a set of verdicts. Phase 2 will score the system, so these choices should match an available labelled dataset.

## Options considered

1. Claims per sentence vs. **atomic, self-contained facts**.
2. **Three labels** vs. adding "partly supported".
3. **SciFact (science and health)** vs. FEVER (Wikipedia) or another domain.

## Decision

- Domain and corpus: SciFact, about 5,000 abstracts.
- Claims are atomic (one fact each) and self-contained (no unresolved pronouns), each linked to the exact draft sentence it came from.
- Three labels: `supported`, `contradicted`, `not_enough_info` (shown as "can't tell").

## Consequences

- Phase 2 scores directly against SciFact's labels.
- Atomic claims make search and verdicts more precise but mean more model calls per draft; a `max_claims` setting caps it.
- "Partly true" sentences are expressed as several atomic claims with different verdicts rather than a fourth label.
