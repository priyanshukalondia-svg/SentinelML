export type ValidationStatus = "HEALTHY" | "WARNING" | "FAILED";
export type HealthStatus = "HEALTHY" | "WARNING" | "CRITICAL";
export type AlertSeverity = "CRITICAL" | "WARNING" | "INFO" | "RESOLVED";
export type AlertState = "OPEN" | "ACKNOWLEDGED" | "RESOLVED";
export type ModelState = "CANDIDATE" | "CHAMPION" | "CHALLENGER" | "ARCHIVED" | "REJECTED";
export type RunStatus = "RUNNING" | "COMPLETED" | "FAILED" | "TIMEOUT";

export interface Dataset {
  id: number;
  dataset_id: string;
  version: string;
  file_name: string;
  row_count: number;
  feature_count: number;
  target_column: string;
  validation_status: ValidationStatus;
  is_reference: boolean;
  quality_report: Record<string, any>;
  created_at: string;
}

export interface TrainingRun {
  id: number;
  run_group_id: string;
  model_type: string;
  status: RunStatus;
  mlflow_run_id: string;
  params: Record<string, any>;
  metrics: Record<string, number>;
  error_message: string;
  triggered_by: string;
  started_at: string;
  completed_at: string | null;
}

export interface ModelVersion {
  id: number;
  model_name: string;
  version: string;
  dataset_version: string;
  metrics: Record<string, number>;
  state: ModelState;
  deployment_status: "NOT_DEPLOYED" | "DEPLOYED";
  git_commit: string;
  created_at: string;
}

export interface DriftFeature {
  feature: string;
  drift_score: number;
  status: "NORMAL" | "WARNING" | "HIGH";
}

export interface DriftReport {
  method: string;
  overall_status: "NORMAL" | "WARNING" | "CRITICAL";
  features: DriftFeature[];
  computed_at: string;
}

export interface PerformanceReport {
  baseline_f1: number | null;
  current_f1: number | null;
  degradation_pct: number | null;
  sample_size: number;
  computed_at: string;
}

export interface HealthScore {
  overall: number;
  performance: number;
  data_quality: number;
  drift: number;
  latency: number;
  errors: number;
  status: HealthStatus;
  computed_at: string;
}

export interface MonitoringOverview {
  active_model: string | null;
  health: HealthScore;
  drift: DriftReport;
  performance: PerformanceReport;
  avg_latency_ms: number;
  prediction_volume: number;
}

export interface Alert {
  id: number;
  severity: AlertSeverity;
  title: string;
  description: string;
  source: string;
  state: AlertState;
  created_at: string;
  resolved_at: string | null;
}

export interface AuditLogEntry {
  id: number;
  event_type: string;
  description: string;
  status: string;
  model_version: string | null;
  dataset_version: string | null;
  timestamp: string;
}

export interface RecoveryStep {
  step: string;
  message: string;
  timestamp: string;
}

export interface RecoveryWorkflow {
  id: number;
  trigger: string;
  status: string;
  champion_version: string;
  challenger_version: string;
  champion_metric: number | null;
  challenger_metric: number | null;
  outcome: string;
  log: RecoveryStep[];
  started_at: string;
  completed_at: string | null;
}

export interface WSEvent<T = any> {
  type: string;
  payload: T;
  timestamp: string;
}
