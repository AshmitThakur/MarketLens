import { useCallback, useEffect, useMemo, useState } from "react";

import { getCities, getStates } from "../api/marketlens";
import { EmptyState, ErrorState, LoadingState } from "../components/AsyncState";
import CityTable from "../components/CityTable";
import PageHeader from "../components/PageHeader";

export default function Cities() {
  const [cities, setCities] = useState([]);
  const [states, setStates] = useState([]);
  const [state, setState] = useState("");
  const [search, setSearch] = useState("");
  const [sortConfig, setSortConfig] = useState({ key: "opportunity_score", direction: "desc" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadStates = useCallback(async () => {
    try {
      setStates(await getStates());
    } catch (requestError) {
      setError(requestError.message);
    }
  }, []);

  const loadCities = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setCities(await getCities({ state: state || undefined }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, [state]);

  useEffect(() => {
    loadStates();
  }, [loadStates]);

  useEffect(() => {
    loadCities();
  }, [loadCities]);

  const visibleCities = useMemo(() => {
    const query = search.trim().toLowerCase();
    const filtered = query
      ? cities.filter((city) => city.city.toLowerCase().includes(query))
      : [...cities];

    return filtered.sort((first, second) => {
      const a = first[sortConfig.key];
      const b = second[sortConfig.key];
      const comparison = typeof a === "string" ? a.localeCompare(b) : a - b;
      return sortConfig.direction === "asc" ? comparison : -comparison;
    });
  }, [cities, search, sortConfig]);

  const sortBy = (key) => {
    setSortConfig((current) => ({
      key,
      direction: current.key === key && current.direction === "asc" ? "desc" : "asc"
    }));
  };

  return (
    <>
      <PageHeader
        eyebrow="Market directory"
        title="City Analytics"
        description="Compare current demand, customer activity, growth and category breadth across every analyzed city."
      />

      <section className="panel p-5 sm:p-6">
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:max-w-2xl">
          <label>
            <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">Search city</span>
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="e.g. Quito"
              className="focus-ring w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400"
            />
          </label>
          <label>
            <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">Filter by state</span>
            <select
              value={state}
              onChange={(event) => setState(event.target.value)}
              className="focus-ring w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900"
            >
              <option value="">All states</option>
              {states.map((item) => (
                <option key={item.state} value={item.state}>
                  {item.state} ({item.cities})
                </option>
              ))}
            </select>
          </label>
        </div>

        {loading ? (
          <LoadingState message="Loading cities…" />
        ) : error ? (
          <ErrorState message={error} onRetry={loadCities} />
        ) : visibleCities.length ? (
          <>
            <p className="mb-3 text-sm text-slate-500">
              Showing <span className="font-semibold text-slate-900">{visibleCities.length}</span> cities
            </p>
            <CityTable cities={visibleCities} detailed onSort={sortBy} sortConfig={sortConfig} />
          </>
        ) : (
          <EmptyState />
        )}
      </section>
    </>
  );
}
