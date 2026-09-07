const configuredApiBaseUrl = (import.meta as any).env?.VITE_API_BASE_URL?.trim();
const API_BASE_URL: string = configuredApiBaseUrl || (
  (import.meta as any).env?.PROD
    ? "https://sentinelml-api.onrender.com/api/v1"
    : "http://127.0.0.1:8000/api/v1"
);

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    let body: any = {};
    try {
      body = await res.json();
    } catch {
      // no-op — some errors won't have a JSON body
    }
    throw new ApiError(res.status, body.error || "UNKNOWN_ERROR", body.message || res.statusText);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Datasets
  listDatasets: () => request<import("../types").Dataset[]>("/datasets"),
  getDataset: (id: number) => request<import("../types").Dataset>(`/datasets/${id}`),
  uploadDataset: (file: File, targetColumn: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("target_column", targetColumn);
    return request<import("../types").Dataset>("/datasets/upload", { method: "POST", body: form });
  },

  // Training
  startTraining: (datasetId: number, models: string[]) =>
    request<import("../types").TrainingRun[]>("/training/start", {
      method: "POST",
      body: JSON.stringify({ dataset_id: datasetId, models, triggered_by: "manual" }),
    }),
  listTrainingRuns: () => request<import("../types").TrainingRun[]>("/training"),

  // Models
  listModels: () => request<import("../types").ModelVersion[]>("/models"),
  getModel: (id: number) => request<import("../types").ModelVersion>(`/models/${id}`),
  getModelLineage: (id: number) => request<any>(`/models/${id}/lineage`),
  deployModel: (id: number) => request<import("../types").ModelVersion>(`/models/${id}/deploy`, { method: "POST" }),
  rollbackModel: (id: number) => request<import("../types").ModelVersion>(`/models/${id}/rollback`, { method: "POST" }),

  // Prediction
  predict: (features: Record<string, number>) =>
    request<{ prediction: number; probability: number; model_version: string; latency_ms: number }>("/predict", {
      method: "POST",
      body: JSON.stringify({ features }),
    }),

  // Monitoring
  getMonitoringOverview: () => request<import("../types").MonitoringOverview>("/monitoring/overview"),
  getDrift: (method: string = "psi") => request<import("../types").DriftReport>(`/monitoring/drift?method=${method}`),
  getPerformance: () => request<import("../types").PerformanceReport>("/monitoring/performance"),

  // Alerts
  listAlerts: () => request<import("../types").Alert[]>("/alerts"),
  acknowledgeAlert: (id: number) => request<import("../types").Alert>(`/alerts/${id}/acknowledge`, { method: "POST" }),
  resolveAlert: (id: number) => request<import("../types").Alert>(`/alerts/${id}/resolve`, { method: "POST" }),

  // Audit + recovery
  getAuditLog: () => request<import("../types").AuditLogEntry[]>("/audit-log"),
  listRecoveryWorkflows: () => request<import("../types").RecoveryWorkflow[]>("/recovery"),
  getRecoveryWorkflow: (id: number) => request<import("../types").RecoveryWorkflow>(`/recovery/${id}`),

  // Simulation
  simulateDrift: () => request<{ message: string; recovery_workflow_id: number | null }>("/simulation/drift", { method: "POST" }),
  simulateDegradation: () =>
    request<{ message: string; recovery_workflow_id: number | null }>("/simulation/degradation", { method: "POST" }),
  simulateLatency: () =>
    request<{ message: string; recovery_workflow_id: number | null }>("/simulation/latency", { method: "POST" }),
  simulateErrors: () =>
    request<{ message: string; recovery_workflow_id: number | null }>("/simulation/errors", { method: "POST" }),

  // Health
  getHealth: () => fetch(`${API_BASE_URL.replace(/\/api\/v1$/, "")}/health`).then((r) => r.json()),

  // Config
  getConfig: () => request<any>("/config"),
  updateConfig: (patch: Record<string, number>) =>
    request<any>("/config", { method: "PATCH", body: JSON.stringify(patch) }),
};

const configuredWsUrl = (import.meta as any).env?.VITE_WS_URL?.trim();
export const WS_URL: string = configuredWsUrl || `${API_BASE_URL.replace(/^http/, "ws")}/ws/events`;
