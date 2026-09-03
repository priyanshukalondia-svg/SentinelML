import clsx from "clsx";
import type { ReactNode } from "react";

type Tone = "healthy" | "warning" | "critical" | "info" | "neutral";

const TONE_CLASSES: Record<Tone, string> = {
  healthy: "bg-healthy-bg border-healthy-border text-healthy-text",
  warning: "bg-warning-bg border-warning-border text-warning-text",
  critical: "bg-critical-bg border-critical-border text-critical-text",
  info: "bg-info-bg border-info-border text-info-text",
  neutral: "bg-neutral-bg border-neutral-border text-neutral-text",
};

const DOT_CLASSES: Record<Tone, string> = {
  healthy: "bg-healthy-dot",
  warning: "bg-warning-dot",
  critical: "bg-critical-dot",
  info: "bg-info-dot",
  neutral: "bg-neutral-dot",
};

const STATE_TONE_MAP: Record<string, Tone> = {
  HEALTHY: "healthy",
  WARNING: "warning",
  CRITICAL: "critical",
  FAILED: "critical",
  TRAINING: "info",
  RUNNING: "info",
  COMPLETED: "healthy",
  TIMEOUT: "warning",
  DEPLOYED: "healthy",
  NOT_DEPLOYED: "neutral",
  CHAMPION: "healthy",
  CHALLENGER: "info",
  CANDIDATE: "neutral",
  REJECTED: "critical",
  ARCHIVED: "neutral",
  NORMAL: "healthy",
  HIGH: "critical",
  OPEN: "critical",
  ACKNOWLEDGED: "warning",
  RESOLVED: "healthy",
  PROMOTED: "healthy",
  DETECTED: "warning",
  DIAGNOSING: "warning",
  RETRAINING: "info",
  EVALUATING: "info",
  ROLLED_BACK: "warning",
};

export function toneForState(state: string): Tone {
  return STATE_TONE_MAP[state] ?? "neutral";
}

export function StatusBadge({
  label,
  tone,
  pulse = false,
  icon,
}: {
  label: string;
  tone?: Tone;
  pulse?: boolean;
  icon?: ReactNode;
}) {
  const resolvedTone = tone ?? toneForState(label);
  return (
    <span className={clsx("badge", TONE_CLASSES[resolvedTone])}>
      {icon ?? <span className={clsx("badge-dot", DOT_CLASSES[resolvedTone], pulse && "animate-pulse-soft")} />}
      {label}
    </span>
  );
}
