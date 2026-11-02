from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel, Field

class InvestigationEvent(BaseModel):
    agent_name: str
    stage: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str

class TriageOutput(BaseModel):
    category: str
    primary_service: str
    impacted_services: List[str]
    severity: str
    priority_level: str
    summary: str
    recommended_investigation_steps: List[str]
    confidence_score: float

class LogAnalysisOutput(BaseModel):
    recurring_error_patterns: List[str]
    error_frequency: int
    culprit_module: Optional[str] = None
    culprit_line: Optional[int] = None
    stack_trace_snippet: Optional[str] = None
    anomaly_summary: str
    extracted_evidence: List[Dict[str, Any]]

class CodeInvestigationOutput(BaseModel):
    culprit_file: str
    culprit_function: str
    culprit_lines: str
    vulnerability_explanation: str
    code_snippet: str
    retrieved_chunks_count: int
    supporting_evidence: List[Dict[str, Any]]
    confidence: float

class HypothesisItem(BaseModel):
    title: str
    description: str
    probability: float
    supporting_evidence: List[str]
    contradicting_evidence: List[str] = Field(default_factory=list)

class RootCauseOutput(BaseModel):
    primary_hypothesis: str
    explanation: str
    architectural_flaw: str
    confidence_score: float
    ranked_hypotheses: List[HypothesisItem]
    missing_evidence: List[str] = Field(default_factory=list)

class FixOutput(BaseModel):
    affected_file: str
    diff: str
    explanation: str
    regression_risk: str
    test_code: str
    lines_added: int
    lines_removed: int

class ValidationOutput(BaseModel):
    syntax_valid: bool
    tests_passed: bool
    tests_run: int
    test_failures: int
    stdout: str
    stderr: str
    duration_seconds: float
    summary: str

class ReviewOutput(BaseModel):
    approved_for_human_review: bool
    safety_verdict: str  # Safe, Warning, Unsafe
    evidence_quality_score: float
    uncertainty_summary: str
    recommendation: str
    executive_summary: str

class InvestigationState(TypedDict, total=False):
    incident_id: str
    title: str
    description: str
    severity: str
    affected_services: List[str]
    error_rate: str
    detection_source: str
    logs: List[Dict[str, Any]]
    traces: List[Dict[str, Any]]
    repo_path: str

    # Agent Step Outputs
    triage_result: Optional[Dict[str, Any]]
    log_analysis_result: Optional[Dict[str, Any]]
    code_investigation_result: Optional[Dict[str, Any]]
    root_cause_analysis: Optional[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    evidence_items: List[Dict[str, Any]]
    retrieved_documents: List[Dict[str, Any]]
    proposed_patch: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    review_result: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]

    # Workflow Orchestration Controls
    retry_count: int
    max_retries: int
    current_stage: str
    status: str
    agent_events: List[Dict[str, Any]]
    total_tokens: int
    total_cost: float
    error: Optional[str]
