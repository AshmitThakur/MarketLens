const controls = [
  { key: "sales_weight", label: "Sales per Store" },
  { key: "transaction_weight", label: "Transactions per Store" },
  { key: "growth_weight", label: "Comparable Growth" },
  { key: "breadth_weight", label: "Category Breadth" }
];

export default function WeightControls({ weights, onChange }) {
  return (
    <div className="grid gap-x-8 gap-y-5 lg:grid-cols-2">
      {controls.map((control) => (
        <label key={control.key} className="block">
          <span className="mb-2 flex items-center justify-between gap-4 text-sm font-semibold text-slate-700">
            {control.label}
            <span className="rounded-md bg-slate-100 px-2 py-1 text-slate-900">
              {weights[control.key]}%
            </span>
          </span>
          <input
            type="range"
            min="0"
            max="100"
            step="1"
            value={weights[control.key]}
            onChange={(event) => onChange(control.key, Number(event.target.value))}
            className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-brand-600"
          />
        </label>
      ))}
    </div>
  );
}
