---
title: Opt-in LangSmith tracing
summary: Use LangSmith to inspect Review runs, with raw graph data hidden in the local tracing setup.
status: superseded
updated: 2026-11-27
---

# ADR 0011 · Opt-in LangSmith tracing

- **Status:** Superseded by [ADR 0012](0012-full-content-langsmith-traces.md) (traces are no longer masked)
- **Date:** 2026-11-27

## Context

Backend logs record model usage and verdict totals. Debugging an individual verdict also requires seeing the steps that ran for its claim.

## Options considered

1. LangSmith tracing through the existing LangGraph integration.
2. A self-hosted tracing stack using Langfuse or Phoenix.
3. More detailed backend logs.

## Decision

Use LangSmith in development. Enable it through the backend process environment and apply SDK masking to graph inputs, outputs and metadata. Verify with public SciFact drafts.

## Consequences

A Review trace can show graph steps and timing together. Hosted verification requires LangSmith credentials. Custom retrieval and model call details will be added in the next tracing commit.
