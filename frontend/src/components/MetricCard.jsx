export default function MetricCard({ label, value, detail, accent = false }) {
  return (
    <section className={`panel relative overflow-hidden p-5 lg:p-6 ${accent ? "border-brand-100" : ""}`}>
      {accent && <div className="absolute inset-x-0 top-0 h-1 bg-brand-500" />}
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-bold tracking-tight text-slate-950">{value}</p>
      {detail && <p className="mt-1 text-sm text-slate-500">{detail}</p>}
    </section>
  );
}
