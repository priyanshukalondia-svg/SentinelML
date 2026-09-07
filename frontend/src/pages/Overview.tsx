import { ArrowRight, Database, HeartPulse, ShieldCheck, Sparkles, Workflow } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardHeader, MetricStat } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { api } from "../services/api";
import type { MonitoringOverview } from "../types";

const lifecycle = [
  { step: "01", title: "Prepare", description: "Validate a dataset and choose a reference", icon: Database, color: "#4F46E5" },
  { step: "02", title: "Train", description: "Compare algorithms and track experiments", icon: Workflow, color: "#0EA5E9" },
  { step: "03", title: "Deploy", description: "Promote the strongest model to production", icon: ShieldCheck, color: "#10B981" },
  { step: "04", title: "Recover", description: "Detect drift and heal when health falls", icon: HeartPulse, color: "#F59E0B" },
];

const trend = [
  { name: "Prepare", health: 76 }, { name: "Train", health: 84 }, { name: "Deploy", health: 91 },
  { name: "Monitor", health: 88 }, { name: "Recover", health: 96 },
];
const demoSignals = [
  { name: "Performance", value: 86 }, { name: "Data quality", value: 94 }, { name: "Drift", value: 78 },
  { name: "Latency", value: 91 }, { name: "Errors", value: 97 },
];
const tooltipStyle = { borderRadius: 10, border: "1px solid #E5E7EB", boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)" };

export default function Overview({ refreshKey }: { refreshKey: number }) {
  const [overview, setOverview] = useState<MonitoringOverview | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.getMonitoringOverview().then((data) => !cancelled && setOverview(data)).catch(() => {});
    return () => { cancelled = true; };
  }, [refreshKey]);

  const hasModel = Boolean(overview?.active_model);
  const signals = overview ? [
    { name: "Performance", value: overview.health.performance },
    { name: "Data quality", value: overview.health.data_quality },
    { name: "Drift", value: overview.health.drift },
    { name: "Latency", value: overview.health.latency },
    { name: "Errors", value: overview.health.errors },
  ] : demoSignals;

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-2xl bg-ink px-6 py-8 text-white shadow-card sm:px-9 sm:py-10">
        <div className="relative z-10 max-w-2xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-xs font-medium text-indigo-100"><Sparkles size={14} /> A guided tour of SentinelML</div>
          <h1 className="max-w-xl text-3xl font-bold tracking-tight sm:text-4xl">Build models that keep watch over themselves.</h1>
          <p className="mt-4 max-w-xl text-sm leading-6 text-slate-300 sm:text-base">SentinelML takes a fraud model from raw data to monitored production. Start with your own CSV or use the built-in demo to see the full lifecycle in action.</p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link to="/datasets" className="btn-primary bg-white text-ink hover:bg-slate-100"><Database size={16} /> Upload or try a dataset <ArrowRight size={16} /></Link>
            <Link to="/monitoring" className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-3.5 py-2 text-sm font-medium text-white transition-colors hover:bg-white/10">Explore monitoring</Link>
          </div>
        </div>
        <div className="absolute -right-16 -top-24 h-72 w-72 rounded-full border-[32px] border-indigo-400/15" /><div className="absolute -bottom-32 right-20 h-72 w-72 rounded-full border-[18px] border-cyan-300/10" />
      </section>

      <div>
        <PageHeader title="How it works" description="One connected loop from data preparation to self-healing production operations" />
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          {lifecycle.map(({ step, title, description, icon: Icon, color }, index) => (
            <div key={title} className="relative rounded-2xl border border-border bg-surface p-5 shadow-card">
              <div className="mb-5 flex items-center justify-between"><div className="flex h-10 w-10 items-center justify-center rounded-xl" style={{ backgroundColor: `${color}15`, color }}><Icon size={20} /></div><span className="text-xs font-bold text-ink-faint">{step}</span></div>
              <h2 className="text-sm font-semibold text-ink">{title}</h2><p className="mt-1 text-xs leading-5 text-ink-muted">{description}</p>
              {index < lifecycle.length - 1 && <ArrowRight className="absolute -right-3 top-9 z-10 hidden text-ink-faint md:block" size={16} />}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3"><CardHeader title="Health through the lifecycle" subtitle={hasModel ? "Current production health" : "Illustrative demo path"} /><div className="h-56"><ResponsiveContainer width="100%" height="100%"><AreaChart data={trend} margin={{ top: 10, right: 8, left: -24, bottom: 0 }}><defs><linearGradient id="healthFill" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#4F46E5" stopOpacity={0.22} /><stop offset="95%" stopColor="#4F46E5" stopOpacity={0.02} /></linearGradient></defs><CartesianGrid stroke="#EEF0F4" vertical={false} /><XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#6B7280" }} /><YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#9CA3AF" }} /><Tooltip contentStyle={tooltipStyle} formatter={(value) => [`${value}/100`, "Health"]} /><Area type="monotone" dataKey="health" stroke="#4F46E5" strokeWidth={3} fill="url(#healthFill)" /></AreaChart></ResponsiveContainer></div></Card>
        <Card className="lg:col-span-2"><CardHeader title="Health signals" subtitle={hasModel ? overview?.health.status : "Ready for your first model"} /><div className="h-56"><ResponsiveContainer width="100%" height="100%"><BarChart data={signals} layout="vertical" margin={{ top: 0, right: 8, left: 8, bottom: 0 }}><CartesianGrid stroke="#EEF0F4" horizontal={false} /><XAxis type="number" domain={[0, 100]} hide /><YAxis type="category" dataKey="name" width={76} axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "#6B7280" }} /><Tooltip contentStyle={tooltipStyle} formatter={(value) => [`${value}/100`, "Score"]} /><Bar dataKey="value" radius={[0, 5, 5, 0]} barSize={16}>{signals.map((entry) => <Cell key={entry.name} fill={entry.value >= 90 ? "#10B981" : entry.value >= 75 ? "#F59E0B" : "#EF4444"} />)}</Bar></BarChart></ResponsiveContainer></div></Card>
      </div>

      <section className="rounded-2xl border border-brand-100 bg-brand-50/60 px-6 py-5 sm:flex sm:items-center sm:justify-between sm:gap-6"><div><p className="text-sm font-semibold text-ink">Ready to see the workflow for yourself?</p><p className="mt-1 text-sm text-ink-muted">Load the demo fraud dataset and train your first challenger model.</p></div><Link to="/datasets" className="btn-primary mt-4 shrink-0 sm:mt-0">Open datasets <ArrowRight size={16} /></Link></section>
      {hasModel && overview && <div className="grid grid-cols-2 gap-3 sm:grid-cols-4"><Card><MetricStat label="Active model" value={overview.active_model ?? "—"} /></Card><Card><MetricStat label="Predictions" value={overview.prediction_volume} /></Card><Card><MetricStat label="Avg latency" value={overview.avg_latency_ms} suffix="ms" /></Card><Card><MetricStat label="Drift" value={overview.drift.overall_status} tone={overview.drift.overall_status === "NORMAL" ? "healthy" : "warning"} /></Card></div>}
    </div>
  );
}