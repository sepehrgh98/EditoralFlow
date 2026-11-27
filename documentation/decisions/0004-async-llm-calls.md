---
title: ADR 0004 - Async LLM calls
summary: The LLM layer, agents and graph nodes are async from Phase 0.
status: accepted
updated: 2026-11-27
---

# ADR 0004: Async LLM calls

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

The `LLMClient` interface (Phase 0, commit 3) fixes how every agent calls a model. Phase 0 runs only two calls per review, but Phase 1 fact-checks each claim in its own branch, so one review will make many LLM calls at once. FastAPI, LangGraph and the Anthropic and OpenAI SDKs all support async natively.

## Options considered

1. **Async (`async def`, `await`) from Phase 0.** **(chosen)**
2. **Sync now,** relying on LangGraph running parallel sync nodes in threads; switch later if needed.

## Decision

`LLMClient.generate` and `generate_structured` are `async`. Agents and graph nodes that call them are async too. Tests use `pytest-asyncio` in auto mode.

## Consequences

- Many concurrent LLM calls without threads; no rewrite of the LLM layer, agents and tests in Phase 1.
- Code needs `async`/`await` throughout the call chain; sync code cannot call these methods directly.
- One extra dev dependency (`pytest-asyncio`).
