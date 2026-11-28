---
title: Documentation map
summary: Start here. Index of all EditoralFlow documentation for humans and AI agents, plus the rules for keeping it current.
status: current
updated: 2026-11-27
---

# Documentation map

Start here. Every documentation file is listed below with what it answers. Files are Markdown with a short YAML header (`title`, `summary`, `status`, `updated`) so both people and agents can scan them.

## Where things are

| File | Answers | Status |
| --- | --- | --- |
| [product/vision.md](product/vision.md) | What is EditoralFlow, who is it for, what are the principles? | agreed |
| [product/roadmap.md](product/roadmap.md) | What gets built in which phase, and when is a phase done? | agreed |
| [product/concept-priorities.md](product/concept-priorities.md) | Which AI engineering concepts matter, and where does each appear? | agreed |
| [architecture/target-architecture.md](architecture/target-architecture.md) | What will the finished system look like, and with which stack? | agreed |
| [architecture/current-state.md](architecture/current-state.md) | What does the code do now, including the combined Review workflow? | current |
| [decisions/](decisions/) | Why was each significant choice made? (ADRs, numbered) | ongoing |
| [phases/](phases/) | Detailed design and outcome of each phase | ongoing |

### Decisions

| ADR | Title | Status |
| --- | --- | --- |
| [0001](decisions/0001-fact-checking-as-core.md) | Fact-checking is the core of EditoralFlow | accepted |
| [0002](decisions/0002-tech-stack.md) | Tech stack | accepted |
| [0003](decisions/0003-langgraph-from-phase-0.md) | LangGraph from Phase 0 | accepted |
| [0004](decisions/0004-async-llm-calls.md) | Async LLM calls | accepted |
| [0005](decisions/0005-json-outputs-for-structured-answers.md) | JSON outputs for structured answers | accepted |
| [0006](decisions/0006-local-models-with-ollama.md) | Local models with Ollama for development | accepted |
| [0007](decisions/0007-claims-and-labels.md) | Claims and labels | accepted |
| [0008](decisions/0008-citations-by-sentence-number.md) | Citations by sentence number | accepted |
| [0009](decisions/0009-bm25-baseline.md) | BM25 baseline | accepted |
| [0010](decisions/0010-fact-check-subgraph.md) | Fact-check as a subgraph | accepted |
| [0011](decisions/0011-opt-in-langsmith-tracing.md) | Opt-in LangSmith tracing | accepted |

### Phases

| Phase | Design | Status |
| --- | --- | --- |
| 0 Clean foundation | [phase-0-foundation.md](phases/phase-0-foundation.md) | done |
| 1 Fact-check MVP | [phase-1-fact-check-mvp.md](phases/phase-1-fact-check-mvp.md) | done |
| 1.5 LangSmith tracing | [phase-1.5-langsmith-tracing.md](phases/phase-1.5-langsmith-tracing.md) | agreed, in progress (2 of 3 commits) |

## Status values

`agreed` (decided, change only by a new decision) · `done` (phase complete) · `current` (describes the code as it is now) · `accepted` / `proposed` / `superseded` (ADRs) · `ongoing` (folder that grows) · `template` / `guide`.

## Rules for keeping documentation current

1. **Documentation is part of done.** A feature, fix or phase is not complete until the relevant files here are updated in the same pull request.
2. **After every feature:** update `architecture/current-state.md` and any file whose content is now wrong.
3. **Before every phase:** write `phases/phase-N-<name>.md` and get it agreed before coding.
4. **After every phase:** fill in the phase file's *Outcome* section and update the roadmap status.
5. **Every significant decision** gets a new ADR from `decisions/_template.md`, numbered in order. Never edit an accepted ADR's decision; supersede it with a new one.
6. **Keep this map in sync:** any new, renamed or removed file is reflected in the tables above.
7. **Update the `updated` date** in a file's header whenever its content changes.
8. **One topic per file**, short sections, tables for comparisons, Mermaid for diagrams.
