import { ListChecks } from "lucide-react";
import { useEffect, useState } from "react";
import { EmptyState, SkeletonCard } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import type { AuditLogEntry } from "../types";

const EVENT_TONE: Record<string, "healthy" | "warning" | "critical" | "info" | "neutral"> = {
  MODEL_TRAINED: "info",
  MODEL_REGISTERED: "info",
  MODEL_PROMOTED: "healthy",
  MODEL_DEPLOYED: "healthy",
  MODEL_REJECTED: "warning",
  DRIFT_DETECTED: "warning",
  RETRAINING_TRIGGERED: "warning",
  ROLLBACK_TRIGGERED: "critical",
  ROLLBACK_COMPLETED: "warning",
  DATA_VALIDATION_FAILED: "critical",
  MODEL_TRAINING_FAILED: "critical",
};

export default function AuditLog({ refreshKey }: { refreshKey: number }) {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  useEffect(() => {
    setLoading(true);
    api
      .getAuditLog()
      .then(setEntries)
      .finally(() => setLoading(false));
  }, [refreshKey]);

  const filtered = entries.filter(
    (e) =>
      query === "" ||
      e.event_type.toLowerCase().includes(query.toLowerCase()) ||
      e.description.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div>
      <PageHeader
        title="Audit Log"
        description="Complete, timestamped history of every major system event"
        action={
          <input
            className="input w-64"
            placeholder="Filter events…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        }
      />

      {loading && entries.length === 0 ? (
        <SkeletonCard />
      ) : filtered.length === 0 ? (
        <EmptyState title="No audit events" description="System events will appear here as they happen." icon={<ListChecks size={28} />} />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-muted text-left text-xs font-semibold uppercase tracking-wide text-ink-muted">
                <th className="px-4 py-3">Event</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3">Dataset</th>
                <th className="px-4 py-3">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e) => (
                <tr key={e.id} className="border-b border-border-subtle last:border-0 hover:bg-surface-muted/60">
                  <td className="px-4 py-3">
                    <StatusBadge label={e.event_type} tone={EVENT_TONE[e.event_type] ?? "neutral"} />
                  </td>
                  <td className="max-w-md px-4 py-3 text-ink">{e.description}</td>
                  <td className="px-4 py-3 text-ink-muted">{e.model_version ?? "—"}</td>
                  <td className="px-4 py-3 text-ink-muted">{e.dataset_version ?? "—"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-ink-muted">{new Date(e.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
