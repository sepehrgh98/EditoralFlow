---
title: ADR 0013 - Own eval runner with optional LangSmith experiments
summary: Phase 2 evals run in our own Python harness writing JSON and Markdown scorecards; uploading a run as a LangSmith experiment is opt-in. Replaces Langfuse in ADR 0002.
status: accepted
updated: 2026-11-27
---

# ADR 0013: Own eval runner with optional LangSmith experiments

- **Status:** Accepted
- **Date:** 2026-11-27
- **Supersedes:** the "Evals and tracing" row of [ADR 0002](0002-tech-stack.md) (Langfuse)

## Context

ADR 0002 planned an own runner on pytest plus Langfuse. Since then, Phase 1.5 adopted LangSmith for tracing (ADRs 0011 and 0012). The eval harness must run offline, in CI without accounts, and its metric code should be ours to read and explain.

## Options considered

1. **Own runner writing scorecard files, with an opt-in LangSmith experiment upload.** **(chosen)**
2. Only LangSmith datasets and evaluators.
3. Own runner plus Langfuse, as ADR 0002 planned.

## Decision

`backend/evals/` is a plain Python package with a CLI (`python -m evals run ...`). Metrics are pure functions with unit tests. Each run writes `scorecard.json` and `scorecard.md`; a committed `baseline.json` is the reference. `--langsmith` additionally uploads the run as a LangSmith experiment. Langfuse is dropped: one hosted tool is enough.

## Consequences

- Every number can be reproduced without a LangSmith account or network access.
- LangSmith adds side-by-side run comparison and click-through from a wrong answer to its trace, when wanted.
- We maintain our own metric code and report format.
