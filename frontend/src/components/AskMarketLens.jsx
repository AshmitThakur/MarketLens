import { useState } from "react";

import { askMarketLens } from "../api/marketlens";
import AiLabel from "./AiLabel";

const suggestions = [
  "Why does this city rank where it does?",
  "What are this city's strongest indicators?",
  "What weaknesses should management consider?"
];

export default function AskMarketLens({ city }) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event) => {
    event?.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    setLoading(true);
    setError("");
    try {
      setResponse(await askMarketLens(`${trimmed} Focus on ${city}.`));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel mt-6 p-5 sm:p-6">
      <div className="flex flex-wrap items-center gap-3">
        <p className="eyebrow">City analysis</p>
        <AiLabel />
      </div>
      <h2 className="mt-1 text-xl font-bold text-slate-950">Ask MarketLens</h2>
      <p className="mt-1 text-sm text-slate-500">
        Ask one grounded question about {city} and the current MarketLens metrics.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => setQuestion(suggestion)}
            className="focus-ring rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700"
          >
            {suggestion}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="mt-4 flex flex-col gap-3 sm:flex-row">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          maxLength={1000}
          placeholder={`Ask about ${city}…`}
          className="focus-ring min-w-0 flex-1 rounded-xl border border-slate-200 px-4 py-2.5 text-sm placeholder:text-slate-400"
        />
        <button
          type="submit"
          disabled={!question.trim() || loading}
          className="focus-ring rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {loading ? "Analyzing…" : "Ask MarketLens"}
        </button>
      </form>

      {error && <p className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}

      {response && (
        <div className="mt-5 border-t border-slate-100 pt-5">
          <p className="text-sm leading-6 text-slate-700">{response.answer}</p>
          {response.supporting_points.length > 0 && (
            <ul className="mt-4 space-y-2">
              {response.supporting_points.map((point) => (
                <li key={point} className="flex gap-2 text-sm text-slate-600">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                  {point}
                </li>
              ))}
            </ul>
          )}
          {response.caveat && (
            <p className="mt-4 rounded-lg bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800">
              <span className="font-bold">Caveat:</span> {response.caveat}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
