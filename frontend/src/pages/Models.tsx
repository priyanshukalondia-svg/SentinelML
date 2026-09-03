import { ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card, EmptyState, SkeletonCard } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import type { ModelVersion } from "../types";
import { useToast } from "../components/Toast";

export default function Models({ refreshKey }: { refreshKey: number }) {
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const { push } = useToast();

  function load() {
    setLoading(true);
    api
      .listModels()
      .then(setModels)
      .catch((err) => push({ tone: "error", title: "Failed to load models", description: err.message }))
      .finally(() => setLoading(false));
  }

  useEffect(load, [refreshKey]);

  async function handleDeploy(id: number) {
    setBusyId(id);
    try {
      await api.deployModel(id);
      push({ tone: "success", title: "Model deployed" });
      load();
    } catch (err: any) {
      push({ tone: "error", title: "Deploy failed", description: err.message });
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <PageHeader title="Models" description="Champion, challengers, and full version history for fraud-detector" />

      {loading && models.length === 0 ? (
        <div className="grid gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : models.length === 0 ? (
        <EmptyState
          title="No models trained yet"
          description="Go to Datasets to upload data and start a training run."
          icon={<ShieldCheck size={28} />}
          action={
            <Link to="/datasets" className="btn-primary">
              Go to Datasets
            </Link>
          }
        />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-muted text-left text-xs font-semibold uppercase tracking-wide text-ink-muted">
                <th className="px-4 py-3">Version</th>
                <th className="px-4 py-3">State</th>
                <th className="px-4 py-3">F1</th>
                <th className="px-4 py-3">ROC-AUC</th>
                <th className="px-4 py-3">Dataset</th>
                <th className="px-4 py-3">Deployment</th>
                <th className="px-4 py-3">Trained</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={m.id} className="border-b border-border-subtle last:border-0 hover:bg-surface-muted/60">
                  <td className="px-4 py-3">
                    <Link to={`/models/${m.id}`} className="font-medium text-brand-700 hover:underline">
                      {m.version}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge label={m.state} />
                  </td>
                  <td className="px-4 py-3 tabular-nums">{m.metrics.f1?.toFixed(3) ?? "—"}</td>
                  <td className="px-4 py-3 tabular-nums">{m.metrics.roc_auc?.toFixed(3) ?? "—"}</td>
                  <td className="px-4 py-3 text-ink-muted">{m.dataset_version}</td>
                  <td className="px-4 py-3">
                    <StatusBadge label={m.deployment_status} />
                  </td>
                  <td className="px-4 py-3 text-ink-muted">{new Date(m.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3 text-right">
                    {m.state !== "CHAMPION" && (
                      <button
                        className="btn-secondary py-1.5 text-xs"
                        disabled={busyId === m.id}
                        onClick={() => handleDeploy(m.id)}
                      >
                        {busyId === m.id ? "Deploying…" : "Deploy"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
