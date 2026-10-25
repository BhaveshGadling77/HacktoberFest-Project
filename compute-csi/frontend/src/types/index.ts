export type RunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'TIMED_OUT';
export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type WorkloadType = 'LOCAL_CPU' | 'REMOTE_GPU';
export type ExecutionMode = 'NORMAL' | 'FAULT_RETRY' | 'DELAY' | 'REPEATED';
export type FaultScenario = 'NONE' | 'FIRST_ATTEMPT_FAIL' | 'TIMEOUT_THEN_RETRY' | 'REPEATED_PROCESSING';
export type FindingType = 'REPEATED_ATTEMPTS' | 'FAILED_ATTEMPTS' | 'DURATION_ANOMALY' | 'ENERGY_ANOMALY' | 'CPU_ANOMALY' | 'MISSING_DATA';

export interface ActivityEvent {
  event_id: string;
  event_type: string;
  activity_name: string;
  attempt: number;
  timestamp: string;
  duration_ms?: number;
  failure_reason?: string;
}

export interface RunSummary {
  run_id: string;
  workflow_id: string;
  status: RunStatus;
  start_time: string;
  duration_seconds?: number;
  attempt_count: number;
  failure_count: number;
}

export interface RunDetail extends RunSummary {
  workload_type: WorkloadType;
  execution_mode: ExecutionMode;
  fault_scenario: FaultScenario;
  end_time?: string;
  outcome?: string;
  timeline: ActivityEvent[];
}

export interface MetricPoint { timestamp: string; value: number; }
export interface MetricSeries {
  name: string;
  unit: string;
  points: MetricPoint[];
  available: boolean;
  unavailability_reason?: string;
}
export interface RunMetrics {
  run_id: string;
  window_start: string;
  window_end: string;
  energy_joules: MetricSeries;
  cpu_percent: MetricSeries;
  memory_mb: MetricSeries;
  raw_available_metrics: string[];
}

export interface EvidenceItem {
  evidence_id: string;
  source: string;
  evidence_type: string;
  timestamp: string;
  run_id: string;
  description: string;
  raw_value?: unknown;
  verified: boolean;
  available: boolean;
}

export interface Finding {
  finding_id: string;
  finding_type: FindingType;
  description: string;
  severity: Severity;
  evidence_refs: string[];
  verified: boolean;
  confidence: number;
  uncertainty_note?: string;
  suggested_action?: string;
}

export interface GemmaAnalysis {
  summary: string;
  possible_causes: string[];
  evidence_explanation: string;
  alternative_explanations: string[];
  recommended_steps: string[];
  uncertainty_note: string;
  is_fallback: boolean;
}

export interface InvestigationReport {
  report_id: string;
  incident_id: string;
  run_id?: string;
  title: string;
  summary: string;
  findings: Finding[];
  evidence: EvidenceItem[];
  gemma_analysis?: GemmaAnalysis;
  overall_confidence: number;
  created_at: string;
  limitations: string[];
}

export interface IncidentSummary {
  incident_id: string;
  run_id?: string;
  title: string;
  severity: Severity;
  status: string;
  finding_types: FindingType[];
  created_at: string;
}

export interface IntegrationStatus {
  connected: boolean;
  error?: string;
  address?: string;
  url?: string;
  endpoint?: string;
  model?: string;
  namespace?: string;
  task_queue?: string;
  instance_url?: string;
  available_metrics?: string[];
  scrape_targets?: { instance: string; up: boolean }[];
}

export interface IntegrationsStatus {
  temporal: IntegrationStatus;
  prometheus: IntegrationStatus;
  kepler: IntegrationStatus;
  gemma: IntegrationStatus;
  jarvislabs: IntegrationStatus;
}

export interface DashboardSummary {
  total_runs: number;
  active_runs: number;
  failed_runs: number;
  detected_incidents: number;
  total_retries: number;
  energy_metrics_available: boolean;
  recent_runs: RunSummary[];
  recent_incidents: IncidentSummary[];
  integration_health: IntegrationsStatus;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages?: number;
  total_pages: number;
}

export interface WorkloadSpec {
  workload_type: WorkloadType;
  execution_mode: ExecutionMode;
  fault_scenario: FaultScenario;
  input_size: number;
  delay_seconds: number;
  max_retries: number;
}

export interface StartRunRequest { workload_spec: WorkloadSpec; }
export interface StartRunResponse { run_id: string; workflow_id: string; status: string; message: string; }
