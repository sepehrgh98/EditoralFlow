"use client";

import { useState } from "react";

type Issue = {
  type: string;
  text: string;
  issue: string;
  suggestion: string;
};

type AgentResult = {
  score: number;
  issues: Issue[];
  summary: string;
};

type ReviewResult = {
  grammar_result?: AgentResult;
  style_result?: AgentResult;
};

const agents = [
  {
    key: "grammar_result",
    label: "Grammar",
    accent: "text-sky-300",
    ring: "ring-sky-400/30",
  },
  {
    key: "style_result",
    label: "Style",
    accent: "text-emerald-300",
    ring: "ring-emerald-400/30",
  },
] as const;

export default function Home() {
  const [article, setArticle] = useState("");
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const wordCount = article
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;

  const issueCount = agents.reduce((total, agent) => {
    return total + (result?.[agent.key]?.issues.length ?? 0);
  }, 0);

  const averageScore = result
    ? Math.round(
        agents.reduce((total, agent) => {
          return total + (result[agent.key]?.score ?? 0);
        }, 0) / agents.length
      )
    : null;

  const reviewArticle = async () => {
    if (!article.trim() || loading) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        "http://localhost:8000/review",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            article,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error("Review request failed.");
      }

      setResult(data);
    } catch (error) {
      console.error(error);
      setError("Could not complete the review. Check the backend and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#101215] text-zinc-100">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-8 px-5 py-6 sm:px-8 lg:px-10">
        <header className="flex flex-col gap-4 border-b border-white/10 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-sky-300">
              Editorial desk
            </p>
            <h1 className="mt-2 text-4xl font-semibold tracking-normal text-white sm:text-5xl">
              EditorialFlow
            </h1>
          </div>

          <div className="grid grid-cols-3 gap-3 text-sm">
            <Metric label="Words" value={wordCount} />
            <Metric label="Issues" value={result ? issueCount : "-"} />
            <Metric label="Score" value={averageScore ?? "-"} />
          </div>
        </header>

        <section className="grid flex-1 gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
          <div className="flex min-h-[560px] flex-col rounded-lg border border-white/10 bg-[#171a1f] shadow-2xl shadow-black/20">
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div>
                <h2 className="text-base font-semibold text-white">
                  Article
                </h2>
                <p className="mt-1 text-sm text-zinc-400">
                  {wordCount} words queued
                </p>
              </div>

              <button
                onClick={reviewArticle}
                disabled={!article.trim() || loading}
                className="inline-flex min-h-11 items-center justify-center rounded-md bg-sky-400 px-5 text-sm font-semibold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-400"
              >
                {loading ? "Reviewing" : "Review"}
              </button>
            </div>

            <textarea
              className="min-h-[480px] flex-1 resize-none bg-transparent px-5 py-5 text-base leading-7 text-zinc-100 outline-none placeholder:text-zinc-600"
              placeholder="Paste article here..."
              value={article}
              onChange={(event) => setArticle(event.target.value)}
            />
          </div>

          <aside className="flex min-h-[560px] flex-col gap-4">
            {error && (
              <div className="rounded-lg border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {error}
              </div>
            )}

            {!result && !loading && (
              <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-white/15 bg-[#171a1f] px-8 text-center">
                <div>
                  <div className="mx-auto mb-5 h-2 w-24 rounded-full bg-gradient-to-r from-sky-300 via-emerald-300 to-amber-300" />
                  <h2 className="text-xl font-semibold text-white">
                    Ready for review
                  </h2>
                  <p className="mt-3 max-w-sm text-sm leading-6 text-zinc-400">
                    Results will appear here after the grammar and style agents finish.
                  </p>
                </div>
              </div>
            )}

            {loading && (
              <div className="flex flex-1 items-center justify-center rounded-lg border border-white/10 bg-[#171a1f]">
                <div className="text-center">
                  <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-zinc-700 border-t-sky-300" />
                  <p className="mt-4 text-sm font-medium text-zinc-300">
                    Reviewing article
                  </p>
                </div>
              </div>
            )}

            {result && !loading && (
              <>
                <div className="rounded-lg border border-white/10 bg-[#171a1f] p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <h2 className="text-lg font-semibold text-white">
                        Review summary
                      </h2>
                      <p className="mt-1 text-sm text-zinc-400">
                        {issueCount} total issues found
                      </p>
                    </div>

                    <div className="rounded-md border border-white/10 bg-black/20 px-4 py-3 text-center">
                      <p className="text-2xl font-semibold text-white">
                        {averageScore}
                      </p>
                      <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">
                        Avg score
                      </p>
                    </div>
                  </div>
                </div>

                {agents.map((agent) => {
                  const agentResult = result[agent.key];

                  return (
                    <section
                      key={agent.key}
                      className={`rounded-lg border border-white/10 bg-[#171a1f] p-5 ring-1 ${agent.ring}`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h3 className={`text-lg font-semibold ${agent.accent}`}>
                            {agent.label}
                          </h3>
                          <p className="mt-2 text-sm leading-6 text-zinc-300">
                            {agentResult?.summary || "No summary returned."}
                          </p>
                        </div>

                        <div className="rounded-md bg-black/25 px-3 py-2 text-right">
                          <p className="text-xl font-semibold text-white">
                            {agentResult?.score ?? "-"}
                          </p>
                          <p className="text-xs text-zinc-500">
                            score
                          </p>
                        </div>
                      </div>

                      <div className="mt-5 space-y-3">
                        {(agentResult?.issues.length ?? 0) === 0 && (
                          <p className="rounded-md border border-white/10 bg-black/15 px-3 py-3 text-sm text-zinc-400">
                            No issues reported.
                          </p>
                        )}

                        {agentResult?.issues.map((issue, index) => (
                          <article
                            key={`${agent.key}-${index}`}
                            className="rounded-md border border-white/10 bg-black/15 p-4"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <span className="rounded-sm bg-white/10 px-2 py-1 text-xs font-medium uppercase tracking-[0.12em] text-zinc-300">
                                {issue.type}
                              </span>
                              <span className="text-xs text-zinc-500">
                                #{index + 1}
                              </span>
                            </div>

                            {issue.text && (
                              <p className="mt-3 border-l-2 border-amber-300/70 pl-3 text-sm text-zinc-200">
                                {issue.text}
                              </p>
                            )}

                            <p className="mt-3 text-sm leading-6 text-zinc-300">
                              {issue.issue}
                            </p>

                            {issue.suggestion && (
                              <p className="mt-2 text-sm leading-6 text-emerald-200">
                                {issue.suggestion}
                              </p>
                            )}
                          </article>
                        ))}
                      </div>
                    </section>
                  );
                })}
              </>
            )}
          </aside>
        </section>
      </div>
    </main>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {
  return (
    <div className="min-w-20 rounded-md border border-white/10 bg-white/[0.04] px-4 py-3 text-right">
      <p className="text-lg font-semibold text-white">
        {value}
      </p>
      <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">
        {label}
      </p>
    </div>
  );
}
