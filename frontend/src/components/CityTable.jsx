import { useNavigate } from "react-router-dom";

import {
  formatGrowth,
  formatNumber,
  formatScore
} from "../utils/formatters";

const overviewColumns = [
  { key: "rank", label: "Rank" },
  { key: "city", label: "City" },
  { key: "state", label: "State" },
  { key: "active_stores", label: "Stores" },
  { key: "comparable_growth_pct", label: "Growth" },
  { key: "opportunity_score", label: "Opportunity Score" }
];

const detailedColumns = [
  { key: "city", label: "City" },
  { key: "state", label: "State" },
  { key: "active_stores", label: "Stores" },
  { key: "sales_per_store", label: "Sales / Store" },
  { key: "transactions_per_store", label: "Transactions / Store" },
  { key: "comparable_growth_pct", label: "Growth %" },
  { key: "category_breadth", label: "Category Breadth" },
  { key: "opportunity_score", label: "Opportunity Score" }
];

function displayValue(city, key, index) {
  if (key === "rank") return index + 1;
  if (key === "comparable_growth_pct") return formatGrowth(city[key]);
  if (["sales_per_store", "transactions_per_store"].includes(key)) {
    return formatNumber(city[key]);
  }
  if (key === "opportunity_score") {
    return (
      <span className="inline-flex min-w-[68px] justify-center rounded-lg bg-brand-50 px-2.5 py-1 font-bold text-brand-700">
        {formatScore(city[key])}
      </span>
    );
  }
  return city[key];
}

export default function CityTable({
  cities,
  detailed = false,
  onSort,
  sortConfig
}) {
  const navigate = useNavigate();
  const columns = detailed ? detailedColumns : overviewColumns;

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] border-collapse text-left">
        <thead>
          <tr className="border-b border-slate-200">
            {columns.map((column) => (
              <th
                key={column.key}
                className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 first:pl-0 last:pr-0"
              >
                {onSort && column.key !== "rank" ? (
                  <button
                    className="focus-ring rounded text-left hover:text-slate-900"
                    onClick={() => onSort(column.key)}
                  >
                    {column.label}
                    {sortConfig?.key === column.key && (
                      <span aria-hidden="true">
                        {sortConfig.direction === "asc" ? " ↑" : " ↓"}
                      </span>
                    )}
                  </button>
                ) : (
                  column.label
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cities.map((city, index) => (
            <tr
              key={`${city.city}-${city.state}`}
              tabIndex={0}
              role="link"
              onClick={() => navigate(`/cities/${encodeURIComponent(city.city)}`)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  navigate(`/cities/${encodeURIComponent(city.city)}`);
                }
              }}
              className="cursor-pointer border-b border-slate-100 text-sm text-slate-600 transition-colors last:border-0 hover:bg-slate-50 focus:bg-brand-50 focus:outline-none"
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={`whitespace-nowrap px-4 py-4 first:pl-0 last:pr-0 ${
                    column.key === "city" ? "font-semibold text-slate-950" : ""
                  }`}
                >
                  {displayValue(city, column.key, index)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
