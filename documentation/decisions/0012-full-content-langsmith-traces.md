---
title: ADR 0012 - Full-content LangSmith traces
summary: Review and Fact-check traces send full inputs, outputs and errors to LangSmith; tracing stays opt-in. Supersedes ADR 0011's masking.
status: accepted
updated: 2026-11-27
---

# ADR 0012: Full-content LangSmith traces

- **Status:** Accepted
- **Date:** 2026-11-27
- **Supersedes:** [ADR 0011](0011-opt-in-langsmith-tracing.md) (masking of inputs, outputs and errors)

## Context

ADR 0011 masked graph inputs, outputs and error details in every app trace and kept only selected metadata. In practice a masked Review trace shows `{}` on every step, so it cannot answer the questions tracing is for: what draft text a claim came from, which abstracts search returned, what prompt the model saw, what it answered, and why a call failed. Full content was only available through a separate command for public SciFact claims.

## Options considered

1. **Send full content for every traced run.** **(chosen)**
2. Keep masking by default and add a switch to unmask for development.
3. Keep masking; use the public SciFact command for full traces.

## Decision

When tracing is enabled, the LangSmith client hides nothing: graph inputs and outputs, span inputs and outputs (draft, claims, query, passages, prompts, model answers, verdicts) and real error messages are all sent. Tracing remains opt-in through `LANGSMITH_TRACING` in the backend's environment and is off by default.

## Consequences

- Any Review or Fact-check run can be debugged step by step in LangSmith, with the same detail as the public SciFact command.
- With tracing on, every draft submitted to the app is stored on LangSmith's hosted service. Only enable it for drafts that may leave the machine; a production deployment needs its own decision (privacy, retention, a self-hosted option).
- The public SciFact command (`scripts/trace_scifact.py`) is still useful to trace a dataset claim by id, but is no longer the only way to see full content.
