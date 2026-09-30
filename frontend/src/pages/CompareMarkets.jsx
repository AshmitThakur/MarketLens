import { useCallback, useEffect, useMemo, useState } from "react";

import { compareCities, getCities } from "../api/marketlens";
import AiLabel from "../components/AiLabel";
import { ErrorState, LoadingState } from "../components/AsyncState";
import PageHeader from "../components/PageHeader";
import { formatScore } from "../utils/formatters";

const scoreFields = [
  ["Sales", "sales_score"],
  ["Transactions", "transaction_score"],
  ["Growth", "growth_score"],
  ["Breadth", "breadth_score"]
];

function StrengthList({ title, items }) {
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <h3 className="text-sm font-bold text-slate-900">{title}</h3>
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-sm leading-6 text-slate-600">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function CompareMarkets() {
  const [cities, setCities] = useState([]);
  const [cityA, setCityA] = useState("");
  const [cityB, setCityB] = useState("");
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const loadCities = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await getCities();
      setCities(result);
      setCityA(result[0]?.city || "");
      setCityB(result.find((city) => city.city === "Cuenca")?.city || result[1]?.city || "");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCities();
  }, [loadCities]);

  const selectedA = useMemo(
    () => cities.find((city) => city.city === cityA),
    [cities, cityA]
  );
  const selectedB = useMemo(
    () => cities.find((city) => city.city === cityB),
    [cities, cityB]
  );

  const compare = async () => {
    if (!cityA || !cityB || cityA === cityB) return;
    setSubmitting(true);
    setError("");
    try {
      setComparison(await compareCities(cityA, cityB));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingState message="Loading markets…" />;

  return (
    <>
      <PageHeader
        eyebrow="Side-by-side analysis"
        title="Compare Markets"
        description="Review calculated component scores first, then request a grounded management interpretation of the trade-offs."
        action={<AiLabel />}
      />

      <section className="panel p-5 sm:p-6">
        <div className="grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          {[
            ["City A", cityA, setCityA],
            ["City B", cityB, setCityB]
          ].map(([label, value, setter]) => (
            <label key={label}>
              <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>
              <select
                value={value}
                onChange={(event) => {
                  setter(event.target.value);
                  setComparison(null);
                }}
                className="focus-ring w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm"
              >
                {cities.map((city) => (
                  <option key={`${label}-${city.city}`} value={city.city}>{city.city}, {city.state}</option>
                ))}
              </select>
            </label>
          ))}
          <button
            onClick={compare}
            disabled={!cityA || !cityB || cityA === cityB || submitting}
            className="focus-ring rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {submitting ? "Comparing…" : "Compare with MarketLens"}
          </button>
        </div>
        {cityA === cityB && (
          <p className="mt-3 text-sm text-amber-700">Select two different cities.</p>
        )}
      </section>

      {error && <div className="mt-6"><ErrorState message={error} /></div>}

      {selectedA && selectedB && (
        <section className="panel mt-6 p-5 sm:p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow">Calculated metrics</p>
              <h2 className="mt-1 text-xl font-bold text-slate-950">Component Score Comparison</h2>
            </div>
            <div className="hidden gap-5 text-sm sm:flex">
              <span className="font-semibold text-brand-700">● {selectedA.city}</span>
              <span className="font-semibold text-slate-500">● {selectedB.city}</span>
            </div>
          </div>

          <div className="mt-6 space-y-5">
            {scoreFields.map(([label, field]) => (
              <div key={field} className="grid gap-3 sm:grid-cols-[120px_minmax(0,1fr)_minmax(0,1fr)] sm:items-center">
                <p className="text-sm font-semibold text-slate-600">{label}</p>
                <div className="flex min-w-0 items-center gap-3">
                  <div className="h-2 min-w-0 flex-1 rounded-full bg-slate-100"><div className="h-full rounded-full bg-brand-500" style={{ width: `${selectedA[field]}%` }} /></div>
                  <p className="w-14 text-right text-sm font-bold text-brand-700">{formatScore(selectedA[field])}</p>
                </div>
                <div className="flex min-w-0 items-center gap-3">
                  <div className="h-2 min-w-0 flex-1 rounded-full bg-slate-100"><div className="h-full rounded-full bg-slate-400" style={{ width: `${selectedB[field]}%` }} /></div>
                  <p className="w-14 text-right text-sm font-bold text-slate-700">{formatScore(selectedB[field])}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 grid gap-4 border-t border-slate-100 pt-5 sm:grid-cols-2">
            {[selectedA, selectedB].map((city) => (
              <div key={city.city} className="rounded-xl bg-slate-50 p-4">
                <p className="font-bold text-slate-950">{city.city}</p>
                <p className="text-sm text-slate-500">Opportunity score {formatScore(city.opportunity_score)} / 100</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {comparison && (
        <section className="panel mt-6 p-5 sm:p-6">
          <div className="flex flex-wrap items-center gap-3">
            <p className="eyebrow">Management interpretation</p>
            <AiLabel />
          </div>
          <h2 className="mt-2 text-xl font-bold text-slate-950">{comparison.city_a} vs {comparison.city_b}</h2>
          <p className="mt-3 text-sm leading-6 text-slate-700">{comparison.summary}</p>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <StrengthList title={`${comparison.city_a} relative strengths`} items={comparison.advantages_city_a} />
            <StrengthList title={`${comparison.city_b} relative strengths`} items={comparison.advantages_city_b} />
          </div>
          <div className="mt-4 rounded-xl bg-slate-50 p-5">
            <StrengthList title="Main trade-offs" items={comparison.main_tradeoffs} />
            <p className="mt-5 border-t border-slate-200 pt-4 text-sm leading-6 text-slate-700">
              <span className="font-bold text-slate-900">Management interpretation: </span>
              {comparison.management_interpretation}
            </p>
          </div>
        </section>
      )}
    </>
  );
}
