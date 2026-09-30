import { useCallback, useEffect, useMemo, useState } from "react";

import { getCities, recalculateScores } from "../api/marketlens";
import { ErrorState, LoadingState } from "../components/AsyncState";
import CityTable from "../components/CityTable";
import OpportunityChart from "../components/OpportunityChart";
import PageHeader from "../components/PageHeader";
import WeightControls from "../components/WeightControls";

const DEFAULT_WEIGHTS = {
  sales_weight: 40,
  transaction_weight: 30,
  growth_weight: 20,
  breadth_weight: 10
};

export default function ExpansionAnalysis() {
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const [cities, setCities] = useState([]);
  const [defaultCities, setDefaultCities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const total = useMemo(
    () => Object.values(weights).reduce((sum, value) => sum + value, 0),
    [weights]
  );
  const validTotal = total === 100;

  const loadDefaultRanking = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await getCities({ limit: 10 });
      setCities(result);
      setDefaultCities(result);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDefaultRanking();
  }, [loadDefaultRanking]);

  const updateWeight = (key, value) => {
    setWeights((current) => ({ ...current, [key]: value }));
  };

  const submitWeights = async () => {
    if (!validTotal) return;
    setSubmitting(true);
    setError("");
    try {
      const result = await recalculateScores(
        Object.fromEntries(
          Object.entries(weights).map(([key, value]) => [key, value / 100])
        )
      );
      setCities(result.slice(0, 10));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  };

  const resetWeights = () => {
    setWeights(DEFAULT_WEIGHTS);
    setCities(defaultCities);
    setError("");
  };

  if (loading) return <LoadingState message="Loading opportunity model…" />;

  return (
    <>
      <PageHeader
        eyebrow="Decision support"
        title="Expansion Opportunity Model"
        description="Adjust weights to explore how different strategic priorities change market rankings."
      />

      <section className="panel p-5 sm:p-7">
        <div className="flex flex-col justify-between gap-4 border-b border-slate-100 pb-6 sm:flex-row sm:items-start">
          <div>
            <h2 className="text-lg font-bold text-slate-950">Strategic priorities</h2>
            <p className="mt-1 text-sm text-slate-500">
              Rankings can be recalculated only when the total equals 100%.
            </p>
          </div>
          <div className={`rounded-xl px-4 py-2 text-sm font-bold ${validTotal ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
            Total: {total}%
          </div>
        </div>

        <div className="py-7">
          <WeightControls weights={weights} onChange={updateWeight} />
        </div>

        <div className="flex flex-wrap items-center gap-3 border-t border-slate-100 pt-6">
          <button
            onClick={submitWeights}
            disabled={!validTotal || submitting}
            className="focus-ring rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            {submitting ? "Recalculating…" : "Recalculate Rankings"}
          </button>
          <button
            onClick={resetWeights}
            className="focus-ring rounded-xl px-4 py-2.5 text-sm font-semibold text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50"
          >
            Reset to Default
          </button>
        </div>
      </section>

      {error && <div className="mt-6"><ErrorState message={error} /></div>}

      <section className="panel mt-6 p-5 sm:p-6">
        <p className="eyebrow">Scenario results</p>
        <h2 className="mt-1 text-xl font-bold text-slate-950">Recalculated Top 10</h2>
        <OpportunityChart cities={cities} />
      </section>

      <section className="panel mt-6 p-5 sm:p-6">
        <p className="eyebrow">Full comparison</p>
        <h2 className="mb-4 mt-1 text-xl font-bold text-slate-950">Scenario Ranking</h2>
        <CityTable cities={cities} />
      </section>
    </>
  );
}
