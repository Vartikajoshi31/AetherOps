from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import BaseModelMixin

class AgentRun(Base, BaseModelMixin):
    __tablename__ = "agent_runs"

    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_name = Column(String(128), default="AutonomousIncidentInvestigatorWorkflow")
    status = Column(String(64), default="running", index=True) 
    # pending, running, paused_awaiting_approval, completed, failed, cancelled
    current_agent = Column(String(64), default="triage")
    step_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    graph_state = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    incident = relationship("Incident", back_populates="agent_runs")
    events = relationship("AgentEvent", back_populates="agent_run", cascade="all, delete-orphan", order_by="AgentEvent.created_at")
    hypotheses = relationship("RootCauseHypothesis", back_populates="agent_run", cascade="all, delete-orphan")
    reports = relationship("InvestigationReport", back_populates="agent_run", cascade="all, delete-orphan")

class AgentEvent(Base, BaseModelMixin):
    __tablename__ = "agent_events"

    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(64), nullable=False, index=True) 
    # triage, log_analysis, code_investigation, root_cause, fix_generation, validation, review
    event_type = Column(String(64), nullable=False)
    # agent_start, tool_call, tool_result, reasoning_summary, decision, state_change, agent_finish, error
    message = Column(Text, nullable=False)
    tool_name = Column(String(128), nullable=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)
    step_index = Column(Integer, default=0)
    duration_ms = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)

    agent_run = relationship("AgentRun", back_populates="events")

class RootCauseHypothesis(Base, BaseModelMixin):
    __tablename__ = "root_cause_hypotheses"

    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    rank = Column(Integer, default=1)
    is_primary = Column(Boolean, default=False)
    supporting_evidence = Column(JSON, default=list)
    counter_evidence = Column(JSON, default=list)

    agent_run = relationship("AgentRun", back_populates="hypotheses")

class InvestigationReport(Base, BaseModelMixin):
    __tablename__ = "investigation_reports"

    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    executive_summary = Column(Text, nullable=False)
    severity_assessment = Column(String(32), default="High")
    affected_services_summary = Column(JSON, default=list)
    timeline_chronology = Column(JSON, default=list)
    error_patterns = Column(JSON, default=list)
    relevant_logs_summary = Column(Text, nullable=True)
    related_code_summary = Column(Text, nullable=True)
    primary_root_cause = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.85)
    confidence_rationale = Column(Text, nullable=True)
    missing_information = Column(JSON, default=list)
    regression_risks = Column(JSON, default=list)
    recommended_next_steps = Column(JSON, default=list)
    status = Column(String(32), default="final")

    incident = relationship("Incident", back_populates="reports")
    agent_run = relationship("AgentRun", back_populates="reports")
