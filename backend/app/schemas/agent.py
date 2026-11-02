from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class InvestigationStartRequest(BaseModel):
    model_override: Optional[str] = None
    max_steps: Optional[int] = 15
    auto_generate_fix: bool = True
    auto_validate_patch: bool = True

class AgentEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    agent_name: str
    event_type: str
    message: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    step_index: int
    duration_ms: float
    tokens_used: int
    created_at: str

class RootCauseHypothesisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    incident_id: str
    title: str
    explanation: str
    confidence_score: float
    rank: int
    is_primary: bool
    supporting_evidence: List[Dict[str, Any]] = []
    counter_evidence: List[Dict[str, Any]] = []
    created_at: str

class InvestigationReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    run_id: Optional[str] = None
    title: str
    executive_summary: str
    severity_assessment: str
    affected_services_summary: List[str] = []
    timeline_chronology: List[Dict[str, Any]] = []
    error_patterns: List[Dict[str, Any]] = []
    relevant_logs_summary: Optional[str] = None
    related_code_summary: Optional[str] = None
    primary_root_cause: str
    confidence_score: float
    confidence_rationale: Optional[str] = None
    missing_information: List[str] = []
    regression_risks: List[str] = []
    recommended_next_steps: List[str] = []
    status: str
    created_at: str

class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    workflow_name: str
    status: str
    current_agent: str
    step_count: int
    total_tokens_used: int
    estimated_cost_usd: float
    started_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    events: List[AgentEventResponse] = []
    hypotheses: List[RootCauseHypothesisResponse] = []
    report: Optional[InvestigationReportResponse] = None
