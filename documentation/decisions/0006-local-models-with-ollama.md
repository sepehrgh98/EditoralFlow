---
title: ADR 0006 - Local models with Ollama for development
summary: Ollama is the default LLM provider so development costs nothing; Claude stays available by setting; the OpenAI client is dropped from Phase 0.
status: accepted
updated: 2026-11-27
---

# ADR 0006: Local models with Ollama for development

- **Status:** Accepted
- **Date:** 2026-11-27
- **Amends:** [ADR 0002](0002-tech-stack.md), LLM row

## Context

The owner will run the app many times while building it. The Claude API is billed per token and is separate from a claude.ai or ChatGPT subscription. The development machine (Apple M4 Pro, 24 GB) can run 8B-14B open models locally with Ollama, which is already installed. Nothing in the app uses OpenAI, which ADR 0002 listed as optional.

## Options considered

1. **Ollama by default, Claude by setting; drop OpenAI from Phase 0.** **(chosen)**
2. **Claude only:** best quality, but every development run costs money.
3. **Free cloud API tiers:** tight limits, changing terms, some train on submitted data.

## Decision

- `LLM_PROVIDER` is `ollama` (default) or `anthropic`. Agents do not know which is used.
- Ollama tiers: `fast` = `qwen3:8b`, `strong` = `qwen3:14b` (both from settings). Thinking is off by default for speed (`OLLAMA_THINK`), and the context window is set to 16,384 tokens (`OLLAMA_NUM_CTX`) because Ollama's default is too small for long articles.
- Anthropic tiers: `fast` = `claude-haiku-5-5`, `strong` = `claude-sonnet-5-5`.
- The OpenAI client is not built. It can be added later behind the same `LLMClient` interface.

## Consequences

- Development and manual testing cost nothing; text never leaves the machine.
- Local models are weaker than Claude, especially for verification. Phase 1 (fact-checking) and Phase 2 (evaluations) should compare both and may switch the default.
- Ollama must be running with the model pulled (`ollama pull qwen3:8b`); the client reports a clear error otherwise.
- When the backend runs in Docker, `OLLAMA_HOST` must point to the host machine (`http://host.docker.internal:11434`); set in commit 7.
- The `openai` package stays until the old code that imports it is deleted in commit 7.
