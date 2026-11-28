---
title: Roadmap
summary: The phased plan from MVP to production, with goals, scope, gates and deferred items.
status: agreed
updated: 2026-11-27
---

# Roadmap

The MVP ends at Phase 2. Each later stage starts only when the previous one passes its gate. Each phase begins with its own design discussion, recorded in `documentation/phases/`.

| Stage | Phases | Gate to move on |
| --- | --- | --- |
| **MVP** | 0 Clean foundation · 1 Fact-check MVP · 2 Eval harness | Baseline score recorded and running in CI |
| **Accuracy** | 3 Hybrid retrieval · 4 Self-correction | Beats the baseline on the eval |
| **Editorial desk** | 5 Orchestration · 6 MCP server | Survives a crash and resumes |
| **Ship and explain** | 7 Production · 8 Write-up | Public demo and results page |

## Phase 0: Clean foundation

- **Goal:** a codebase we can build on with confidence.
- **Scope:** layered backend structure; remove the duplicate LLM service; models from settings; structured output (JSON outputs) validated with Pydantic models; local models via Ollama by default, Claude by setting; retries, timeouts and token/cost tracking in the LLM layer; existing agents as a minimal LangGraph graph (Grammar and Style in parallel); pytest unit tests with a fake LLM; ruff, pyright and GitHub Actions; README; ADRs.
- **Design:** [phases/phase-0-foundation.md](../phases/phase-0-foundation.md)
- **Out of scope:** any new feature.
- **Done when:** CI is green on every push, and the existing grammar and style review still works.
- **Status:** done (2026-11-27). CI green; merged into `main`. See the design file's Outcome.

## Phase 1: Fact-check MVP

- **Goal:** the smallest version that checks facts end to end.
- **Scope:** SciFact abstracts as the corpus; BM25 keyword search only; a claim extractor; a verifier returning *supported*, *contradicted* or *can't tell* citing source sentences; the fact-check subgraph, alone via `POST /fact-check` and optionally inside the review graph; frontend highlights claims and shows evidence on click.
- **Design:** [phases/phase-1-fact-check-mvp.md](../phases/phase-1-fact-check-mvp.md)
- **Out of scope:** vector search, retries, orchestration, the queue.
- **Done when:** you paste a paragraph and see coloured claims with real citations.
- **Status:** implementation complete (2026-11-27). The live browser check confirmed highlights, exact SciFact quotations and an abstention without citations. See the design file's Outcome.

## Phase 2: Evaluation harness

- **Goal:** know how good it is, and catch it getting worse.
- **Scope:** eval runner over the SciFact dev set; verdict accuracy, evidence recall@k, citation correctness and abstention rate; a small hand-labelled set of real-style articles; LLM-as-a-judge for claim extraction; per-step traces to evaluate the trajectory; a CI job on a fixed subset that fails on regression; results table in the README.
- **Done when:** every pull request shows the score change, and a baseline is recorded.

## Phase 3: Hybrid retrieval and reranking

- **Goal:** find the right evidence more often.
- **Scope:** embeddings + Qdrant; BM25 + vector search fused with reciprocal rank fusion; cross-encoder reranker; metadata filters; ablation table (BM25, vector, hybrid, hybrid + rerank) on recall and latency.
- **Done when:** evidence recall beats the Phase 1 baseline, with numbers and latency cost written down.

## Phase 4: Self-correcting verification

- **Goal:** fewer wrong verdicts, and honest abstention.
- **Scope:** query rewriting and a second retrieval round; a token-budgeted context assembler; a confidence threshold for "can't tell"; a citation guard rejecting quotes not found word for word; a check for verdicts the evidence doesn't support.
- **Done when:** the eval shows the accuracy vs. abstention trade-off curve and the chosen operating point.

## Phase 5: Editorial desk orchestration

- **Goal:** turn the fact-checker into the full editorial desk.
- **Scope:** extend the LangGraph graph (in place since Phase 0) with style-guide (RAG) and duplicate agents; editor-in-chief step; Postgres checkpointing; retries per step; human approval pause and resume; revise loop.
- **Done when:** a run killed mid-review resumes after restart; nothing is approved without the editor.

## Phase 6: MCP server

- **Goal:** use EditoralFlow from any MCP client.
- **Scope:** tools `check_claims`, `search_sources`, `review_article`; hand-written JSON-RPC with Pydantic validation; read-only vs. write permissions; demo with Claude.
- **Done when:** an MCP client gets cited verdicts back.

## Phase 7: Production hardening

- **Goal:** behave like a real service.
- **Scope:** job queue and workers with job states; dashboard; observability (tokens, latency, cost per agent); model routing and retrieval caching; untrusted-document handling (prompt injection), PII masking in logs, audit log; lean deployment.
- **Done when:** a public demo URL works and the dashboard shows cost per article.

## Phase 8: Write-up

- **Goal:** make it all readable in 10 minutes.
- **Scope:** architecture doc with diagrams; ADRs collected; results page with benchmarks, ablations, cost per article and failure cases; 3-minute demo video.
- **Done when:** a newcomer understands what it does, how well it works and why it is built this way.

## Deliberately deferred

- **Affiliate / monetization agent** (original plan): low AI signal; unrelated to the core story.
- **AWS migration** (original plan): only after the lean deployment works.
- **Live web search:** harder to control and evaluate; later, as a clearly labelled fallback.
- **Three-layer memory:** possibly later, to remember each editor's overrides, once measurable.
- **GraphRAG:** only if multi-hop claims prove a real weakness and it beats hybrid retrieval on the eval.

## Open questions

Answered in the design discussion of the phase where they matter; each answer becomes an ADR.

| Question | Decided in |
| --- | --- |
| ~~Domain: science/health (SciFact) or another?~~ SciFact ([ADR 0007](../decisions/0007-claims-and-labels.md)) | decided |
| ~~Claim granularity: per sentence or atomic facts?~~ Atomic ([ADR 0007](../decisions/0007-claims-and-labels.md)) | decided |
| ~~Verdict labels: three, or add "partly supported"?~~ Three ([ADR 0007](../decisions/0007-claims-and-labels.md)) | decided |
| LLM choice for extraction vs. verification, monthly API budget | Phase 0–1 |
| Embeddings and reranker: hosted or local open model? | Phase 3 |
| ~~Orchestration: LangGraph or hand-written state machine?~~ LangGraph from Phase 0 ([ADR 0003](../decisions/0003-langgraph-from-phase-0.md)) | decided |
| Public style guide for the demo | Phase 5 |
| Weekly time budget and MVP target date | Phase 0 |
