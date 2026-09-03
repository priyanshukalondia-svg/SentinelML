import {
  Activity,
  AlertTriangle,
  Beaker,
  Database,
  LayoutDashboard,
  ListChecks,
  RefreshCcw,
  Settings as SettingsIcon,
  ShieldCheck,
} from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import clsx from "clsx";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/models", label: "Models", icon: ShieldCheck },
  { to: "/experiments", label: "Experiments", icon: Beaker },
  { to: "/datasets", label: "Datasets", icon: Database },
  { to: "/monitoring", label: "Monitoring", icon: Activity },
  { to: "/alerts", label: "Alerts", icon: AlertTriangle },
  { to: "/recovery", label: "Recovery", icon: RefreshCcw },
  { to: "/audit", label: "Audit Log", icon: ListChecks },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

export function AppShell({
  children,
  connected,
  activeModel,
}: {
  children: ReactNode;
  connected: boolean;
  activeModel?: string | null;
}) {
  return (
    <div className="flex min-h-screen bg-canvas">
      <aside className="fixed inset-y-0 left-0 z-20 flex w-60 flex-col border-r border-border bg-surface">
        <div className="flex items-center gap-2.5 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
            S
          </div>
          <div>
            <p className="text-sm font-bold leading-none text-ink">SentinelML</p>
            <p className="mt-1 text-[11px] leading-none text-ink-faint">Self-Healing MLOps</p>
          </div>
        </div>

        <nav className="flex-1 space-y-0.5 px-3">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => (isActive ? "nav-link-active" : "nav-link")}>
              <Icon size={17} strokeWidth={2} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border p-4">
          <div className="flex items-center gap-2 rounded-lg bg-surface-muted px-3 py-2">
            <span
              className={clsx(
                "h-2 w-2 rounded-full",
                connected ? "animate-pulse-soft bg-healthy-dot" : "bg-critical-dot"
              )}
            />
            <span className="text-xs font-medium text-ink-muted">{connected ? "Live" : "Reconnecting…"}</span>
          </div>
          {activeModel && (
            <p className="mt-2 truncate px-1 text-[11px] text-ink-faint">
              Active model: <span className="font-medium text-ink-muted">{activeModel}</span>
            </p>
          )}
        </div>
      </aside>

      <main className="ml-60 flex-1">
        <div className="mx-auto max-w-7xl px-8 py-8">{children}</div>
      </main>
    </div>
  );
}

export function PageHeader({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-xl font-bold text-ink">{title}</h1>
        {description && <p className="mt-1 text-sm text-ink-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}
