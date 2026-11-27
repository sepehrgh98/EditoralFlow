import { useRef, useState } from "react";

const verdicts = {
  supported: { label: "Supported", color: "bg-emerald-400/20 text-emerald-200" },
  contradicted: { label: "Contradicted", color: "bg-rose-400/20 text-rose-200" },
  not_enough_info: { label: "Can’t tell", color: "bg-zinc-500/25 text-zinc-200" },
} as const;

type VerdictLabel = keyof typeof verdicts;

type ClaimResult = {
  claim: { id: string; text: string; source_sentence: string };
  verdict: {
    label: VerdictLabel;
    explanation: string;
    citations: { doc_id: string; title: string; sentence_index: number; text: string }[];
  };
};

export type FactCheckResult = {
  results: ClaimResult[];
  counts: Record<VerdictLabel, number>;
};

function matchDraft(article: string, results: ClaimResult[]) {
  const ranges: { start: number; end: number; result: ClaimResult }[] = [];
  const unmatched: ClaimResult[] = [];
  for (const result of results) {
    const sentence = result.claim.source_sentence;
    let start = sentence ? article.indexOf(sentence) : -1;
    if (start === -1) {
      unmatched.push(result);
    }
    while (start !== -1) {
      ranges.push({ start, end: start + sentence.length, result });
      start = article.indexOf(sentence, start + sentence.length);
    }
  }

  const boundaries = [...new Set([0, article.length, ...ranges.flatMap(({ start, end }) => [start, end])])]
    .sort((a, b) => a - b);

  return {
    unmatched,
    segments: boundaries.slice(0, -1).map((start, index) => ({
      start,
      text: article.slice(start, boundaries[index + 1]),
      claims: ranges.filter((range) => range.start <= start && start < range.end)
        .map(({ result }) => result),
    })),
  };
}

export function FactCheckResults({
  article,
  result,
  onEdit,
}: {
  article: string;
  result: FactCheckResult;
  onEdit: () => void;
}) {
  const [selection, setSelection] = useState<{
    claims: ClaimResult[];
    active: ClaimResult;
  } | null>(null);
  const evidenceHeading = useRef<HTMLHeadingElement>(null);
  const { unmatched, segments } = matchDraft(article, result.results);

  function openEvidence(claims: ClaimResult[]) {
    setSelection({ claims, active: claims[0] });
    evidenceHeading.current?.focus();
  }

  return (
    <>
      <section className="min-h-[560px] rounded-lg border border-white/10 bg-[#171a1f]">
        <div className="flex items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
          <h2 className="font-semibold text-white">Checked draft</h2>
          <button
            type="button"
            onClick={onEdit}
            className="rounded-md border border-white/15 px-4 py-2 text-sm hover:bg-white/10"
          >
            Edit draft
          </button>
        </div>
        <p className="whitespace-pre-wrap break-words px-5 py-5 leading-8">
          {segments.map(({ start, text, claims }) => {
            const labels = [...new Set(claims.map(({ verdict }) => verdict.label))];
            if (labels.length === 0) {
              return <span key={start}>{text}</span>;
            }
            const color = labels.length === 1
              ? verdicts[labels[0]].color
              : "bg-sky-400/20 text-sky-100";
            return (
              <button
                key={start}
                type="button"
                aria-label={`${text} — ${labels.map((label) => verdicts[label].label).join(", ")}`}
                aria-controls="claim-evidence"
                aria-pressed={claims.some((claim) => claim === selection?.active)}
                onClick={() => openEvidence(claims)}
                className={`inline whitespace-pre-wrap rounded text-left underline decoration-dotted underline-offset-4 hover:decoration-solid ${color}`}
              >
                {text}
              </button>
            );
          })}
        </p>
        {unmatched.length > 0 && (
          <section className="border-t border-white/10 px-5 py-4">
            <h3 className="text-sm font-semibold text-white">Claims without a matching draft sentence</h3>
            <ul className="mt-2 space-y-2">
              {unmatched.map((claim) => (
                <li key={claim.claim.id}>
                  <button
                    type="button"
                    aria-controls="claim-evidence"
                    aria-pressed={selection?.active === claim}
                    onClick={() => openEvidence([claim])}
                    className={`rounded px-2 py-1 text-left text-sm underline decoration-dotted ${verdicts[claim.verdict.label].color}`}
                  >
                    {claim.claim.text} · {verdicts[claim.verdict.label].label}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </section>

      <aside className="space-y-4">
        <section className="rounded-lg border border-white/10 bg-[#171a1f] p-5">
          <h2 className="text-lg font-semibold text-white">Fact-check summary</h2>
          <ul className="mt-3 flex flex-wrap gap-2 text-sm">
            {(Object.keys(verdicts) as VerdictLabel[]).map((label) => (
              <li key={label} className={`rounded px-2 py-1 ${verdicts[label].color}`}>
                {result.counts[label]} {verdicts[label].label}
              </li>
            ))}
          </ul>
        </section>

        <section id="claim-evidence" className="rounded-lg border border-white/10 bg-[#171a1f] p-5">
          <h2 ref={evidenceHeading} tabIndex={-1} className="text-lg font-semibold text-white">
            Claim evidence
          </h2>
          {selection && selection.claims.length > 1 && (
            <ul className="mt-3 space-y-1">
              {selection.claims.map((claim) => (
                <li key={claim.claim.id}>
                  <button
                    type="button"
                    aria-pressed={selection.active === claim}
                    onClick={() => setSelection({ ...selection, active: claim })}
                    className="w-full rounded px-2 py-1 text-left text-sm hover:bg-white/10 aria-pressed:bg-white/10"
                  >
                    {claim.claim.text} · {verdicts[claim.verdict.label].label}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <div aria-live="polite">
            {selection ? (
              <ClaimEvidence result={selection.active} />
            ) : (
              <p className="mt-3 text-sm text-zinc-400">
                {result.results.length === 0
                  ? "No factual claims were found in this draft."
                  : "Select a highlighted sentence or a claim to see its verdict and evidence."}
              </p>
            )}
          </div>
        </section>
      </aside>
    </>
  );
}

function ClaimEvidence({ result }: { result: ClaimResult }) {
  const { claim, verdict } = result;
  const badge = verdicts[verdict.label];
  return (
    <div className="mt-4 space-y-3">
      <span className={`rounded px-2 py-1 text-sm font-medium ${badge.color}`}>{badge.label}</span>
      <h3 className="font-semibold text-white">{claim.text}</h3>
      <p className="text-sm leading-6 text-zinc-300">{verdict.explanation}</p>
      {verdict.citations.map((citation) => (
        <figure
          key={`${citation.doc_id}-${citation.sentence_index}`}
          className="rounded-md border border-white/10 bg-black/15 p-4"
        >
          <blockquote className="text-sm leading-6 text-zinc-100">{citation.text}</blockquote>
          <figcaption className="mt-2 text-sm text-zinc-400">{citation.title}</figcaption>
        </figure>
      ))}
    </div>
  );
}
