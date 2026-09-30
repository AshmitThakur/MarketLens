import { NavLink } from "react-router-dom";

const navigation = [
  { label: "Overview", to: "/", end: true },
  { label: "Expansion Analysis", to: "/analysis" },
  { label: "Compare Markets", to: "/compare" },
  { label: "Cities", to: "/cities" }
];

export default function Sidebar() {
  return (
    <aside className="border-b border-slate-200 bg-white md:fixed md:inset-y-0 md:left-0 md:z-20 md:flex md:w-64 md:flex-col md:border-b-0 md:border-r">
      <div className="flex items-center gap-3 px-5 py-5 md:px-7 md:py-8">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-brand-600 text-sm font-bold text-white shadow-sm">
          ML
        </div>
        <div>
          <p className="text-lg font-bold tracking-tight text-slate-950">MarketLens</p>
          <p className="text-[11px] font-medium text-slate-500">
            Retail expansion strategy
          </p>
        </div>
      </div>

      <nav className="flex gap-1 overflow-x-auto px-4 pb-4 md:flex-1 md:flex-col md:gap-2 md:overflow-visible md:px-4 md:pb-0">
        {navigation.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `focus-ring whitespace-nowrap rounded-xl px-4 py-3 text-sm font-semibold transition-colors ${
                isActive
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="hidden border-t border-slate-100 px-7 py-6 md:block">
        <p className="text-xs font-medium text-slate-400">
          Powered by retail analytics
        </p>
      </div>
    </aside>
  );
}
