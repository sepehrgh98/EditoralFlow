---
title: Concept priorities
summary: Ranking of 12 AI engineering concepts and how the roadmap covers them.
status: agreed
updated: 2026-11-27
---

# Concept priorities

The project goal is one deep product built around Tier 1 plus two or three Tier 2 concepts, not 12 separate projects. Concepts are ranked on hiring signal, rarity in portfolios, and effort to build and prove with a number.

## Ranking

| Rank | Concept | Tier | Why |
| --- | --- | --- | --- |
| 1 | #4 Self-correcting agentic RAG | 1 | Citation grounding, abstention, hallucination detection: the strongest signal |
| 2 | #2 Hybrid retrieval + reranking | 1 | Foundation under #4; easy to measure |
| 3 | #9 Agent evaluation pipeline | 1 | Rare in portfolios; makes everything else credible |
| 4 | #5 Durable state + human approval | 2 | Production thinking |
| 5 | #6 Custom MCP server | 2 | Hot, small scope, quick win |
| 6 | #12 Architecture write-up + ADRs | 2 | Cheap; multiplies the value of everything else |
| 7 | #11 Semantic cache + model routing | 3 | Cost awareness |
| 8 | #10 Security gateway | 3 | Prompt-injection defence is asked about more and more |
| 9 | #1 Context assembler | 3 | Comes naturally as part of #4 |
| 10 | #7 Three-layer memory | 4 | Hard to measure; easy to over-engineer |
| 11 | #3 GraphRAG | 4 | Expensive; often no better than hybrid retrieval |
| 12 | #8 Multi-agent consensus voting | 4 | Same-model agents share blind spots; mostly costs more |

Tier 4 items can come in later if the product calls for them and an eval shows they help.

## Coverage in the roadmap

| Concept | Phase | How it shows up |
| --- | --- | --- |
| #4 Self-correcting agentic RAG | 1, 4 | Query rewriting, multi-step retrieval, citation guard, abstention |
| #2 Hybrid retrieval + reranking | 3 | BM25 + vector + fusion + cross-encoder, with ablations |
| #9 Agent evaluation pipeline | 2 | Step-level traces, golden set, LLM-as-a-judge, CI regression gate |
| #5 Durable state + human approval | 5 | Checkpoints, resume after crash, retries, editor approval |
| #6 Custom MCP server | 6 | JSON-RPC, Pydantic validation, permissions |
| #12 Architecture write-up + ADRs | 0–8 | ADRs as we go, final write-up in Phase 8 |
| #11 Semantic cache + model routing | 7 | Cheap vs. strong model per agent, caching, cost tracking |
| #10 Security gateway | 7 | Untrusted-document handling, PII masking, audit log |
| #1 Context assembler | 4 | Token-budgeted evidence packing |
| #8 Typed multi-agent system | 5 (partly) | Typed state and a supervisor; no consensus voting |
| #7 Three-layer memory | Deferred | |
| #3 GraphRAG | Deferred | |
