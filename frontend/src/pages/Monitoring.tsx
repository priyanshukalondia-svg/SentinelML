import { Activity, AlertOctagon, Clock, TrendingDown, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardHeader, EmptyState, MetricStat, SkeletonCard } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { api } from "../services/api";
import { useToast } from "../components/Toast";
import type { MonitoringOverview } from "../types";

const DRIFT_COLORS: Record<string, string> = { NORMAL: "#10B981", WARNING: "#F59E0B", HIGH: "#EF4444" };

const SIM_ACTIONS = [
  { key: "drift", label: "Simulate Data Drift", icon: Activity, fn: (a: typeof api) => a.simulateDrift() },
  { key: "degradation", label: "Simulate Model Degradation", icon: TrendingDown, fn: (a: typeof api) => a.simulateDegradation() },
  { key: "latency", label: "Simulate Latency Spike", icon: Clock, fn: (a: typeof api) => a.simulateLatency() },
  { key: "errors", label: "Simulate Error Spike", icon: AlertOctagon, fn: (a: typeof api) => a.simulateErrors() },
] as const;

export default function Monitoring({ refreshKey }: { refreshKey: number }) {
  const [overview, setOverview] = useState<MonitoringOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const { push } = useToast();

  function load() {
    setLoading(true);
    api
      .getMonitoringOverview()
      .then(setOverview)
      .finally(() => setLoading(false));
  }

  useEffect(load, [refreshKey]);

  async function runSimulation(key: string, fn: (a: typeof api) => Promise<{ message: string }>) {
    setBusyKey(key);
    try {
      const result = await fn(api);
      push({ tone: "info", title: "Simulation triggered", description: result.message });
      setTimeout(load, 1200);
    } catch (err: any) {
      push({ tone: "error", title: "Simulation failed", description: err.message });
    } finally {
      setBusyKey(null);
    }
  }

  if (loading && !overview) {
    return (
      <div>
        <PageHeader title="Monitoring" description="Drift, performance, latency and errors for the deployed model" />
        <SkeletonCard />
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Monitoring" description="Drift, performance, latency and errors for the deployed model" />

      <Card className="mb-6 border-brand-200 bg-brand-50/40">
        <CardHeader
          title="Failure simulation"
          subtitle="Trigger controlled failures to watch SentinelML detect and self-heal in real time"
        />
        <div className="flex flex-wrap gap-2">
          {SIM_ACTIONS.map(({ key, label, icon: Icon, fn }) => (
            <button key={key} className="btn-secondary" disabled={busyKey !== null} onClick={() => runSimulation(key, fn)}>
              <Icon size={15} />
              {busyKey === key ? "Running…" : label}
            </button>
          ))}
        </div>
      </Card>

      {!overview || !overview.active_model ? (
        <EmptyState title="No active model" description="Deploy a model to begin monitoring." icon={<Zap size={28} />} />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Card>
              <MetricStat
                label="Overall health"
                value={overview.health.overall}
                tone={overview.health.status === "HEALTHY" ? "healthy" : overview.health.status === "WARNING" ? "warning" : "critical"}
              />
            </Card>
            <Card>
              <MetricStat label="Current F1" value={overview.performance.current_f1?.toFixed(3) ?? "—"} />
            </Card>
            <Card>
              <MetricStat label="Avg latency" value={overview.avg_latency_ms} suffix="ms" />
            </Card>
            <Card>
              <MetricStat label="Prediction volume" value={overview.prediction_volume} />
            </Card>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader title="Feature drift" subtitle={`${overview.drift.method} vs. reference dataset`} />
              {overview.drift.features.length === 0 ? (
                <p className="py-8 text-center text-sm text-ink-muted">No production traffic yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={overview.drift.features} layout="vertical" margin={{ left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#EEF0F2" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11, fill: "#6B7280" }} axisLine={false} tickLine={false} />
                    <YAxis dataKey="feature" type="category" width={130} tick={{ fontSize: 11, fill: "#374151" }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #E5E7EB", fontSize: 12 }} />
                    <Bar dataKey="drift_score" radius={[0, 6, 6, 0]}>
                      {overview.drift.features.map((f, i) => (
                        <Cell key={i} fill={DRIFT_COLORS[f.status]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>

            <Card>
              <CardHeader title="Performance vs. baseline" />
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-lg bg-surface-muted px-4 py-3">
                  <span className="text-sm text-ink-muted">Baseline F1 (champion)</span>
                  <span className="tabular-nums text-lg font-bold text-ink">{overview.performance.baseline_f1?.toFixed(3) ?? "—"}</span>
                </div>
                <div className="flex items-center justify-between rounded-lg bg-surface-muted px-4 py-3">
                  <span className="text-sm text-ink-muted">Current F1 (labeled traffic)</span>
                  <span className="tabular-nums text-lg font-bold text-ink">
                    {overview.performance.current_f1?.toFixed(3) ?? "No labeled data yet"}
                  </span>
                </div>
                {overview.performance.degradation_pct !== null && (
                  <div className="flex items-center justify-between rounded-lg bg-critical-bg px-4 py-3">
                    <span className="text-sm text-critical-text">Degradation</span>
                    <span className="tabular-nums text-lg font-bold text-critical-text">{overview.performance.degradation_pct}%</span>
                  </div>
                )}
                <p className="text-xs text-ink-muted">Based on {overview.performance.sample_size} labeled predictions.</p>
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
