---
title: ADR 0005 - JSON outputs for structured answers
summary: Get schema-shaped answers from Claude with JSON outputs (output_config.format), not forced tool use.
status: accepted
updated: 2026-11-27
---

# ADR 0005: JSON outputs for structured answers

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

The Phase 0 design said agents get structured answers through forced tool use: the Pydantic schema becomes a tool and Claude must call it (`tool_choice` `tool`). Claude Sonnet 5.5, our strong model, rejects forced `tool_choice` with a 400 error. The API now has JSON outputs (`output_config.format` with a JSON schema), which constrains the answer to the schema and works on Haiku 5.5 and Sonnet 5.5.

## Options considered

1. **JSON outputs** (`output_config.format`), schema made API-compatible with the SDK's `transform_schema`, answer validated with Pydantic. **(chosen)**
2. **Tool use with `tool_choice: auto`** plus a prompt instruction to call the tool; check a call was made and re-prompt if not.
3. **Forced tool use** as designed: does not work on Sonnet 5.5.

## Decision

`AnthropicClient.generate_structured` uses JSON outputs through `messages.create` with `output_config.format`. It then checks `stop_reason` (refusal, cut off) and validates the text with Pydantic, retrying once on a validation failure. `messages.parse` is not used, because it validates before we can see the stop reason. Ollama uses the equivalent `format` parameter.

## Consequences

- One mechanism for both Claude tiers and for Ollama; less code than a tool round-trip.
- Refusals and cut-off answers get their own clear errors instead of a generic validation error.
- Schema features JSON outputs does not support (such as numeric limits) are moved into descriptions by `transform_schema` and enforced by our Pydantic validation.
