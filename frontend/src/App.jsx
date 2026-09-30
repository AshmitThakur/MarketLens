import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { LoadingState } from "./components/AsyncState";
import Sidebar from "./components/Sidebar";

const Cities = lazy(() => import("./pages/Cities"));
const CityDetail = lazy(() => import("./pages/CityDetail"));
const CompareMarkets = lazy(() => import("./pages/CompareMarkets"));
const ExpansionAnalysis = lazy(() => import("./pages/ExpansionAnalysis"));
const Overview = lazy(() => import("./pages/Overview"));

export default function App() {
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <Sidebar />
      <main className="min-w-0 px-4 pb-10 pt-6 md:ml-64 md:px-8 lg:px-10">
        <div className="mx-auto max-w-[1440px]">
          <Suspense fallback={<LoadingState message="Loading dashboard…" />}>
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/analysis" element={<ExpansionAnalysis />} />
              <Route path="/compare" element={<CompareMarkets />} />
              <Route path="/cities" element={<Cities />} />
              <Route path="/cities/:city" element={<CityDetail />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </div>
      </main>
    </div>
  );
}
