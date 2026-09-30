import { useState } from "react";

import { generateExecutiveInsights } from "../api/marketlens";
import AiLabel from "./AiLabel";

function InsightList({ title, items }) {
  return (
    <div>
      <h4 className="text-sm font-bold text-slate-900">{title}</h4>
      <ul className="mt-2 space-y-2 text-sm leading-6 text-slate-600">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ExecutiveCopilot() {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generate = async () => {
    setLoading(true);
    setError("");
    try {
      setInsights(await generateExecutiveInsights());
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel mt-6 overflow-hidden">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-100 p-5 sm:flex-row sm:items-center sm:p-6">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <p className="eyebrow">Management briefing</p>
            <AiLabel />
          </div>
          <h2 className="mt-1 text-xl font-bold text-slate-950">
            MarketLens Executive Copilot
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Generate a grounded interpretation of the current top-five ranking.
          </p>
        </div>
        <button
          onClick={generate}
          disabled={loading}
          className="focus-ring shrink-0 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-wait disabled:bg-slate-300"
        >
          {loading ? "Generating insights…" : "Generate Executive Insights"}
        </button>
      </div>

      {error && (
        <div className="border-b border-red-100 bg-red-50 px-6 py-4 text-sm text-red-700">
          {error} The calculated dashboard remains available.
        </div>
      )}

      {!insights && !error && (
        <div className="px-6 py-8 text-sm text-slate-500">
          Insights are generated only when requested, so no Gemini call is made on page load.
        </div>
      )}

      {insights && (
        <div className="p-5 sm:p-6">
          <div className="rounded-xl border border-brand-100 bg-brand-50/60 p-5">
            <p className="text-xs font-bold uppercase tracking-wide text-brand-700">Executive Summary</p>
            <p className="mt-2 text-sm leading-6 text-slate-700">{insights.executive_summary}</p>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Key Findings</h3>
              <div className="mt-3 space-y-3">
                {insights.key_findings.map((finding) => (
                  <div key={finding.title} className="rounded-xl border border-slate-200 p-4">
                    <p className="text-sm font-bold text-slate-900">{finding.title}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600">{finding.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-5 rounded-xl bg-slate-50 p-5">
              <InsightList title="Opportunities for further evaluation" items={insights.opportunities} />
              <InsightList title="Risks & caveats" items={insights.risks_and_caveats} />
              <InsightList title="Recommended next steps" items={insights.recommended_next_steps} />
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
