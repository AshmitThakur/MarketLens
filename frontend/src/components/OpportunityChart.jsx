import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { formatScore } from "../utils/formatters";

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const city = payload[0].payload;
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-lg">
      <p className="font-semibold text-slate-900">{city.city}</p>
      <p className="text-sm text-slate-500">{city.state}</p>
      <p className="mt-2 text-sm font-semibold text-brand-600">
        Score {formatScore(city.opportunity_score)}
      </p>
    </div>
  );
}

export default function OpportunityChart({ cities }) {
  return (
    <div className="h-[390px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={cities}
          layout="vertical"
          margin={{ top: 4, right: 22, bottom: 4, left: 8 }}
        >
          <CartesianGrid horizontal={false} stroke="#e8edf5" />
          <XAxis
            type="number"
            domain={[0, 100]}
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#64748b", fontSize: 12 }}
          />
          <YAxis
            type="category"
            dataKey="city"
            width={90}
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#334155", fontSize: 12, fontWeight: 600 }}
          />
          <Tooltip cursor={{ fill: "#f8fafc" }} content={<ChartTooltip />} />
          <Bar
            dataKey="opportunity_score"
            fill="#356ae6"
            radius={[0, 6, 6, 0]}
            barSize={18}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
