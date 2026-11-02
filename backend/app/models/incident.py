from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import BaseModelMixin

class Incident(Base, BaseModelMixin):
    __tablename__ = "incidents"

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    severity = Column(String(32), default="High", index=True)  # Critical, High, Medium, Low
    status = Column(String(64), default="Detected", index=True) 
    # Detected, Investigating, Root Cause Identified, Fix Generated, Validating, Awaiting Approval, Resolved, Failed
    
    affected_services = Column(JSON, default=list)  # ["checkout-service", "payment-service"]
    error_rate = Column(String(32), default="0.00%")
    detection_source = Column(String(64), default="Datadog Alert")
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    root_cause_summary = Column(Text, nullable=True)
    resolution_summary = Column(Text, nullable=True)
    tags = Column(JSON, default=list)

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    deployment_id = Column(String(36), ForeignKey("deployments.id", ondelete="SET NULL"), nullable=True)

    organization = relationship("Organization", back_populates="incidents")
    deployment = relationship("Deployment", back_populates="incidents")
    events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan", order_by="IncidentEvent.created_at")
    logs = relationship("IncidentLog", back_populates="incident", cascade="all, delete-orphan")
    traces = relationship("IncidentTrace", back_populates="incident", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="incident", cascade="all, delete-orphan", order_by="desc(AgentRun.created_at)")
    evidence = relationship("EvidenceItem", back_populates="incident", cascade="all, delete-orphan")
    patches = relationship("Patch", back_populates="incident", cascade="all, delete-orphan")
    reports = relationship("InvestigationReport", back_populates="incident", cascade="all, delete-orphan")

class IncidentEvent(Base, BaseModelMixin):
    __tablename__ = "incident_events"

    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # status_change, agent_dispatched, triage_completed, etc.
    message = Column(Text, nullable=False)
    actor = Column(String(64), default="System")  # System, AgentOps AI, Engineer Name
    event_metadata = Column(JSON, default=dict)

    incident = relationship("Incident", back_populates="events")

class IncidentLog(Base, BaseModelMixin):
    __tablename__ = "incident_logs"

    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    service_name = Column(String(128), nullable=False, index=True)
    level = Column(String(32), default="ERROR", index=True)  # INFO, WARN, ERROR, FATAL
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    log_attributes = Column(JSON, default=dict)

    incident = relationship("Incident", back_populates="logs")

class IncidentTrace(Base, BaseModelMixin):
    __tablename__ = "incident_traces"

    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    trace_id = Column(String(64), nullable=False, index=True)
    span_id = Column(String(64), nullable=False)
    parent_span_id = Column(String(64), nullable=True)
    service_name = Column(String(128), nullable=False)
    operation_name = Column(String(128), nullable=False)
    duration_ms = Column(Float, default=0.0)
    status_code = Column(String(32), default="ERROR")
    error_message = Column(Text, nullable=True)
    trace_metadata = Column(JSON, default=dict)

    incident = relationship("Incident", back_populates="traces")

class Deployment(Base, BaseModelMixin):
    __tablename__ = "deployments"

    service_id = Column(String(36), ForeignKey("services.id", ondelete="CASCADE"), nullable=True)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True)
    commit_sha = Column(String(64), nullable=False, index=True)
    commit_message = Column(Text, nullable=False)
    author = Column(String(128), nullable=False)
    deployed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(32), default="succeeded")  # succeeded, rolled_back, failed
    environment = Column(String(32), default="production")

    service = relationship("Service", back_populates="deployments")
    repository = relationship("Repository", back_populates="deployments")
    incidents = relationship("Incident", back_populates="deployment")
