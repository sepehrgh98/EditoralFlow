---
title: Current state
summary: What the code does today, file by file, and its known weaknesses. Update after every phase.
status: current
updated: 2026-11-27
---

# Current state

Snapshot after Phase 1.5. The frontend offers one Review workflow for grammar and style. When fact-checking is enabled in review, it also displays highlighted draft sentences and citations. The API exposes standalone fact-checking through `POST /fact-check`.

With LangSmith tracing enabled in the backend process, the graph run is named `EditoralFlow Review`. Traces include full inputs, outputs and error messages (ADR 0012), plus span metadata such as claim ID, retrieved documents, model, latency, verdict and citation IDs. Search, verification and structured model calls add child spans under the graph nodes.

The public SciFact trace command in `backend/scripts/trace_scifact.py` runs a dataset claim by ID and records full inputs and outputs for that run.

## What it does

Paste an article in the frontend; a grammar agent and a style agent review it in parallel and each return a score from 0 to 100, a list of issues and a summary. By default the agents run on a local model through Ollama (free); Claude can be used by setting `LLM_PROVIDER=anthropic`.

## Request flow

1. `frontend/src/app/page.tsx` sends the draft to `POST /review`.
2. `backend/app/api/review.py` validates the body and runs the review graph built at startup.
3. `backend/app/workflows/review_graph.py`: Prepare draft tidies the text, then Grammar and Style run at the same time, then Merge results builds the response and logs the review's total tokens, time and cost.
4. Each agent (`backend/app/agents/`) sends its system prompt and the article to `LLMClient.generate_structured(..., AgentResult)`.
5. `backend/app/llm/ollama.py` (or `anthropic.py`) asks the model for an answer in the `AgentResult` shape, validates it, retries once if invalid, and logs model, tokens, latency and cost.
6. The API returns `{grammar_result, style_result}` by default and includes `fact_check_result` when `REVIEW_INCLUDE_FACT_CHECK=true`. LLM failures return 503 (unreachable, timeout) or 502 (invalid answer) with a clear `detail`.

`POST /fact-check` validates the same article body as `/review` and runs the fact-check graph. It extracts claims, searches SciFact for each claim with BM25, and returns verdicts, citations and counts. The server builds the index at startup. If the corpus cannot load, fact-check requests return 503 with the reason and health reports `fact_check: unavailable`. When review is configured to include fact-checking, a corpus load failure stops startup.

## Files

| Path | Role |
| --- | --- |
| `backend/app/main.py` | `create_app()` factory: settings, logging, CORS; at startup builds the LLM client, BM25 index and graphs once. Started with `uvicorn --factory app.main:create_app` |
| `backend/app/api/review.py` | `POST /review`: rejects blank articles (422), maps `LLMError` to 503 and `LLMOutputError` to 502 |
| `backend/app/api/fact_check.py` | `POST /fact-check`: runs the fact-check graph with the configured concurrency limit |
| `backend/app/api/schemas.py`, `errors.py` | Shared article validation (422 for blank text) and model error mapping (502 or 503) |
| `backend/app/api/health.py` | `GET /health`: status, LLM provider and fact-check readiness |
| `backend/app/api/deps.py` | Reads settings and graphs from app state; returns 503 when fact-checking is unavailable |
| `backend/app/core/config.py` | `Settings` (pydantic-settings) from env and `backend/.env`: provider (`ollama` default, or `anthropic`), Ollama host/models/context/thinking, Anthropic key and models, LLM timeout/retries/max tokens, corpus path, fact-check limits, review fact-check flag, log level and CORS. Fails clearly if Anthropic is chosen without a key |
| `backend/app/core/tracing.py` | Configures an opt-in LangSmith client for both graph entry points and filters trace data |
| `backend/app/core/logging.py` | `setup_logging(level)`: one log format; quiets routine logs from `httpx` and `bm25s` |
| `backend/app/llm/base.py` | `LLMClient` async interface (`generate`, `generate_structured`, tier `fast`/`strong`), `LLMResponse`, `Usage`, `LLMError`, `LLMOutputError`, `log_usage()` |
| `backend/app/llm/ollama.py` | `OllamaClient`: local models (default `qwen3:8b` / `qwen3:14b`), JSON-schema `format`, one retry on an invalid answer, clear errors when Ollama is down or a model is missing |
| `backend/app/llm/anthropic.py` | `AnthropicClient`: Claude via JSON outputs; SDK retries/backoff and timeout from settings; refusal and cut-off errors; one retry on an invalid answer |
| `backend/app/llm/pricing.py` | Price table and `estimate_cost()` |
| `backend/app/llm/factory.py` | `build_llm_client(settings)` picks the client from `LLM_PROVIDER` |
| `backend/app/agents/base.py` | Generic `BaseAgent[R]`: loads `prompts/<agent>/system.txt` and `user.txt`, checks the declared slots, fills them in one pass (`run(**values)`), calls `generate_structured` with the agent's `output_schema` and `tier`, returns result + usage. `ReviewAgent` adds `review(article)` with `AgentResult` |
| `backend/app/agents/grammar.py`, `style.py` | `GrammarAgent`, `StyleAgent`: `ReviewAgent`s that name their prompt folder |
| `backend/app/agents/claim_extractor.py` | `ClaimExtractor` (fast tier, slot `article`): `extract(draft)` returns `Claim`s numbered `c1`..., empty and repeated claims removed, at most `max_claims` (20) |
| `backend/app/agents/verifier.py` | `Verifier` (strong tier, slots `claim`, `passages`): numbers the abstracts' sentences 1..N, asks for `explanation`, `sentence_numbers`, `label`, builds citations from the corpus, downgrades unproven verdicts to `not_enough_info`; no model call when there are no passages |
| `backend/app/agents/prompts/` | `verifier/` (judge only from the given sentences; when unsure, can't tell); `claim_extractor/` (rules for atomic, self-contained claims plus one worked example); `grammar/` and `style/`, each with `system.txt` (job, rules, 0-100 score scale) and `user.txt` (`{article}` slot) |
| `backend/app/retrieval/corpus.py` | `Document` (doc id, title, numbered sentences), `Corpus` (count, iterate, lookup by id), `load_corpus(path)` for SciFact-format files; clear errors for a missing or broken file |
| `backend/app/retrieval/base.py` | `Passage` (document + score) and the async `Retriever` interface: `search(query, k)` |
| `backend/app/retrieval/bm25.py` | `BM25Retriever` (`bm25s` + English stemming, stopwords dropped), title + abstract indexed in memory (about 0.35 s for 5,183 abstracts); returns up to k passages with score > 0 |
| `backend/scripts/download_scifact.py` | `make data`: downloads the official SciFact release once into `backend/data/scifact/` (gitignored), keeps `corpus.jsonl` (5,183 abstracts) and the claim files, extracting only those named files |
| `backend/app/models/review.py` | `Issue`, `AgentResult` (score 0-100), `ReviewResponse` (with optional `fact_check_result`, left out of the JSON when absent), with field descriptions the model reads |
| `backend/app/models/fact_check.py` | `Claim`, `Citation`, `Verdict` (labels `supported` / `contradicted` / `not_enough_info`), `ClaimResult`, `FactCheckResponse` with `counts` computed from results |
| `backend/app/workflows/state.py` | `ReviewInput`, `ReviewState` (with a `usage` reducer and optional `fact_check_result`), `ReviewUpdate` |
| `backend/app/workflows/review_graph.py` | LangGraph graph: Prepare draft -> Grammar and Style (and Fact-check, if a fact-check graph is given) in parallel -> Merge results; `build_review_graph(llm, fact_check=None, *, fact_check_max_concurrency=4)`, `run_review(graph, article)` |
| `backend/app/workflows/fact_check_state.py` | `FactCheckState` (`results` and `usage` reducers) and the per-claim `ClaimState` |
| `backend/app/workflows/fact_check_graph.py` | Fact-check graph: `extract_claims` -> `Send` one `check_claim` (retrieve -> verify) per claim -> `collect` (claim order, summary log); `build_fact_check_graph(llm, retriever, top_k=3, max_claims=20)`, `run_fact_check(graph, article, max_concurrency=4)` |
| `backend/tests/` | pytest suite (config, fake, Ollama, Anthropic, factory, pricing, agent, graph and API tests); `fixtures/scifact_corpus.jsonl` is a 5-abstract fictional corpus used instead of the download; `fakes.py` holds `FakeLLM` (canned answers in order or from a responder function, schema validation, call recording); async tests via pytest-asyncio |
| `backend/.env.example` | Every setting with defaults and comments |
| `backend/pyproject.toml`, `uv.lock`, `.python-version` | Dependencies and ruff/pyright/pytest config, managed by uv; Python pinned to 3.12 to match the Docker image |
| `backend/Dockerfile`, `docker-compose.yml` | Backend image installed from the lock; Compose points `OLLAMA_HOST` at the Mac (`host.docker.internal`), since Ollama runs natively for GPU access |
| `Makefile`, `backend/Makefile` | `make start` / `stop` / `logs` (Docker), `make dev` (without Docker), `make check` (ruff lint + format check, pyright, tests), `make test-live` (real model), `make hooks` (turn on pre-commit), `make data` (download SciFact) |
| `.github/workflows/ci.yml` | GitHub Actions: on every push and pull request, ruff, pyright and pytest for the backend (fake LLM only, no cost) |
| `.pre-commit-config.yaml` | ruff check and format on changed backend files at each commit |
| `backend/tests/test_live.py` | Live tests against the model in settings; marker `live`, skipped unless `make test-live` |
| `frontend/src/app/page.tsx` | Sends the draft to the review API and displays scores, issues and optional fact-check evidence |
| `frontend/src/app/fact-check.tsx` | Matches claim source sentences against the draft, highlights verdicts and shows evidence for matched and unmatched claims |
| `Expert.docx` | Original 10-phase plan |

## Known weaknesses

- Frontend has no automated checks in CI. Phase 1 verified the live browser flow on five SciFact claims. Systematic evaluation is planned for Phase 2.
- The local 8B model sometimes reports an issue under the wrong agent (a style issue from the grammar agent) or merges two problems into one issue. Prompt tuning and measurement come with evaluations in Phase 2.
- Ollama answers one request at a time unless `OLLAMA_NUM_PARALLEL` is raised, so the two agents' calls queue there.
- The style check judges against general good writing, not a house style guide; the Phase 5 style-guide agent will retrieve the publication's rules and cite them.
- If one agent fails, the whole review fails; partial results are left for a later phase.
- The frontend shows a generic review error. The API supplies the error detail.
