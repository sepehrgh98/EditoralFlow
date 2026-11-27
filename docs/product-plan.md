# EditoralFlow Product Plan

_Last updated: 2026-11-27_

## The product

EditoralFlow is an AI editorial desk. It reviews a draft for quality and fit with house rules, checks every factual statement against the customer's trusted sources, and lets an editor approve it with the evidence in hand.

- **Problem:** teams publish more text than ever, much of it AI-written, and can't afford to check every fact by hand. Wrong or invented facts get published.
- **Solution:** for each claim, the system shows the source passage that backs it up or contradicts it, or honestly says "can't tell". A human makes the final call.
- **Who it's for:** editors at content agencies, publishers and in-house content teams. For now it's a skills project; a commercial version would swap in a customer's corpus.
- **Approach:** start with the smallest useful version and harden it one layer at a time. Each phase ends with something that runs and a number that proves it.

## Starting point

The current code is a working Phase 1 of the original plan (`Expert.docx`): paste an article, and a grammar agent and a style agent each return a score, issues and a summary. It's a good base, but the core needs cleaning before we build on it.

| Area | What exists | What to fix |
| --- | --- | --- |
| Backend | FastAPI, one `POST /review` endpoint | Synchronous only; agents built at import time |
| LLM layer | Provider interface with Anthropic and OpenAI behind a factory | Duplicate `llm_service.py`; old model names; no retries or token tracking |
| Agents | Grammar and style agents, prompts in text files | JSON parsed from raw text; switch to structured output (tool use) with Pydantic validation |
| Workflow | Agents called one after another | `ReviewState` defined but unused; no orchestration |
| Frontend | Next.js page showing scores and issues | No highlighting inside the text; no history |
| Quality | One manual Anthropic smoke script | No unit tests, no evals, no CI, empty README |
| Plan | `Expert.docx`: 10 phases from MVP to AWS | Keep the infra ideas; move fact-checking to the centre; drop the affiliate agent |

## Design principles

1. **Measure before you improve.** Each feature lands with a metric on the eval set. No "it feels better".
2. **Proof or abstain.** Every verdict carries a source quote that exists word for word in the corpus, or it says "can't tell".
3. **Simple first.** Each phase adds one layer. Nothing is built for a need we don't have yet.
4. **One retrieval layer, many agents.** The fact-check, style-guide and duplicate agents share the same search.
5. **Human in charge.** The system proposes; the editor decides. Nothing is approved automatically.
6. **Write decisions down.** Every significant choice gets a short ADR in `docs/adr/` when it's made, not at the end.
7. **Swappable parts.** The LLM provider, the embedding model, the vector store and the corpus sit behind interfaces.

## Target architecture

One shared retrieval layer serves every review agent.

```mermaid
flowchart TD
    web[Editor web app<br/>Next.js review screen] --> api
    mcp[MCP clients<br/>Claude, Cursor, any tool] --> api
    evals[Eval harness<br/>runs in CI on SciFact] --> api
    api[FastAPI + job queue + workers] --> wf

    subgraph wf[LangGraph editorial workflow, checkpointed and resumable]
        grammar[Grammar] --> eic
        style[Style guide] --> eic
        dup[Duplicates] --> eic
        fact[Fact-check]:::core --> eic
        eic[Editor-in-chief proposes a decision] --> human[Editor approves]
    end

    wf --> retrieval[Hybrid retrieval<br/>BM25 + vectors + reranker]
    wf --> llm[LLM gateway<br/>routing, retries, cost]
    wf --> db[(Postgres<br/>checkpoints, jobs, audit log)]
    retrieval --> corpus[(Source corpus<br/>SciFact first, then yours)]

    classDef core stroke-width:3px
```

Three kinds of client call one API. The workflow runs four review agents in parallel, with fact-checking as the deep one, then pauses for the editor. Every agent that searches uses the same hybrid retrieval layer, and every model call goes through one gateway that tracks cost.

## Roadmap at a glance

The MVP ends at Phase 2; each later stage passes a measurable gate.

| Stage | Phases | Gate to move on |
| --- | --- | --- |
| **MVP** | 0 Clean foundation · 1 Fact-check MVP · 2 Eval harness | Baseline score recorded and running in CI |
| **Accuracy** | 3 Hybrid retrieval · 4 Self-correction | Beats the baseline on the eval |
| **Editorial desk** | 5 Orchestration · 6 MCP server | Survives a crash and resumes |
| **Ship and explain** | 7 Production · 8 Write-up | Public demo and results page |

## Phases in detail

Each phase ends with a working demo and a number. Phases 0 to 2 are the true MVP; everything after hardens it. Each phase starts with its own design discussion (see "Open questions").

### Phase 0: Clean foundation

- **Goal:** a codebase we can build on with confidence.
- **Scope:** remove the duplicate LLM service; update model names; structured output via tool use with Pydantic models; add retries, timeouts and token counting in the LLM layer; pytest unit tests with a fake LLM; ruff + GitHub Actions running tests; README; first ADR ("why fact-checking is the core").
- **Out of scope:** any new feature.
- **Done when:** CI is green on every push, and the existing grammar and style review still works.

### Phase 1: Fact-check MVP

- **Goal:** the smallest version that checks facts end to end.
- **Scope:** load SciFact abstracts as the corpus; BM25 keyword search only; a claim extractor (draft to a list of atomic claims); a verifier that reads the top passages and returns *supported*, *contradicted* or *can't tell* with a quoted passage; a `POST /fact-check` endpoint; the frontend highlights each claim in colour and shows its evidence on click.
- **Out of scope:** vector search, retries, orchestration, the queue.
- **Done when:** you paste a paragraph and see coloured claims with real citations.

### Phase 2: Evaluation harness

- **Goal:** know how good it is, and catch it getting worse.
- **Scope:** an eval runner over the SciFact dev set; metrics for verdict accuracy, evidence recall@k, citation correctness (the quote exists and is the gold passage) and abstention rate; a small hand-labelled set of real-style articles; LLM-as-a-judge for claim extraction quality; per-step traces (extracted claims, retrieved passages, verdict) to evaluate the trajectory, not just the answer; a CI job on a small, fixed subset that fails on a regression; a results table in the README.
- **Done when:** every pull request shows the score change, and a baseline is recorded.

### Phase 3: Hybrid retrieval and reranking

- **Goal:** find the right evidence more often. Most fact-check failures start here.
- **Scope:** an embedding model and a vector store (Qdrant); BM25 + vector search combined with reciprocal rank fusion; a cross-encoder reranker; metadata filters (source, date); an ablation table comparing BM25, vector, hybrid and hybrid + rerank on recall and latency.
- **Done when:** evidence recall improves over the Phase 1 baseline, with the numbers and the latency cost written down.

### Phase 4: Self-correcting verification

- **Goal:** fewer wrong verdicts, and honest abstention.
- **Scope:** query rewriting and a second retrieval round when evidence is weak; a context assembler that fits the best passages into a token budget; a confidence score with a tuned threshold for "can't tell"; a citation guard that rejects any quote not found word for word in the source; a check that flags verdicts the evidence doesn't support.
- **Done when:** the eval shows the trade-off curve (accuracy vs. abstention rate) and the chosen operating point.

### Phase 5: Editorial desk orchestration

- **Goal:** turn the fact-checker into the full editorial desk.
- **Scope:** a LangGraph workflow with typed state; grammar (existing), style-guide (RAG over the house style guide) and duplicate-topic agents running in parallel; an editor-in-chief step that proposes approve / revise / escalate; checkpointing to Postgres so runs resume after a crash; retries per step; a pause for the human editor to accept or override each finding, then resume.
- **Done when:** you can kill the server mid-review, restart it, and the run continues; nothing is approved without the editor.

### Phase 6: MCP server

- **Goal:** use EditoralFlow from Claude, Cursor or any AI writing tool.
- **Scope:** tools `check_claims`, `search_sources` and `review_article`; a JSON-RPC implementation with Pydantic validation; read-only vs. write permissions; a short demo of Claude fact-checking a draft.
- **Done when:** an MCP client can call the tools and get cited verdicts back.

### Phase 7: Production hardening

- **Goal:** behave like a real service.
- **Scope:** a job queue with workers and job states (pending, running, needs human, done, failed); a dashboard with history, status, cost and time per article; observability (tokens, latency and cost per agent); model routing (a cheap model for grammar, a strong model for verification) and caching of repeated retrievals; security basics: treat uploaded documents as untrusted (prompt-injection defences), mask PII in logs, keep an audit log of editor decisions; a lean deployment (e.g. Vercel + Render/Fly + managed Postgres + Qdrant Cloud).
- **Done when:** a public demo URL works, and the dashboard shows cost per article.

### Phase 8: Write-up

- **Goal:** make all of it readable in 10 minutes.
- **Scope:** an architecture doc with diagrams; the ADRs collected; a results page with benchmarks, ablations, cost per article and honest failure cases; a 3-minute demo video.
- **Done when:** someone who never saw the project understands what it does, how well it works and why it's built this way.

## Coverage of the 12 concepts

Nine of the twelve are covered naturally, including all Tier 1 and Tier 2 concepts (see [concept-priorities.md](concept-priorities.md)). The remaining three are deferred on purpose.

| Concept | Tier | Phase | How it shows up |
| --- | --- | --- | --- |
| #4 Self-correcting agentic RAG | 1 | 1, 4 | Query rewriting, multi-step retrieval, citation guard, abstention |
| #2 Hybrid retrieval + reranking | 1 | 3 | BM25 + vector + fusion + cross-encoder, with ablations |
| #9 Agent evaluation pipeline | 1 | 2 | Step-level traces, golden set, LLM-as-a-judge, CI regression gate |
| #5 Durable state + human approval | 2 | 5 | Checkpoints, resume after crash, retries, editor approval |
| #6 Custom MCP server | 2 | 6 | JSON-RPC, Pydantic validation, permissions |
| #12 Architecture write-up + ADRs | 2 | 0–8 | ADRs written as we go, final write-up in Phase 8 |
| #11 Semantic cache + model routing | 3 | 7 | Cheap vs. strong model per agent, retrieval caching, cost tracking |
| #10 Security gateway | 3 | 7 | Untrusted-document handling, PII masking, audit log |
| #1 Context assembler | 3 | 4 | Token-budgeted evidence packing for the verifier |
| #8 Typed multi-agent system | 4 | 5 (partly) | Typed state and a supervisor; no consensus voting |
| #7 Three-layer memory | 4 | Deferred | See below |
| #3 GraphRAG | 4 | Deferred | See below |

## Deliberately deferred

- **Affiliate / monetization agent** (`Expert.docx` Phase 8): low AI signal; unrelated to the core story.
- **AWS migration** (`Expert.docx` Phase 10): only after the lean deployment works; a good later ADR ("Bedrock vs. direct API").
- **Live web search:** harder to control and evaluate; add later as a clearly labelled fallback source.
- **Three-layer memory:** a later feature could remember each editor's overrides to reduce repeat flags. Only once there's a way to measure it.
- **GraphRAG:** only if multi-hop claims (e.g. HoVer) prove to be a real weakness, and only if it beats hybrid retrieval on the eval.

## Open questions

These are answered during the design discussion of the phase where they matter, and each answer is recorded as an ADR.

| Question | Decided in |
| --- | --- |
| Domain: start with science/health (SciFact), or another domain? | Phase 1 |
| Claim granularity: one claim per sentence, or atomic facts? | Phase 1 |
| Verdict labels: three labels, or add "partly supported"? | Phase 1 |
| LLM choice for extraction vs. verification, and monthly API budget | Phase 0–1 |
| Embeddings and reranker: hosted API or local open model? | Phase 3 |
| Orchestration: LangGraph, or a hand-written state machine? | Phase 5 |
| Which public style guide to use for the demo? | Phase 5 |
| Time budget per week and target date for the MVP (Phases 0–2) | Phase 0 |
