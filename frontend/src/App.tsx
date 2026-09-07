import { useCallback, useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ToastProvider, useToast } from "./components/Toast";
import { useLiveEvents } from "./hooks/useLiveEvents";
import { api } from "./services/api";
import type { WSEvent } from "./types";

import Overview from "./pages/Overview";
import Models from "./pages/Models";
import ModelDetail from "./pages/ModelDetail";
import Experiments from "./pages/Experiments";
import Datasets from "./pages/Datasets";
import Monitoring from "./pages/Monitoring";
import Alerts from "./pages/Alerts";
import Recovery from "./pages/Recovery";
import AuditLog from "./pages/AuditLog";
import Settings from "./pages/Settings";

function AppInner() {
  const { push } = useToast();
  const [activeModel, setActiveModel] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleEvent = useCallback(
    (event: WSEvent) => {
      // Bump a global refresh key so any page can react to relevant events
      // without every page needing its own websocket subscription.
      setRefreshKey((k) => k + 1);

      switch (event.type) {
        case "alert":
          push({
            tone: event.payload.severity === "CRITICAL" ? "error" : event.payload.severity === "WARNING" ? "warning" : "info",
            title: event.payload.title,
            description: event.payload.description,
          });
          break;
        case "model_promoted":
          push({ tone: "success", title: "Challenger promoted", description: `${event.payload.version} is now the champion.` });
          setActiveModel(event.payload.version);
          break;
        case "rollback_completed":
          push({
            tone: "warning",
            title: "Automatic rollback completed",
            description: `Restored ${event.payload.restored_version}.`,
          });
          setActiveModel(event.payload.restored_version);
          break;
        case "training_failed":
          push({ tone: "error", title: "Training failed", description: event.payload.error });
          break;
        default:
          break;
      }
    },
    [push]
  );

  const { connected } = useLiveEvents(handleEvent);

  useEffect(() => {
    api
      .getMonitoringOverview()
      .then((overview) => setActiveModel(overview.active_model))
      .catch(() => {});
  }, []);

  return (
    <AppShell connected={connected} activeModel={activeModel}>
      <Routes>
        <Route path="/" element={<Datasets refreshKey={refreshKey} />} />
        <Route path="/models" element={<Models refreshKey={refreshKey} />} />
        <Route path="/models/:id" element={<ModelDetail />} />
        <Route path="/experiments" element={<Experiments refreshKey={refreshKey} />} />
        <Route path="/datasets" element={<Datasets refreshKey={refreshKey} />} />
        <Route path="/monitoring" element={<Monitoring refreshKey={refreshKey} />} />
        <Route path="/alerts" element={<Alerts refreshKey={refreshKey} />} />
        <Route path="/recovery" element={<Recovery refreshKey={refreshKey} />} />
        <Route path="/audit" element={<AuditLog refreshKey={refreshKey} />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </AppShell>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppInner />
    </ToastProvider>
  );
}
