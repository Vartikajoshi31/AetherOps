import {
  Incident,
  IncidentDetail,
  DashboardMetrics,
  InvestigationReport,
  Patch,
  EvaluationRun,
  BenchmarkIncident
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(`API Request to ${endpoint} failed (${response.status}): ${errorDetail}`);
  }

  return response.json();
}

export const api = {
  // Metrics & Dashboard
  getMetrics: () => fetchJson<DashboardMetrics>("/api/metrics"),

  // Incidents
  getIncidents: (params?: { status?: string; severity?: string; service?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append("status", params.status);
    if (params?.severity) query.append("severity", params.severity);
    if (params?.service) query.append("service", params.service);
    if (params?.search) query.append("search", params.search);
    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchJson<Incident[]>(`/api/incidents${qs}`);
  },

  getIncidentById: (id: string) => fetchJson<IncidentDetail>(`/api/incidents/${id}`),

  createIncident: (data: {
    title: string;
    description: string;
    severity: string;
    affected_services: string[];
    error_rate?: string;
    detection_source?: string;
    initial_log_message?: string;
    initial_stack_trace?: string;
    tags?: string[];
  }) =>
    fetchJson<Incident>("/api/incidents", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getIncidentReport: (id: string) => fetchJson<InvestigationReport | null>(`/api/incidents/${id}/report`),

  getIncidentPatch: (id: string) => fetchJson<Patch | null>(`/api/incidents/${id}/patch`),

  getIncidentEvidence: (id: string) => fetchJson<any[]>(`/api/incidents/${id}/evidence`),

  approvePatch: (
    incidentId: string,
    data: { action: "approved" | "rejected"; feedback?: string; create_github_pr: boolean }
  ) =>
    fetchJson<any>(`/api/incidents/${incidentId}/approve`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Agent Investigation
  startInvestigation: (incidentId: string, options?: { model_override?: string; max_steps?: number }) =>
    fetchJson<any>(`/api/incidents/${incidentId}/investigate`, {
      method: "POST",
      body: JSON.stringify(options || {}),
    }),

  // Evaluations & Benchmarks
  getBenchmarks: (category?: string) => {
    const qs = category ? `?category=${category}` : "";
    return fetchJson<BenchmarkIncident[]>(`/api/evaluations/benchmarks${qs}`);
  },

  getEvaluationRuns: () => fetchJson<EvaluationRun[]>("/api/evaluations/runs"),

  runEvaluationBenchmark: (data: { name: string; model_name: string; limit?: number }) =>
    fetchJson<EvaluationRun>("/api/evaluations/run", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Repositories
  getRepositories: () => fetchJson<any[]>("/api/repositories"),
  indexRepository: (repoId: string) =>
    fetchJson<any>(`/api/repositories/${repoId}/index`, { method: "POST" }),
};
