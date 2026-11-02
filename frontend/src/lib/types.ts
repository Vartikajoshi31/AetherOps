export type IncidentSeverity = "Critical" | "High" | "Medium" | "Low";

export type IncidentStatus =
  | "Detected"
  | "Investigating"
  | "Root Cause Identified"
  | "Fix Generated"
  | "Validating"
  | "Awaiting Approval"
  | "Resolved"
  | "Failed";

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  affected_services: string[];
  error_rate: string;
  detection_source: string;
  tags: string[];
  start_time: string;
  resolved_at: string | null;
  root_cause_summary?: string | null;
  resolution_summary?: string | null;
  created_at: string;
  updated_at: string;
  events_count: number;
  logs_count: number;
  traces_count: number;
  patches_count: number;
}

export interface IncidentEvent {
  id: string;
  incident_id: string;
  event_type: string;
  message: string;
  actor: string;
  event_metadata: Record<string, any>;
  created_at: string;
}

export interface IncidentLog {
  id: string;
  incident_id: string;
  service_name: string;
  level: "INFO" | "WARN" | "ERROR" | "FATAL";
  timestamp: string;
  message: string;
  stack_trace?: string | null;
  log_attributes: Record<string, any>;
}

export interface IncidentTrace {
  id: string;
  incident_id: string;
  trace_id: string;
  span_id: string;
  parent_span_id?: string | null;
  service_name: string;
  operation_name: string;
  duration_ms: number;
  status_code: string;
  error_message?: string | null;
  trace_metadata: Record<string, any>;
}

export interface IncidentDetail extends Incident {
  events: IncidentEvent[];
  logs: IncidentLog[];
  traces: IncidentTrace[];
}

export interface PatchValidation {
  id: string;
  patch_id: string;
  status: "passed" | "failed" | "timeout" | "syntax_error" | "security_violation";
  syntax_valid: boolean;
  tests_passed: boolean;
  total_tests: string;
  passed_tests: string;
  failed_tests: string;
  execution_time_seconds: number;
  memory_peak_mb: number;
  stdout_output?: string | null;
  stderr_output?: string | null;
  regression_detected: boolean;
  validation_summary: string;
  created_at: string;
}

export interface Patch {
  id: string;
  incident_id: string;
  run_id?: string | null;
  title: string;
  explanation: string;
  diff_content: string;
  affected_files: string[];
  regression_tests?: string | null;
  status: string;
  github_pr_url?: string | null;
  created_at: string;
  validations: PatchValidation[];
}

export interface InvestigationReport {
  id: string;
  incident_id: string;
  run_id?: string | null;
  title: string;
  executive_summary: string;
  severity_assessment: string;
  affected_services_summary: string[];
  timeline_chronology: Record<string, any>[];
  error_patterns: Record<string, any>[];
  relevant_logs_summary?: string | null;
  related_code_summary?: string | null;
  primary_root_cause: string;
  confidence_score: number;
  confidence_rationale?: string | null;
  missing_information: string[];
  regression_risks: string[];
  recommended_next_steps: string[];
  status: string;
  created_at: string;
}

export interface AgentEvent {
  id: string;
  run_id: string;
  agent_name: string;
  event_type: string;
  message: string;
  tool_name?: string | null;
  tool_input?: Record<string, any> | null;
  tool_output?: Record<string, any> | null;
  step_index: number;
  duration_ms: number;
  tokens_used: number;
  created_at: string;
}

export interface RootCauseHypothesis {
  id: string;
  run_id: string;
  incident_id: string;
  title: string;
  explanation: string;
  confidence_score: number;
  rank: number;
  is_primary: boolean;
  supporting_evidence: Record<string, any>[];
  counter_evidence: Record<string, any>[];
  created_at: string;
}

export interface AgentRun {
  id: string;
  incident_id: string;
  workflow_name: string;
  status: string;
  current_agent: string;
  step_count: number;
  total_tokens_used: number;
  estimated_cost_usd: number;
  started_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  events: AgentEvent[];
  hypotheses: RootCauseHypothesis[];
  report?: InvestigationReport | null;
}

export interface ServiceHealth {
  id: string;
  name: string;
  tier: string;
  language: string;
  health_status: "healthy" | "degraded" | "critical";
  error_rate: string;
}

export interface DashboardMetrics {
  total_incidents: number;
  active_incidents: number;
  resolved_incidents: number;
  mean_time_to_diagnosis: string;
  patch_validation_success_rate: string;
  total_ai_investigations_cost_usd: number;
  severity_distribution: Record<IncidentSeverity, number>;
  service_health: ServiceHealth[];
  incident_trends: { date: string; incidents: number; resolved: number }[];
  recent_deployments: {
    id: string;
    commit_sha: string;
    commit_message: string;
    author: string;
    deployed_at: string;
    status: string;
    environment: string;
  }[];
  recent_agent_activity: {
    id: string;
    agent_name: string;
    event_type: string;
    message: string;
    step_index: number;
    duration_ms: number;
    created_at: string;
  }[];
}

export interface BenchmarkIncident {
  id: string;
  benchmark_id: string;
  title: string;
  category: string;
  service_name: string;
  ground_truth_root_cause: string;
  ground_truth_culprit_files: string[];
  created_at: string;
}

export interface EvaluationResult {
  id: string;
  benchmark_id: string;
  incident_title: string;
  identified_root_cause: string;
  ground_truth_root_cause: string;
  root_cause_correct: boolean;
  in_top_3: boolean;
  retrieval_precision: number;
  retrieval_recall: number;
  patch_passed_tests: boolean;
  execution_time_seconds: number;
  tokens_consumed: number;
  cost_usd: number;
  created_at: string;
}

export interface EvaluationRun {
  id: string;
  name: string;
  model_name: string;
  total_benchmarks: number;
  completed_benchmarks: number;
  status: string;
  root_cause_accuracy: number;
  top_3_recall: number;
  evidence_retrieval_precision: number;
  evidence_retrieval_recall: number;
  patch_pass_rate: number;
  regression_rate: number;
  mean_time_to_diagnosis_seconds: number;
  average_tokens_per_incident: number;
  average_cost_per_incident_usd: number;
  created_at: string;
  results: EvaluationResult[];
}
