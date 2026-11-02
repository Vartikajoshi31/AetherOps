from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class IncidentBase(BaseModel):
    title: str = Field(..., example="Checkout Service Connection Pool Exhaustion")
    description: str = Field(..., example="HTTP 500 error spike in checkout-service during payment processing")
    severity: str = Field("High", example="High")  # Critical, High, Medium, Low
    affected_services: List[str] = Field(default_factory=list, example=["checkout-service", "order-service"])
    error_rate: str = Field("0.00%", example="34.8%")
    detection_source: str = Field("Datadog Alert", example="Prometheus / AlertManager")
    tags: List[str] = Field(default_factory=list)

class IncidentCreate(IncidentBase):
    initial_log_message: Optional[str] = None
    initial_stack_trace: Optional[str] = None

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    error_rate: Optional[str] = None
    root_cause_summary: Optional[str] = None
    resolution_summary: Optional[str] = None
    tags: Optional[List[str]] = None

class IncidentEventResponse(BaseModel):
    id: str
    incident_id: str
    event_type: str
    message: str
    actor: str
    event_metadata: Dict[str, Any] = {}
    created_at: str

    class Config:
        from_attributes = True

class IncidentLogResponse(BaseModel):
    id: str
    incident_id: str
    service_name: str
    level: str
    timestamp: str
    message: str
    stack_trace: Optional[str] = None
    log_attributes: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class IncidentTraceResponse(BaseModel):
    id: str
    incident_id: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    service_name: str
    operation_name: str
    duration_ms: float
    status_code: str
    error_message: Optional[str] = None
    trace_metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class IncidentResponse(IncidentBase):
    id: str
    status: str
    start_time: str
    resolved_at: Optional[str] = None
    root_cause_summary: Optional[str] = None
    resolution_summary: Optional[str] = None
    created_at: str
    updated_at: str
    events_count: int = 0
    logs_count: int = 0
    traces_count: int = 0
    patches_count: int = 0

    class Config:
        from_attributes = True

class IncidentDetailResponse(IncidentResponse):
    events: List[IncidentEventResponse] = []
    logs: List[IncidentLogResponse] = []
    traces: List[IncidentTraceResponse] = []
