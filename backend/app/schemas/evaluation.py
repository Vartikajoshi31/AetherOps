from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class BenchmarkIncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    benchmark_id: str
    title: str
    category: str
    service_name: str
    ground_truth_root_cause: str
    ground_truth_culprit_files: List[str] = []
    created_at: str

class EvaluationRunRequest(BaseModel):
    name: str = "Benchmark Evaluation Run"
    model_name: str = "gpt-4o"
    benchmark_categories: Optional[List[str]] = None
    limit: Optional[int] = 10

class EvaluationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    benchmark_id: str
    incident_title: str
    identified_root_cause: str
    ground_truth_root_cause: str
    root_cause_correct: bool
    in_top_3: bool
    retrieval_precision: float
    retrieval_recall: float
    patch_passed_tests: bool
    execution_time_seconds: float
    tokens_consumed: int
    cost_usd: float
    created_at: str

class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    model_name: str
    total_benchmarks: int
    completed_benchmarks: int
    status: str
    root_cause_accuracy: float
    top_3_recall: float
    evidence_retrieval_precision: float
    evidence_retrieval_recall: float
    patch_pass_rate: float
    regression_rate: float
    mean_time_to_diagnosis_seconds: float
    average_tokens_per_incident: int
    average_cost_per_incident_usd: float
    created_at: str
    results: List[EvaluationResultResponse] = []

class DashboardMetricsResponse(BaseModel):
    total_incidents: int
    active_incidents: int
    resolved_incidents: int
    mean_time_to_diagnosis: str
    patch_validation_success_rate: str
    total_ai_investigations_cost_usd: float
    severity_distribution: Dict[str, int]
    service_health: List[Dict[str, Any]]
    incident_trends: List[Dict[str, Any]]
    recent_deployments: List[Dict[str, Any]]
    recent_agent_activity: List[Dict[str, Any]]
