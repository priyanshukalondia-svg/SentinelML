import { AlertTriangle, Gauge, TrendingDown, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { RadialBar, RadialBarChart, PolarAngleAxis } from "recharts";
import { Card, CardHeader, EmptyState, MetricStat, SkeletonCard } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { StatusBadge, toneForState } from "../components/StatusBadge";
import { api } from "../services/api";
import type { Alert, MonitoringOverview } from "../types";

function HealthGauge({ score, status }: { score: number; status: string }) {
  const tone = toneForState(status);
  const color = { healthy: "#10B981", warning: "#F59E0B", critical: "#EF4444", info: "#3B82F6", neutral: "#9CA3AF" }[tone];
  const data = [{ name: "health", value: score, fill: color }];
  return (
    <div className="relative flex h-40 w-40 items-center justify-center">
      <RadialBarChart
        width={160}
        height={160}
        cx={80}
        cy={80}
        innerRadius={58}
        outerRadius={78}
        barSize={14}
        data={data}
        startAngle={90}
        endAngle={-270}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar background={{ fill: "#F3F4F6" }} dataKey="value" cornerRadius={8} />
      </RadialBarChart>
      <div className="absolute flex flex-col items-center">
        <span className="tabular-nums text-3xl font-extrabold text-ink">{score}</span>
        <span className="text-[11px] font-medium text-ink-muted">/ 100</span>
      </div>
    </div>
  );
}

export default function Overview({ refreshKey }: { refreshKey: number }) {
  const [overview, setOverview] = useState<MonitoringOverview | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([api.getMonitoringOverview(), api.listAlerts()])
      .then(([ov, al]) => {
        if (cancelled) return;
        setOverview(ov);
        setAlerts(al.filter((a) => a.state === "OPEN").slice(0, 5));
        setError(null);
      })
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  if (loading && !overview) {
    return (
      <div>
        <PageHeader title="Overview" description="Real-time system health at a glance" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div>
        <PageHeader title="Overview" description="Real-time system health at a glance" />
        <EmptyState
          title="Couldn't load monitoring data"
          description={error}
          icon={<AlertTriangle size={28} />}
        />
      </div>
    );
  }

  if (!overview) return null;

  const noModel = !overview.active_model;

  return (
    <div>
      <PageHeader
        title="Overview"
        description="Real-time system health at a glance"
        action={
          <Link to="/monitoring" className="btn-secondary">
            <Gauge size={16} /> View full monitoring
          </Link>
        }
      />

      {noModel ? (
        <EmptyState
          title="No model deployed yet"
          description="Upload a dataset, train a model, and deploy it to start monitoring production health."
          action={
            <Link to="/datasets" className="btn-primary">
              Get started
            </Link>
          }
        />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <CardHeader title="Model Health" subtitle={overview.active_model ?? undefined} />
              <div className="flex items-center justify-center gap-6">
                <HealthGauge score={overview.health.overall} status={overview.health.status} />
                <div className="space-y-2">
                  <StatusBadge label={overview.health.status} pulse={overview.health.status !== "HEALTHY"} />
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 pt-1 text-xs text-ink-muted">
                    <span>Performance {overview.health.performance}</span>
                    <span>Drift {overview.health.drift}</span>
                    <span>Quality {overview.health.data_quality}</span>
                    <span>Latency {overview.health.latency}</span>
                    <span>Errors {overview.health.errors}</span>
                  </div>
                </div>
              </div>
            </Card>

            <div className="grid grid-cols-2 gap-4 lg:col-span-2">
              <Card>
                <MetricStat label="Active model" value={overview.active_model ?? "—"} />
              </Card>
              <Card>
                <MetricStat
                  label="Drift status"
                  value={overview.drift.overall_status}
                  tone={overview.drift.overall_status === "NORMAL" ? "healthy" : overview.drift.overall_status === "WARNING" ? "warning" : "critical"}
                />
              </Card>
              <Card>
                <MetricStat
                  label="Current F1"
                  value={overview.performance.current_f1?.toFixed(3) ?? overview.performance.baseline_f1?.toFixed(3) ?? "—"}
                />
              </Card>
              <Card>
                <MetricStat label="Avg latency" value={overview.avg_latency_ms} suffix="ms" />
              </Card>
              <Card>
                <MetricStat label="Prediction volume" value={overview.prediction_volume} suffix="recent" />
              </Card>
              <Card>
                <MetricStat label="Open alerts" value={alerts.length} tone={alerts.length > 0 ? "warning" : "default"} />
              </Card>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader
                title="Top drifting features"
                subtitle={`${overview.drift.method} method`}
                action={
                  <Link to="/monitoring" className="text-xs font-medium text-brand-600 hover:text-brand-700">
                    View all →
                  </Link>
                }
              />
              {overview.drift.features.length === 0 ? (
                <p className="py-6 text-center text-sm text-ink-muted">No production traffic yet to compare against the reference dataset.</p>
              ) : (
                <div className="space-y-2">
                  {overview.drift.features.slice(0, 5).map((f) => (
                    <div key={f.feature} className="flex items-center justify-between rounded-lg bg-surface-muted px-3 py-2">
                      <span className="text-sm font-medium text-ink">{f.feature}</span>
                      <div className="flex items-center gap-2">
                        <span className="tabular-nums text-xs text-ink-muted">{f.drift_score.toFixed(3)}</span>
                        <StatusBadge label={f.status} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card>
              <CardHeader
                title="Open alerts"
                action={
                  <Link to="/alerts" className="text-xs font-medium text-brand-600 hover:text-brand-700">
                    View all →
                  </Link>
                }
              />
              {alerts.length === 0 ? (
                <EmptyState title="All clear" description="No open alerts right now." icon={<Zap size={24} />} />
              ) : (
                <div className="space-y-2">
                  {alerts.map((a) => (
                    <div key={a.id} className="flex items-start justify-between gap-3 rounded-lg bg-surface-muted px-3 py-2.5">
                      <div>
                        <p className="text-sm font-medium text-ink">{a.title}</p>
                        <p className="mt-0.5 text-xs text-ink-muted">{a.description}</p>
                      </div>
                      <StatusBadge label={a.severity} tone={a.severity === "CRITICAL" ? "critical" : a.severity === "WARNING" ? "warning" : "info"} />
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {overview.performance.degradation_pct !== null && overview.performance.degradation_pct > 0 && (
            <div className="mt-4 flex items-center gap-2 rounded-xl border border-warning-border bg-warning-bg px-4 py-3 text-sm text-warning-text">
              <TrendingDown size={16} />
              Performance has degraded {overview.performance.degradation_pct}% from the champion's baseline F1.
            </div>
          )}
        </>
      )}
    </div>
  );
}
