---
title: ADR 0015 - CI eval gate on retrieval
summary: CI runs the free, deterministic retrieval eval on every push and pull request and compares it with a committed baseline; LLM evals run locally for now.
status: accepted
updated: 2026-11-27
---

# ADR 0015: CI eval gate on retrieval

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

The roadmap asks CI to catch quality regressions. CI cannot run Ollama, a full LLM run on the dev set takes about an hour locally, and paid model calls on every push add cost and noise.

## Options considered

1. **CI runs the retrieval eval (no LLM) on every push and PR against `baseline.json`; LLM evals run locally.** **(chosen)**
2. Option 1 plus a small paid Claude run on pull requests to `main`.
3. Full LLM evals in CI.

## Decision

On every push and pull request, CI runs the metric unit tests and the full retrieval eval on SciFact dev, then compares it with `backend/evals/baseline.json`. A metric that drops beyond its margin fails the build. LLM evals (verifier, extraction, end-to-end, grammar) run locally with `make eval`, and their results are committed with the baseline. Option 2 is deferred, not rejected.

## Consequences

- CI stays fast, free and deterministic, and catches search regressions.
- Regressions in LLM steps are caught only when someone runs `make eval` locally; the baseline in each PR makes that visible in review.
- Revisit when a CI-safe LLM budget exists.
