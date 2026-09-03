import { Database, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Card, CardHeader, EmptyState, SkeletonCard } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import { useToast } from "../components/Toast";
import type { Dataset } from "../types";

const MODEL_OPTIONS = [
  { key: "logistic_regression", label: "Logistic Regression" },
  { key: "random_forest", label: "Random Forest" },
  { key: "xgboost", label: "XGBoost" },
  { key: "svm", label: "SVM" },
];

export default function Datasets({ refreshKey }: { refreshKey: number }) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [targetColumn, setTargetColumn] = useState("fraud");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [trainingDatasetId, setTrainingDatasetId] = useState<number | null>(null);
  const [selectedModels, setSelectedModels] = useState<Set<string>>(new Set(MODEL_OPTIONS.map((m) => m.key)));
  const [training, setTraining] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { push } = useToast();

  function load() {
    setLoading(true);
    api
      .listDatasets()
      .then(setDatasets)
      .finally(() => setLoading(false));
  }

  useEffect(load, [refreshKey]);

  async function handleUpload(file: File) {
    setUploading(true);
    try {
      const dataset = await api.uploadDataset(file, targetColumn);
      push({
        tone: dataset.validation_status === "FAILED" ? "error" : "success",
        title: `Dataset ${dataset.version} ingested`,
        description: `${dataset.row_count.toLocaleString()} rows — status: ${dataset.validation_status}`,
      });
      load();
    } catch (err: any) {
      push({ tone: "error", title: "Upload failed", description: err.message });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleTrain() {
    if (trainingDatasetId == null || selectedModels.size === 0) return;
    setTraining(true);
    try {
      const runs = await api.startTraining(trainingDatasetId, Array.from(selectedModels));
      const succeeded = runs.filter((r) => r.status === "COMPLETED").length;
      push({
        tone: succeeded > 0 ? "success" : "error",
        title: "Training complete",
        description: `${succeeded}/${runs.length} models trained successfully.`,
      });
      setTrainingDatasetId(null);
    } catch (err: any) {
      push({ tone: "error", title: "Training failed to start", description: err.message });
    } finally {
      setTraining(false);
    }
  }

  return (
    <div>
      <PageHeader title="Datasets" description="Upload, version, and validate training data" />

      <Card className="mb-6">
        <CardHeader title="Upload a new dataset" subtitle="CSV files only — validated automatically on upload" />
        <div className="flex flex-wrap items-end gap-3">
          <div className="w-56">
            <label className="mb-1 block text-xs font-medium text-ink-muted">Target column</label>
            <input className="input" value={targetColumn} onChange={(e) => setTargetColumn(e.target.value)} />
          </div>
          <label className="btn-primary cursor-pointer">
            <Upload size={16} />
            {uploading ? "Uploading…" : "Choose CSV file"}
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              disabled={uploading}
              onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
            />
          </label>
        </div>
      </Card>

      {loading && datasets.length === 0 ? (
        <div className="grid gap-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : datasets.length === 0 ? (
        <EmptyState title="No datasets uploaded yet" description="Upload a CSV above to get started." icon={<Database size={28} />} />
      ) : (
        <div className="space-y-3">
          {datasets.map((d) => (
            <Card key={d.id}>
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 cursor-pointer" onClick={() => setExpandedId(expandedId === d.id ? null : d.id)}>
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-ink">
                      {d.dataset_id} <span className="text-ink-muted">{d.version}</span>
                    </p>
                    <StatusBadge label={d.validation_status} />
                    {d.is_reference && <StatusBadge label="Drift reference" tone="info" />}
                  </div>
                  <p className="mt-1 text-xs text-ink-muted">
                    {d.row_count.toLocaleString()} rows · {d.feature_count} columns · target: {d.target_column} · uploaded{" "}
                    {new Date(d.created_at).toLocaleString()}
                  </p>
                </div>
                <button
                  className="btn-primary"
                  disabled={d.validation_status === "FAILED"}
                  onClick={() => setTrainingDatasetId(trainingDatasetId === d.id ? null : d.id)}
                >
                  Train models
                </button>
              </div>

              {expandedId === d.id && (
                <div className="mt-4 grid grid-cols-2 gap-3 border-t border-border-subtle pt-4 text-sm sm:grid-cols-4">
                  <QualityStat label="Missing" value={`${d.quality_report.overall_missing_pct ?? 0}%`} />
                  <QualityStat label="Duplicates" value={`${d.quality_report.duplicate_pct ?? 0}%`} />
                  <QualityStat label="Issues" value={String(d.quality_report.issues?.length ?? 0)} />
                  <QualityStat label="Warnings" value={String(d.quality_report.warnings?.length ?? 0)} />
                  {d.quality_report.class_distribution && (
                    <div className="col-span-2 sm:col-span-4">
                      <p className="mb-1 text-xs font-medium text-ink-muted">Class distribution</p>
                      <div className="flex gap-2">
                        {Object.entries(d.quality_report.class_distribution).map(([k, v]: any) => (
                          <span key={k} className="rounded-lg bg-surface-muted px-2 py-1 text-xs">
                            {k}: {v.toFixed(1)}%
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {trainingDatasetId === d.id && (
                <div className="mt-4 rounded-xl border border-border bg-surface-muted p-4">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-muted">Select models to train</p>
                  <div className="mb-3 flex flex-wrap gap-2">
                    {MODEL_OPTIONS.map((m) => (
                      <label
                        key={m.key}
                        className="flex cursor-pointer items-center gap-2 rounded-lg border border-border bg-surface px-3 py-1.5 text-xs font-medium text-ink"
                      >
                        <input
                          type="checkbox"
                          checked={selectedModels.has(m.key)}
                          onChange={() =>
                            setSelectedModels((prev) => {
                              const next = new Set(prev);
                              next.has(m.key) ? next.delete(m.key) : next.add(m.key);
                              return next;
                            })
                          }
                        />
                        {m.label}
                      </label>
                    ))}
                  </div>
                  <button className="btn-primary" disabled={training} onClick={handleTrain}>
                    {training ? "Training…" : "Start training"}
                  </button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function QualityStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-ink-muted">{label}</p>
      <p className="font-semibold text-ink">{value}</p>
    </div>
  );
}
