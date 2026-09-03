import { Check, ChevronRight, RefreshCcw, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Card, CardHeader, EmptyState, SkeletonCard } from "../components/Primitives";
import { PageHeader } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import type { RecoveryWorkflow } from "../types";

const STEPS = ["DETECTED", "DIAGNOSING", "RETRAINING", "EVALUATING", "PROMOTED", "DEPLOYED"];
const REJECTED_STEPS = ["DETECTED", "DIAGNOSING", "RETRAINING", "EVALUATING", "REJECTED"];

function StepProgress({ workflow }: { workflow: RecoveryWorkflow }) {
  const completedSteps = new Set(workflow.log.map((entry) => entry.step));
  const failed = workflow.outcome === "REJECTED" || workflow.outcome === "TRAINING_FAILED";
  const steps = failed ? REJECTED_STEPS : STEPS;

  return (
    <div className="flex items-center overflow-x-auto pb-1">
      {steps.map((step, i) => {
        const done = completedSteps.has(step);
        const isLast = i === steps.length - 1;
        const isFailureStep = failed && isLast;
        return (
          <div key={step} className="flex shrink-0 items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-semibold transition-all ${
                  isFailureStep && done
                    ? "border-critical-dot bg-critical-bg text-critical-text"
                    : done
                    ? "border-healthy-dot bg-healthy-bg text-healthy-text"
                    : "border-border bg-surface-muted text-ink-faint"
                }`}
              >
                {done ? isFailureStep ? <X size={14} /> : <Check size={14} /> : i + 1}
              </div>
              <span className={`whitespace-nowrap text-[10px] font-medium ${done ? "text-ink" : "text-ink-faint"}`}>
                {step}
              </span>
            </div>
            {!isLast && (
              <ChevronRight
                size={16}
                className={`mx-1.5 mb-4 shrink-0 ${done && completedSteps.has(steps[i + 1]) ? "text-healthy-dot" : "text-border"}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function Recovery({ refreshKey }: { refreshKey: number }) {
  const [workflows, setWorkflows] = useState<RecoveryWorkflow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .listRecoveryWorkflows()
      .then(setWorkflows)
      .finally(() => setLoading(false));
  }, [refreshKey]);

  if (loading && workflows.length === 0) {
    return (
      <div>
        <PageHeader title="Recovery / Self-Healing" description="Live self-healing workflows and their outcomes" />
        <SkeletonCard />
      </div>
    );
  }

  const active = workflows.filter((w) => w.status !== "COMPLETED" && w.status !== "FAILED");
  const past = workflows.filter((w) => w.status === "COMPLETED" || w.status === "FAILED");

  return (
    <div>
      <PageHeader title="Recovery / Self-Healing" description="Live self-healing workflows and their outcomes" />

      {workflows.length === 0 ? (
        <EmptyState
          title="No recovery workflows yet"
          description="Trigger a failure simulation from the Monitoring page to see the self-healing engine in action."
          icon={<RefreshCcw size={28} />}
        />
      ) : (
        <div className="space-y-4">
          {active.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-muted">Active</p>
              {active.map((w) => (
                <WorkflowCard key={w.id} workflow={w} />
              ))}
            </div>
          )}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-muted">History</p>
            <div className="space-y-3">
              {past.map((w) => (
                <WorkflowCard key={w.id} workflow={w} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function WorkflowCard({ workflow }: { workflow: RecoveryWorkflow }) {
  return (
    <Card className="mb-3">
      <CardHeader
        title={`Recovery #${workflow.id}`}
        subtitle={workflow.trigger}
        action={<StatusBadge label={workflow.outcome || workflow.status} />}
      />
      <StepProgress workflow={workflow} />

      <div className="mt-4 grid grid-cols-2 gap-4 border-t border-border-subtle pt-4 text-sm sm:grid-cols-4">
        <div>
          <p className="text-xs text-ink-muted">Champion</p>
          <p className="font-medium text-ink">{workflow.champion_version || "—"}</p>
          <p className="tabular-nums text-xs text-ink-faint">F1 {workflow.champion_metric?.toFixed(3) ?? "—"}</p>
        </div>
        <div>
          <p className="text-xs text-ink-muted">Challenger</p>
          <p className="font-medium text-ink">{workflow.challenger_version || "—"}</p>
          <p className="tabular-nums text-xs text-ink-faint">F1 {workflow.challenger_metric?.toFixed(3) ?? "—"}</p>
        </div>
        <div>
          <p className="text-xs text-ink-muted">Started</p>
          <p className="font-medium text-ink">{new Date(workflow.started_at).toLocaleTimeString()}</p>
        </div>
        <div>
          <p className="text-xs text-ink-muted">Duration</p>
          <p className="font-medium text-ink">
            {workflow.completed_at
              ? `${Math.round(
                  (new Date(workflow.completed_at).getTime() - new Date(workflow.started_at).getTime()) / 1000
                )}s`
              : "In progress"}
          </p>
        </div>
      </div>

      <details className="mt-3">
        <summary className="cursor-pointer text-xs font-medium text-brand-600 hover:text-brand-700">View detailed log</summary>
        <div className="mt-2 space-y-1.5 border-l-2 border-border pl-4">
          {workflow.log.map((entry, i) => (
            <div key={i} className="text-xs">
              <span className="font-mono font-semibold text-ink-muted">{entry.step}</span>{" "}
              <span className="text-ink-faint">{new Date(entry.timestamp).toLocaleTimeString()}</span>
              <p className="text-ink-muted">{entry.message}</p>
            </div>
          ))}
        </div>
      </details>
    </Card>
  );
}
