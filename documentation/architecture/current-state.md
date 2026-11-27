---
title: Current state
summary: What the code does today, file by file, and its known weaknesses. Update after every phase.
status: current
updated: 2026-11-27
---

# Current state

Snapshot during Phase 1, after commit 3 of 9: the Phase 0 app is unchanged; the SciFact corpus can be downloaded, loaded and searched with BM25, and the fact-check data shapes exist, but nothing in the app uses them yet.

## What it does

Paste an article in the frontend; a grammar agent and a style agent review it in parallel and each return a score from 0 to 100, a list of issues and a summary. By default the agents run on a local model through Ollama (free); Claude can be used by setting `LLM_PROVIDER=anthropic`.

## Request flow

1. `frontend/src/app/page.tsx` sends the article to `POST /review` (unchanged).
2. `backend/app/api/review.py` validates the body and runs the review graph built at startup.
3. `backend/app/workflows/review_graph.py`: Prepare draft tidies the text, then Grammar and Style run at the same time, then Merge results builds the response and logs the review's total tokens, time and cost.
4. Each agent (`backend/app/agents/`) sends its system prompt and the article to `LLMClient.generate_structured(..., AgentResult)`.
5. `backend/app/llm/ollama.py` (or `anthropic.py`) asks the model for an answer in the `AgentResult` shape, validates it, retries once if invalid, and logs model, tokens, latency and cost.
6. The API returns `{grammar_result, style_result}`. LLM failures return 503 (unreachable, timeout) or 502 (invalid answer) with a clear `detail`.

## Files

| Path | Role |
| --- | --- |
| `backend/app/main.py` | `create_app()` factory: settings, logging, CORS; at startup builds the LLM client and the graph once. Started with `uvicorn --factory app.main:create_app` |
| `backend/app/api/review.py` | `POST /review`: rejects blank articles (422), maps `LLMError` to 503 and `LLMOutputError` to 502 |
| `backend/app/api/health.py` | `GET /health`: `{"status": "ok", "provider": ...}` |
| `backend/app/api/deps.py` | Reads settings and graph from the app state for the routes |
| `backend/app/core/config.py` | `Settings` (pydantic-settings) from env and `backend/.env`: provider (`ollama` default, or `anthropic`), Ollama host/models/context/thinking, Anthropic key and models, LLM timeout/retries/max tokens, log level, CORS. Fails clearly if Anthropic is chosen without a key |
| `backend/app/core/logging.py` | `setup_logging(level)`: one log format; quiets routine logs from `httpx` and `bm25s` |
| `backend/app/llm/base.py` | `LLMClient` async interface (`generate`, `generate_structured`, tier `fast`/`strong`), `LLMResponse`, `Usage`, `LLMError`, `LLMOutputError`, `log_usage()` |
| `backend/app/llm/ollama.py` | `OllamaClient`: local models (default `qwen3:8b` / `qwen3:14b`), JSON-schema `format`, one retry on an invalid answer, clear errors when Ollama is down or a model is missing |
| `backend/app/llm/anthropic.py` | `AnthropicClient`: Claude via JSON outputs; SDK retries/backoff and timeout from settings; refusal and cut-off errors; one retry on an invalid answer |
| `backend/app/llm/pricing.py` | Price table and `estimate_cost()` |
| `backend/app/llm/factory.py` | `build_llm_client(settings)` picks the client from `LLM_PROVIDER` |
| `backend/app/agents/base.py` | Generic `BaseAgent[R]`: loads `prompts/<agent>/system.txt` and `user.txt`, checks the declared slots, fills them in one pass (`run(**values)`), calls `generate_structured` with the agent's `output_schema` and `tier`, returns result + usage. `ReviewAgent` adds `review(article)` with `AgentResult` |
| `backend/app/agents/grammar.py`, `style.py` | `GrammarAgent`, `StyleAgent`: `ReviewAgent`s that name their prompt folder |
| `backend/app/agents/prompts/` | `grammar/` and `style/`, each with `system.txt` (job, rules, 0-100 score scale) and `user.txt` (`{article}` slot) |
| `backend/app/retrieval/corpus.py` | `Document` (doc id, title, numbered sentences), `Corpus` (count, iterate, lookup by id), `load_corpus(path)` for SciFact-format files; clear errors for a missing or broken file. Not used by the app yet |
| `backend/app/retrieval/base.py` | `Passage` (document + score) and the async `Retriever` interface: `search(query, k)` |
| `backend/app/retrieval/bm25.py` | `BM25Retriever` (`bm25s` + English stemming, stopwords dropped), title + abstract indexed in memory (about 0.35 s for 5,183 abstracts); returns up to k passages with score > 0. Not used by the app yet |
| `backend/scripts/download_scifact.py` | `make data`: downloads the official SciFact release once into `backend/data/scifact/` (gitignored), keeps `corpus.jsonl` (5,183 abstracts) and the claim files, extracting only those named files |
| `backend/app/models/review.py` | `Issue`, `AgentResult` (score 0-100), `ReviewResponse`, with field descriptions the model reads |
| `backend/app/models/fact_check.py` | `Claim`, `Citation`, `Verdict` (labels `supported` / `contradicted` / `not_enough_info`), `ClaimResult`, `FactCheckResponse` with `counts` computed from results. Not used by the app yet |
| `backend/app/workflows/state.py` | `ReviewInput`, `ReviewState` (with a `usage` reducer), `ReviewUpdate` |
| `backend/app/workflows/review_graph.py` | LangGraph graph: Prepare draft -> Grammar and Style in parallel -> Merge results; `build_review_graph(llm)`, `run_review(graph, article)` |
| `backend/tests/` | pytest suite (config, fake, Ollama, Anthropic, factory, pricing, agent, graph and API tests); `fixtures/scifact_corpus.jsonl` is a 5-abstract fictional corpus used instead of the download; `fakes.py` holds `FakeLLM` (canned answers in order or from a responder function, schema validation, call recording); async tests via pytest-asyncio |
| `backend/.env.example` | Every setting with defaults and comments |
| `backend/pyproject.toml`, `uv.lock`, `.python-version` | Dependencies and ruff/pyright/pytest config, managed by uv; Python pinned to 3.12 to match the Docker image |
| `backend/Dockerfile`, `docker-compose.yml` | Backend image installed from the lock; Compose points `OLLAMA_HOST` at the Mac (`host.docker.internal`), since Ollama runs natively for GPU access |
| `Makefile`, `backend/Makefile` | `make start` / `stop` / `logs` (Docker), `make dev` (without Docker), `make check` (ruff lint + format check, pyright, tests), `make test-live` (real model), `make hooks` (turn on pre-commit), `make data` (download SciFact) |
| `.github/workflows/ci.yml` | GitHub Actions: on every push and pull request, ruff, pyright and pytest for the backend (fake LLM only, no cost) |
| `.pre-commit-config.yaml` | ruff check and format on changed backend files at each commit |
| `backend/tests/test_live.py` | Live tests against the model in settings; marker `live`, skipped unless `make test-live` |
| `frontend/` | Next.js page showing scores and issues (unchanged) |
| `Expert.docx` | Original 10-phase plan |

## Known weaknesses

- Frontend has no tests or lint in CI.
- The local 8B model sometimes reports an issue under the wrong agent (a style issue from the grammar agent) or merges two problems into one issue. Prompt tuning and measurement come with evaluations in Phase 2.
- Ollama answers one request at a time unless `OLLAMA_NUM_PARALLEL` is raised, so the two agents' calls queue there.
- The style check judges against general good writing, not a house style guide; the Phase 5 style-guide agent will retrieve the publication's rules and cite them.
- If one agent fails, the whole review fails; partial results are left for a later phase.
- The frontend shows a generic error message; the precise reason is in the backend logs and the response `detail`.
