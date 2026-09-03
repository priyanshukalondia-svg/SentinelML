import { Beaker } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Card, CardHeader, EmptyState, SkeletonCard } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import type { TrainingRun } from "../types";

const METRIC_COLORS: Record<string, string> = {
  f1: "#4F46E5",
  roc_auc: "#10B981",
  accuracy: "#F59E0B",
};

export default function Experiments({ refreshKey }: { refreshKey: number }) {
  const [runs, setRuns] = useState<TrainingRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<number>>(new Set());

  useEffect(() => {
    setLoading(true);
    api
      .listTrainingRuns()
      .then((data) => {
        setRuns(data);
        setSelected(new Set(data.filter((r) => r.status === "COMPLETED").slice(0, 6).map((r) => r.id)));
      })
      .finally(() => setLoading(false));
  }, [refreshKey]);

  const completedRuns = runs.filter((r) => r.status === "COMPLETED");
  const chartData = useMemo(
    () =>
      completedRuns
        .filter((r) => selected.has(r.id))
        .map((r) => ({
          name: `${r.model_type} #${r.id}`,
          f1: r.metrics.f1 ?? 0,
          roc_auc: r.metrics.roc_auc ?? 0,
          accuracy: r.metrics.accuracy ?? 0,
        })),
    [completedRuns, selected]
  );

  function toggle(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  if (loading && runs.length === 0) {
    return (
      <div>
        <PageHeader title="Experiments" description="Compare training runs tracked in MLflow" />
        <div className="grid gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Experiments" description="Compare training runs tracked in MLflow" />

      {runs.length === 0 ? (
        <EmptyState
          title="No experiments yet"
          description="Start a training run from the Datasets page to see experiments here."
          icon={<Beaker size={28} />}
        />
      ) : (
        <>
          {chartData.length > 0 && (
            <Card className="mb-4">
              <CardHeader title="Metric comparison" subtitle="Selected runs, side by side" />
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#EEF0F2" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#6B7280" }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 1]} tick={{ fontSize: 11, fill: "#6B7280" }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #E5E7EB", fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="f1" name="F1" fill={METRIC_COLORS.f1} radius={[6, 6, 0, 0]} />
                  <Bar dataKey="roc_auc" name="ROC-AUC" fill={METRIC_COLORS.roc_auc} radius={[6, 6, 0, 0]} />
                  <Bar dataKey="accuracy" name="Accuracy" fill={METRIC_COLORS.accuracy} radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-card">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-muted text-left text-xs font-semibold uppercase tracking-wide text-ink-muted">
                  <th className="w-10 px-4 py-3"></th>
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">F1</th>
                  <th className="px-4 py-3">ROC-AUC</th>
                  <th className="px-4 py-3">Latency</th>
                  <th className="px-4 py-3">Triggered by</th>
                  <th className="px-4 py-3">Started</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id} className="border-b border-border-subtle last:border-0 hover:bg-surface-muted/60">
                    <td className="px-4 py-3">
                      {r.status === "COMPLETED" && (
                        <input
                          type="checkbox"
                          checked={selected.has(r.id)}
                          onChange={() => toggle(r.id)}
                          className="h-4 w-4 rounded border-border text-brand-600 focus:ring-brand-400"
                        />
                      )}
                    </td>
                    <td className="px-4 py-3 font-medium text-ink">{r.model_type}</td>
                    <td className="px-4 py-3">
                      <StatusBadge label={r.status} />
                    </td>
                    <td className="px-4 py-3 tabular-nums">{r.metrics.f1?.toFixed(3) ?? "—"}</td>
                    <td className="px-4 py-3 tabular-nums">{r.metrics.roc_auc?.toFixed(3) ?? "—"}</td>
                    <td className="px-4 py-3 tabular-nums text-ink-muted">
                      {r.metrics.inference_latency ? `${r.metrics.inference_latency.toFixed(1)}ms` : "—"}
                    </td>
                    <td className="px-4 py-3 text-ink-muted">{r.triggered_by}</td>
                    <td className="px-4 py-3 text-ink-muted">{new Date(r.started_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
