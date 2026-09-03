import { Save, Settings as SettingsIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { Card, CardHeader, Skeleton } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { api } from "../services/api";
import { useToast } from "../components/Toast";

interface FieldDef {
  key: string;
  label: string;
  help: string;
  step?: number;
  min?: number;
  max?: number;
}

const SECTIONS: { title: string; fields: FieldDef[] }[] = [
  {
    title: "Monitoring",
    fields: [
      { key: "monitoring_interval_seconds", label: "Check interval (seconds)", help: "How often the background monitor evaluates drift/health.", step: 5, min: 5 },
    ],
  },
  {
    title: "Drift thresholds",
    fields: [
      { key: "drift_warning_threshold", label: "Warning threshold", help: "PSI/KS score that triggers a WARNING status.", step: 0.01, min: 0, max: 1 },
      { key: "drift_critical_threshold", label: "Critical threshold", help: "PSI/KS score that triggers retraining.", step: 0.01, min: 0, max: 1 },
    ],
  },
  {
    title: "Promotion rules",
    fields: [
      { key: "promotion_min_improvement", label: "Minimum F1 improvement", help: "Challenger must beat champion by at least this much.", step: 0.01, min: 0 },
      { key: "promotion_max_latency_increase_pct", label: "Max latency increase (%)", help: "Challenger latency regression tolerance.", step: 1, min: 0 },
    ],
  },
  {
    title: "Rollback",
    fields: [
      { key: "rollback_max_error_rate", label: "Max error rate", help: "Prediction error rate that triggers rollback.", step: 0.01, min: 0, max: 1 },
      { key: "rollback_min_health_score", label: "Minimum health score", help: "Health score below this triggers automatic rollback.", step: 1, min: 0, max: 100 },
    ],
  },
  {
    title: "Training",
    fields: [
      { key: "training_timeout_seconds", label: "Training timeout (seconds)", help: "A training run is marked FAILED past this duration.", step: 30, min: 30 },
      { key: "retraining_cooldown_seconds", label: "Retraining cooldown (seconds)", help: "Minimum time between automatic retraining triggers for the same condition.", step: 30, min: 0 },
    ],
  },
];

export default function Settings() {
  const [config, setConfig] = useState<Record<string, any> | null>(null);
  const [draft, setDraft] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const { push } = useToast();

  useEffect(() => {
    api.getConfig().then((c) => {
      setConfig(c);
      setDraft(c);
    });
  }, []);

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await api.updateConfig(draft);
      setConfig(updated);
      setDraft(updated);
      push({ tone: "success", title: "Settings updated", description: "New thresholds are effective immediately." });
    } catch (err: any) {
      push({ tone: "error", title: "Failed to save settings", description: err.message });
    } finally {
      setSaving(false);
    }
  }

  if (!config) {
    return (
      <div>
        <PageHeader title="Settings" description="Configurable thresholds — nothing here is hard-coded" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  const dirty = JSON.stringify(config) !== JSON.stringify(draft);

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Configurable thresholds — nothing here is hard-coded"
        action={
          <button className="btn-primary" disabled={!dirty || saving} onClick={handleSave}>
            <Save size={15} /> {saving ? "Saving…" : "Save changes"}
          </button>
        }
      />

      <div className="mb-4 flex items-center gap-2 rounded-xl border border-info-border bg-info-bg px-4 py-3 text-sm text-info-text">
        <SettingsIcon size={16} />
        Changes apply immediately to the running backend for this session (Section 37). DEMO_MODE is currently{" "}
        <strong className="ml-1">{config.demo_mode ? "ON" : "OFF"}</strong>.
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {SECTIONS.map((section) => (
          <Card key={section.title}>
            <CardHeader title={section.title} />
            <div className="space-y-4">
              {section.fields.map((field) => (
                <div key={field.key}>
                  <label className="mb-1 block text-xs font-medium text-ink-muted">{field.label}</label>
                  <input
                    type="number"
                    className="input"
                    step={field.step}
                    min={field.min}
                    max={field.max}
                    value={draft[field.key] ?? ""}
                    onChange={(e) => setDraft((prev) => ({ ...prev, [field.key]: Number(e.target.value) }))}
                  />
                  <p className="mt-1 text-xs text-ink-faint">{field.help}</p>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
