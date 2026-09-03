import clsx from "clsx";
import type { ReactNode } from "react";

export function Card({
  children,
  className,
  hoverable = false,
}: {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
}) {
  return <div className={clsx("card", hoverable && "card-hover", "p-5", className)}>{children}</div>;
}

export function CardHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="mb-4 flex items-start justify-between gap-4">
      <div>
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        {subtitle && <p className="mt-0.5 text-xs text-ink-muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function MetricStat({
  label,
  value,
  suffix,
  tone = "default",
}: {
  label: string;
  value: string | number;
  suffix?: string;
  tone?: "default" | "healthy" | "warning" | "critical";
}) {
  const toneClass =
    tone === "healthy"
      ? "text-healthy-text"
      : tone === "warning"
      ? "text-warning-text"
      : tone === "critical"
      ? "text-critical-text"
      : "text-ink";
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">{label}</p>
      <p className={clsx("mt-1 tabular-nums text-2xl font-bold", toneClass)}>
        {value}
        {suffix && <span className="ml-1 text-sm font-medium text-ink-muted">{suffix}</span>}
      </p>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-surface-muted/50 px-6 py-14 text-center animate-fade-in">
      {icon && <div className="mb-3 text-ink-faint">{icon}</div>}
      <p className="text-sm font-semibold text-ink">{title}</p>
      {description && <p className="mt-1 max-w-sm text-sm text-ink-muted">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("skeleton", className)} />;
}

export function SkeletonCard() {
  return (
    <Card>
      <Skeleton className="mb-3 h-4 w-24" />
      <Skeleton className="h-8 w-32" />
    </Card>
  );
}
