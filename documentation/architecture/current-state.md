---
title: Current state
summary: What the code does today, file by file, and its known weaknesses. Update after every phase.
status: current
updated: 2026-11-27
---

# Current state

Snapshot of the codebase during Phase 0 (commit 3 of 9). New `core/` and `llm/` code exists but the request flow below still uses the old code. Replace this file's content whenever the structure changes.

## What it does

Paste an article in the frontend; a grammar agent and a style agent each return a score, a list of issues and a summary.

## Request flow

1. `frontend/src/app/page.tsx` sends the article to `POST /review`.
2. `backend/app/routes/review.py` calls `ReviewWorkflow.run(article)`.
3. `backend/app/workflows/review_workflow.py` runs `GrammarAgent` then `StyleAgent` on a state dict.
4. `backend/app/agents/base_agent.py` loads the prompt from `agents/prompts/`, fills in the article and calls `llm.generate(prompt)`.
5. `backend/app/services/llm/anthropic_service.py` calls Claude and returns plain text.
6. The agent strips code fences, runs `json.loads` and builds an `AgentResult` (`models/agent_result.py`).

## Files

| Path | Role |
| --- | --- |
| `backend/app/main.py` | FastAPI app, CORS |
| `backend/app/routes/review.py` | `POST /review` |
| `backend/app/workflows/review_workflow.py` | Runs the two agents in sequence |
| `backend/app/workflows/state.py` | `ReviewState` (unused) |
| `backend/app/agents/` | `BaseAgent`, `GrammarAgent`, `StyleAgent`, prompt files |
| `backend/app/services/llm/` | `BaseLLMService`, Anthropic and OpenAI services, factory; `llm_service.py` is a duplicate |
| `backend/app/models/agent_result.py` | `Issue`, `AgentResult` |
| `backend/app/utils/prompt_loader.py` | Reads prompt files |
| `backend/app/core/config.py` | `Settings` (pydantic-settings) from env and `backend/.env`: provider, API keys, model names, LLM timeout/retries/max tokens, log level, CORS. Fails clearly if the provider's key is missing. Not wired into the app yet (commit 7) |
| `backend/app/core/logging.py` | `setup_logging(level)`: one log format for the app. Not wired in yet |
| `backend/app/llm/base.py` | `LLMClient` async interface (`generate`, `generate_structured`, model tier `fast`/`strong`), `LLMResponse`, `Usage`, `LLMError`, `LLMOutputError`. Not used by the app yet |
| `backend/app/llm/fake.py` | `FakeLLM`: canned answers in order, schema validation, call recording; for tests |
| `backend/.env.example` | Every setting with placeholder values |
| `backend/tests/` | pytest suite (`test_config.py`, `test_llm_fake.py`); async tests via pytest-asyncio |
| `backend/pyproject.toml`, `uv.lock` | Dependencies and ruff/pyright/pytest config, managed by uv |
| `backend/app/tests/test_anthropic.py` | Manual smoke script, not a real test |
| `frontend/` | Next.js page showing scores and issues |
| `Expert.docx` | Original 10-phase plan |

## Known weaknesses (addressed in Phase 0)

- JSON parsed from free text; breaks on any stray output.
- Workflow created at import time; a missing API key crashes the app.
- Hard-coded, outdated model names; duplicate LLM service file.
- No retries, timeouts, token or cost tracking.
- No tests, no CI; README was empty.
