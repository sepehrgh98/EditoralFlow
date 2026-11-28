---
title: Phase 1.5 design - LangSmith tracing
summary: Start with opt-in LangSmith traces for the Review workflow, then build on them to evaluate fact-check quality.
status: done
updated: 2026-11-27
---

# Phase 1.5 · LangSmith tracing

## Goal

Inspect a Review run from claim extraction through evidence retrieval and verification. Use that visibility to diagnose errors when the evaluation harness measures fact-check quality.

## Tracing design

- Start on `phase-1.5` from `main` after the Phase 1 pull request merges.
- Enable LangSmith only through backend process configuration. A Review run should show grammar, style and the fact-check subgraph together when `REVIEW_INCLUDE_FACT_CHECK=true`.
- Hide raw graph inputs and outputs from the first hosted trace. Send only approved metadata in custom spans. Use a public SciFact draft for live verification. Keep LangSmith credentials in the process environment.
- Record claim IDs, BM25 document IDs and scores, model names, timing, verdict labels and citation IDs. Preserve claim IDs across the retrieval and verification steps so an engineer can connect them.
- Keep the HTTP response and frontend behavior unchanged. Live progress in the browser is outside this plan.

## Tracing commit plan

| # | Commit | Verification | Status |
| --- | --- | --- | --- |
| 1 | Enable opt-in LangSmith graph tracing, name the Review run and document local configuration | Submit a public SciFact draft through Review and confirm that grammar, style and fact-check share one trace with raw inputs and outputs hidden | done |
| 2 | Trace BM25 retrieval and custom model calls with selected metadata | Follow one claim from retrieved document IDs and scores through model timing to the verdict and citation IDs. Verify that raw draft text and prompts are absent | done |
| 3 | Document the debugging workflow and record the live result | Run `make check` with tracing disabled, then run a public SciFact review with tracing enabled and document how to distinguish a retrieval miss from a verifier error | done |

Commit 1 verification used a public SciFact claim with live Ollama and a loopback collector for the LangSmith SDK. The payloads contained one named Review trace with grammar, style, fact-check, extraction, retrieval and verification. All run inputs and outputs were empty, and the draft text was absent.

Commit 2 verification followed claim `c1` through three ranked SciFact results, the Ollama model call, a supported verdict and two citation IDs. The local collector confirmed that draft text and prompts were absent. A separate failed model call confirmed that the exported error was redacted. `make check` passed all 165 tests with tracing off.

## Outcome

The [debugging walkthrough](../../README.md#diagnose-a-verdict) uses SciFact development claim 130. For commit 3, a fresh live Ollama run sent a masked trace to the local collector and returned Supported with document `27768226` ranked first. All 165 tests passed with tracing explicitly disabled. The hosted run in `editoralflow-local` confirmed one Review trace with grammar, style, fact-check and nested search, model and verification spans. Claim `c1` ranked document `27768226` first and returned Supported with three citation IDs. All recorded graph inputs and outputs were empty.

The evaluation runner, baseline metrics, labelled articles and CI gate remain in [the Phase 2 roadmap](../product/roadmap.md). Their implementation plan is pending design.
