export function LoadingState({ message = "Loading analytics…" }) {
  return (
    <div className="panel grid min-h-[260px] place-items-center p-8 text-center">
      <div>
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-brand-600" />
        <p className="mt-4 text-sm font-medium text-slate-500">{message}</p>
      </div>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="panel border-red-100 bg-red-50/50 p-8 text-center">
      <p className="font-semibold text-red-800">Unable to load MarketLens data</p>
      <p className="mx-auto mt-2 max-w-xl text-sm text-red-700">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="focus-ring mt-5 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-red-700 shadow-sm ring-1 ring-red-200 hover:bg-red-50"
        >
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ message = "No cities match the current filters." }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 px-6 py-14 text-center text-sm font-medium text-slate-500">
      {message}
    </div>
  );
}
