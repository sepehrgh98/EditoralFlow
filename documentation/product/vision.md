---
title: Product vision
summary: What EditoralFlow is, the problem it solves, who it is for, and the design principles.
status: agreed
updated: 2026-11-27
---

# Product vision

## The product

EditoralFlow is an AI editorial desk. It reviews a draft for quality and fit with house rules, checks every factual statement against the customer's trusted sources, and lets an editor approve it with the evidence in hand.

- **Problem:** teams publish more text than ever, much of it AI-written, and can't afford to check every fact by hand. Wrong or invented facts get published.
- **Solution:** for each claim, the system shows the source passage that backs it up or contradicts it, or honestly says "can't tell". A human makes the final call.
- **Who it's for:** editors at content agencies, publishers and in-house content teams. For now it is a skills and portfolio project; a commercial version would swap in a customer's corpus.
- **Approach:** start with the smallest useful version and harden it one layer at a time. Each phase ends with something that runs and a number that proves it.

## What the user sees (target)

1. **Workspace setup:** upload trusted sources and a style guide (demo: preloaded with SciFact).
2. **Submit a draft:** paste or upload an article; it is queued and each agent's progress is visible.
3. **Review screen:** the article with each factual sentence marked *supported*, *contradicted* or *can't tell*; clicking one shows the exact source passage. Tabs for grammar, style-guide issues and similar past articles.
4. **Editor decision:** accept or override each finding, then approve, send back for revision or escalate. Runs resume after a crash.
5. **Dashboard:** history, status, cost and time per article, share of facts verified.
6. **MCP server:** Claude, Cursor or any AI writing tool can call EditoralFlow.

## Agents

| Agent | Depth | Job |
| --- | --- | --- |
| Fact-check agent | Deep (the core) | Extracts claims, runs hybrid retrieval + reranking, retries with rewritten queries, returns a verdict with a citation or abstains |
| Style-guide agent | Medium | Retrieves relevant house rules and flags breaches with the rule cited |
| Duplicate agent | Light | Finds past articles covering the same topic, with an overlap score |
| Grammar agent | Light | Cheap first pass (exists today) |
| Editor-in-chief (supervisor) | Medium | Combines results, proposes approve / revise / escalate, hands off to the human |

## Design principles

1. **Measure before you improve.** Each feature lands with a metric on the eval set.
2. **Proof or abstain.** Every verdict carries a source quote that exists word for word in the corpus, or it says "can't tell".
3. **Simple first.** Each phase adds one layer. Nothing is built for a need we don't have yet.
4. **One retrieval layer, many agents.** Fact-check, style-guide and duplicate agents share the same search.
5. **Human in charge.** The system proposes; the editor decides. Nothing is approved automatically.
6. **Write decisions down.** Every significant choice gets an ADR in `documentation/decisions/` when it is made.
7. **Swappable parts.** LLM provider, embedding model, vector store and corpus sit behind interfaces.
8. **Documentation is part of done.** A feature is not finished until the documentation reflects it.
