import { BellOff, Check } from "lucide-react";
import { useEffect, useState } from "react";
import { Card, EmptyState, SkeletonCard } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import { useToast } from "../components/Toast";
import type { Alert } from "../types";

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function Alerts({ refreshKey }: { refreshKey: number }) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"ALL" | "OPEN">("ALL");
  const { push } = useToast();

  function load() {
    setLoading(true);
    api
      .listAlerts()
      .then(setAlerts)
      .finally(() => setLoading(false));
  }

  useEffect(load, [refreshKey]);

  async function handleResolve(id: number) {
    try {
      await api.resolveAlert(id);
      load();
    } catch (err: any) {
      push({ tone: "error", title: "Failed to resolve alert", description: err.message });
    }
  }

  async function handleAck(id: number) {
    try {
      await api.acknowledgeAlert(id);
      load();
    } catch (err: any) {
      push({ tone: "error", title: "Failed to acknowledge alert", description: err.message });
    }
  }

  const visible = filter === "OPEN" ? alerts.filter((a) => a.state === "OPEN") : alerts;

  return (
    <div>
      <PageHeader
        title="Alert Center"
        description="System alerts and recovery events"
        action={
          <div className="flex gap-1 rounded-lg border border-border bg-surface p-1">
            {(["ALL", "OPEN"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                  filter === f ? "bg-brand-600 text-white" : "text-ink-muted hover:bg-surface-muted"
                }`}
              >
                {f === "ALL" ? "All" : "Open"}
              </button>
            ))}
          </div>
        }
      />

      {loading && alerts.length === 0 ? (
        <div className="grid gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : visible.length === 0 ? (
        <EmptyState title="No alerts" description="Everything is quiet right now." icon={<BellOff size={28} />} />
      ) : (
        <div className="space-y-2">
          {visible.map((a) => (
            <Card key={a.id} className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <StatusBadge
                  label={a.severity}
                  tone={a.severity === "CRITICAL" ? "critical" : a.severity === "WARNING" ? "warning" : a.severity === "RESOLVED" ? "healthy" : "info"}
                />
                <div>
                  <p className="text-sm font-semibold text-ink">{a.title}</p>
                  <p className="mt-0.5 text-sm text-ink-muted">{a.description}</p>
                  <p className="mt-1 text-xs text-ink-faint">
                    {timeAgo(a.created_at)} · source: {a.source} · <StatusBadge label={a.state} />
                  </p>
                </div>
              </div>
              {a.state === "OPEN" && (
                <div className="flex shrink-0 gap-2">
                  <button className="btn-secondary py-1.5 text-xs" onClick={() => handleAck(a.id)}>
                    Acknowledge
                  </button>
                  <button className="btn-primary py-1.5 text-xs" onClick={() => handleResolve(a.id)}>
                    <Check size={13} /> Resolve
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
