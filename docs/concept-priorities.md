# AI Portfolio Concept Priorities

_Last updated: 2026-11-27_

Build one deep product around Tier 1 plus two or three Tier 2 concepts, not 12 separate projects. Each of the 12 AI engineering concepts is ranked on:

- **Hiring signal:** how often hiring managers ask about it.
- **Rarity:** how few portfolios show it.
- **Effort:** how much work it takes to build it well and to prove it works with a number.

## Tier 1: the core to build

| Rank | Concept | Why it matters |
| --- | --- | --- |
| 1 | #4 Self-correcting agentic RAG | Citation grounding, abstention and hallucination detection are what companies are struggling with right now. The strongest single signal. |
| 2 | #2 Hybrid retrieval + reranking | The foundation under #4. Comes up in almost every RAG interview and is easy to measure. |
| 3 | #9 Agent evaluation pipeline | Rare in portfolios. Answers "how do you know it works?" and makes every other part credible. |

## Tier 2: high-value add-ons

| Rank | Concept | Why it matters |
| --- | --- | --- |
| 4 | #5 Durable state + human approval | Shows production thinking. Moderate effort with LangGraph checkpointing. |
| 5 | #6 Custom MCP server | Hot, small scope, quick win. Building it without an SDK is a good talking point. |
| 6 | #12 Architecture write-up + ADRs | Cheap, and multiplies the value of everything else. |

## Tier 3: add if time allows

| Rank | Concept | Why it matters |
| --- | --- | --- |
| 7 | #11 Semantic cache + model routing | Cost awareness impresses. A simple router takes about a weekend. |
| 8 | #10 Security gateway | Prompt-injection defence is asked about more and more. A basic version is enough. |
| 9 | #1 Context assembler | Real, but comes naturally as part of #4. Not worth a standalone project. |

## Tier 4: don't lead with these

All three are hard to evaluate cheaply, so they cost a lot and pay back little in a portfolio.

| Rank | Concept | Why not lead with it | When it's worth it |
| --- | --- | --- | --- |
| 10 | #7 Three-layer memory | Value only shows across many sessions with real users; no clear metric; importance scoring has no accepted right answer. | The product is naturally multi-session, e.g. learning an editor's style over time. |
| 11 | #3 GraphRAG | Slow, expensive indexing; extraction errors pile up; on most data, hybrid retrieval with reranking matches or beats it. | The data really is a network, and an eval shows it beating the hybrid baseline. |
| 12 | #8 Multi-agent consensus voting | Same-model agents share blind spots, so voting mostly costs 3x for a small gain. | You measure that a verifier agent cuts errors on your eval set. |

## Rule of thumb

Tier 1 plus two or three Tier 2 items makes a strong portfolio. What gets you hired is a clear number, such as "citation accuracy went from 71% to 89%".
