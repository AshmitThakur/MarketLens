import { useCallback, useEffect, useState } from "react";

import { getCities, getOverview } from "../api/marketlens";
import { ErrorState, LoadingState } from "../components/AsyncState";
import CityTable from "../components/CityTable";
import ExecutiveCopilot from "../components/ExecutiveCopilot";
import MetricCard from "../components/MetricCard";
import OpportunityChart from "../components/OpportunityChart";
import PageHeader from "../components/PageHeader";
import { formatScore } from "../utils/formatters";

export default function Overview() {
  const [overview, setOverview] = useState(null);
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [overviewData, cityData] = await Promise.all([
        getOverview(),
        getCities({ limit: 10 })
      ]);
      setOverview(overviewData);
      setCities(cityData);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) return <LoadingState message="Loading executive dashboard…" />;
  if (error) return <ErrorState message={error} onRetry={loadDashboard} />;

  return (
    <>
      <PageHeader
        eyebrow="Executive overview"
        title="Retail expansion at a glance"
        description={`Current analysis period: ${overview.analysis_period.start} to ${overview.analysis_period.end}`}
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Stores Analyzed" value={overview.total_stores} detail="Current retail footprint" />
        <MetricCard label="Cities Analyzed" value={overview.cities_analyzed} detail={`${overview.product_families} product families`} />
        <MetricCard label="States Represented" value={overview.states} detail="Across the analyzed market" />
        <MetricCard
          label="Top Opportunity"
          value={overview.top_opportunity.city}
          detail={`${formatScore(overview.top_opportunity.score)} / 100`}
          accent
        />
      </div>

      <section className="panel mt-6 p-5 sm:p-6">
        <div className="mb-3">
          <p className="eyebrow">Top markets</p>
          <h2 className="mt-1 text-xl font-bold text-slate-950">
            Expansion Opportunity Ranking
          </h2>
        </div>
        <OpportunityChart cities={cities} />
      </section>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_340px]">
        <section className="panel min-w-0 p-5 sm:p-6">
          <p className="eyebrow">Ranked results</p>
          <h2 className="mb-4 mt-1 text-xl font-bold text-slate-950">
            Opportunity Table
          </h2>
          <CityTable cities={cities} />
        </section>

        <aside className="panel h-fit p-6">
          <p className="eyebrow">Methodology</p>
          <h2 className="mt-1 text-xl font-bold text-slate-950">Score Composition</h2>
          <div className="mt-6 space-y-4">
            {[
              ["Sales per Store", 40],
              ["Transactions per Store", 30],
              ["Comparable Growth", 20],
              ["Category Breadth", 10]
            ].map(([label, weight]) => (
              <div key={label}>
                <div className="mb-1.5 flex justify-between text-sm">
                  <span className="font-medium text-slate-600">{label}</span>
                  <span className="font-bold text-slate-900">{weight}%</span>
                </div>
                <div className="h-1.5 rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-brand-500" style={{ width: `${weight * 2}%` }} />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-6 border-t border-slate-100 pt-5 text-sm leading-6 text-slate-500">
            MarketLens combines current demand, customer activity, growth and category diversity into a normalized opportunity score.
          </p>
        </aside>
      </div>

      <ExecutiveCopilot />
    </>
  );
}
