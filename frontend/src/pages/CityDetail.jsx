import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { getCity } from "../api/marketlens";
import { ErrorState, LoadingState } from "../components/AsyncState";
import AskMarketLens from "../components/AskMarketLens";
import MetricCard from "../components/MetricCard";
import {
  formatGrowth,
  formatNumber,
  formatScore
} from "../utils/formatters";

export default function CityDetail() {
  const { city } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadCity = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await getCity(city));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, [city]);

  useEffect(() => {
    loadCity();
  }, [loadCity]);

  if (loading) return <LoadingState message="Loading city analytics…" />;
  if (error) {
    return (
      <>
        <Link to="/cities" className="mb-5 inline-block text-sm font-semibold text-brand-600 hover:text-brand-700">← Back to cities</Link>
        <ErrorState message={error} onRetry={loadCity} />
      </>
    );
  }

  const components = [
    { name: "Sales", score: data.sales_score },
    { name: "Transactions", score: data.transaction_score },
    { name: "Growth", score: data.growth_score },
    { name: "Breadth", score: data.breadth_score }
  ];
  const weightRows = [
    ["Sales per Store", data.weights.sales_weight],
    ["Transactions per Store", data.weights.transaction_weight],
    ["Comparable Growth", data.weights.growth_weight],
    ["Category Breadth", data.weights.breadth_weight]
  ];

  return (
    <>
      <Link to="/cities" className="focus-ring mb-5 inline-block rounded text-sm font-semibold text-brand-600 hover:text-brand-700">← Back to cities</Link>

      <header className="panel overflow-hidden">
        <div className="border-b border-slate-100 p-6 sm:p-8">
          <p className="eyebrow">City opportunity profile</p>
          <div className="mt-2 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">{data.city}</h1>
              <p className="mt-1 text-base text-slate-500">{data.state}</p>
            </div>
            <div className="sm:text-right">
              <p className="text-sm font-medium text-slate-500">Opportunity Score</p>
              <p className="mt-1 text-3xl font-bold text-brand-600">{formatScore(data.opportunity_score)} <span className="text-base font-medium text-slate-400">/ 100</span></p>
            </div>
          </div>
        </div>
      </header>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Sales Score" value={formatScore(data.sales_score)} />
        <MetricCard label="Transaction Score" value={formatScore(data.transaction_score)} />
        <MetricCard label="Growth Score" value={formatScore(data.growth_score)} />
        <MetricCard label="Category Breadth Score" value={formatScore(data.breadth_score)} />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.35fr_1fr]">
        <section className="panel p-5 sm:p-6">
          <p className="eyebrow">Normalized comparison</p>
          <h2 className="mt-1 text-xl font-bold text-slate-950">Component Scores</h2>
          <div className="mt-5 h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={components} margin={{ top: 8, right: 8, bottom: 0, left: -15 }}>
                <CartesianGrid vertical={false} stroke="#e8edf5" />
                <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fill: "#475569", fontSize: 12 }} />
                <YAxis domain={[0, 100]} tickLine={false} axisLine={false} tick={{ fill: "#64748b", fontSize: 12 }} />
                <Tooltip formatter={(value) => [formatScore(value), "Score"]} />
                <Bar
                  dataKey="score"
                  fill="#356ae6"
                  radius={[6, 6, 0, 0]}
                  maxBarSize={58}
                  isAnimationActive={false}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="panel p-5 sm:p-6">
          <p className="eyebrow">Observed activity</p>
          <h2 className="mt-1 text-xl font-bold text-slate-950">Business Metrics</h2>
          <dl className="mt-5 divide-y divide-slate-100">
            {[
              ["Active Stores", data.active_stores],
              ["Sales per Store", formatNumber(data.sales_per_store)],
              ["Transactions per Store", formatNumber(data.transactions_per_store)],
              ["Comparable Growth", formatGrowth(data.comparable_growth_pct)],
              ["Category Breadth", data.category_breadth]
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between gap-4 py-3.5">
                <dt className="text-sm text-slate-500">{label}</dt>
                <dd className="text-sm font-bold text-slate-900">{value}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>

      <section className="panel mt-6 p-5 sm:p-6">
        <p className="eyebrow">Model configuration</p>
        <h2 className="mt-1 text-xl font-bold text-slate-950">Current Scoring Weights</h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {weightRows.map(([label, value]) => (
            <div key={label} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-1 text-xl font-bold text-slate-900">{Math.round(value * 100)}%</p>
            </div>
          ))}
        </div>
      </section>

      <AskMarketLens city={data.city} />
    </>
  );
}
