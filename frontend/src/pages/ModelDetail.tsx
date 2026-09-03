import { ArrowLeft, GitBranch } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardHeader, MetricStat, Skeleton } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import { useToast } from "../components/Toast";
import type { ModelVersion } from "../types";

const BAR_COLOR = "#6366F1";

export default function ModelDetail() {
  const { id } = useParams();
  const modelId = Number(id);
  const [model, setModel] = useState<ModelVersion | null>(null);
  const [lineage, setLineage] = useState<any>(null);
  const [globalExplain, setGlobalExplain] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { push } = useToast();

  useEffect(() => {
    setLoading(true);
    Promise.all([api.getModel(modelId), api.getModelLineage(modelId)])
      .then(([m, l]) => {
        setModel(m);
        setLineage(l);
      })
      .catch((err) => push({ tone: "error", title: "Failed to load model", description: err.message }))
      .finally(() => setLoading(false));

    fetch(`${(import.meta as any).env?.VITE_API_BASE_URL || "http://localhost:8000/api/v1"}/models/${modelId}/explainability/global`)
      .then((r) => r.json())
      .then(setGlobalExplain)
      .catch(() => {});
  }, [modelId]);

  if (loading || !model) {
    return (
      <div>
        <Skeleton className="mb-4 h-6 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const chartData = (globalExplain?.features ?? []).slice(0, 8).map((f: any) => ({
    name: f.feature,
    importance: f.importance,
  }));

  return (
    <div>
      <Link to="/models" className="mb-3 inline-flex items-center gap-1 text-sm text-ink-muted hover:text-ink">
        <ArrowLeft size={14} /> Back to models
      </Link>
      <PageHeader
        title={`${model.model_name} — ${model.version}`}
        description={`Trained on dataset ${model.dataset_version}`}
        action={<StatusBadge label={model.state} />}
      />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card>
          <MetricStat label="F1 Score" value={model.metrics.f1?.toFixed(3) ?? "—"} />
        </Card>
        <Card>
          <MetricStat label="ROC-AUC" value={model.metrics.roc_auc?.toFixed(3) ?? "—"} />
        </Card>
        <Card>
          <MetricStat label="Precision" value={model.metrics.precision?.toFixed(3) ?? "—"} />
        </Card>
        <Card>
          <MetricStat label="Recall" value={model.metrics.recall?.toFixed(3) ?? "—"} />
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Global feature importance" subtitle={globalExplain ? `via ${globalExplain.method}` : "Loading…"} />
          {chartData.length === 0 ? (
            <p className="py-8 text-center text-sm text-ink-muted">Explainability data unavailable for this model.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 24 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#EEF0F2" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11, fill: "#6B7280" }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" width={140} tick={{ fontSize: 11, fill: "#374151" }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ borderRadius: 10, border: "1px solid #E5E7EB", fontSize: 12 }}
                  formatter={(v: number) => v.toFixed(3)}
                />
                <Bar dataKey="importance" radius={[0, 6, 6, 0]}>
                  {chartData.map((_: any, i: number) => (
                    <Cell key={i} fill={BAR_COLOR} fillOpacity={1 - i * 0.08} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card>
          <CardHeader title="Model lineage" subtitle="Full traceability back to training configuration" />
          {lineage && (
            <div className="space-y-3 text-sm">
              <LineageRow label="Dataset version" value={lineage.dataset_version} />
              <LineageRow label="Training run" value={`#${lineage.training_run_id}`} />
              <LineageRow label="Model type" value={lineage.model_type} />
              <LineageRow label="MLflow run ID" value={lineage.mlflow_run_id || "—"} mono />
              <LineageRow label="Git commit" value={lineage.git_commit || "not recorded"} mono />
              <LineageRow label="Deployment" value={lineage.deployment_status} />
              <LineageRow label="Created" value={new Date(lineage.created_at).toLocaleString()} />
            </div>
          )}
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader title="Training parameters" />
        <div className="flex flex-wrap gap-2">
          {lineage &&
            Object.entries(lineage.params ?? {}).map(([k, v]) => (
              <span key={k} className="rounded-lg bg-surface-muted px-2.5 py-1 font-mono text-xs text-ink-muted">
                {k}: <span className="font-medium text-ink">{String(v)}</span>
              </span>
            ))}
        </div>
      </Card>
    </div>
  );
}

function LineageRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between border-b border-border-subtle pb-2 last:border-0">
      <span className="text-ink-muted">{label}</span>
      <span className={mono ? "font-mono text-xs text-ink" : "font-medium text-ink"}>{value}</span>
    </div>
  );
}
