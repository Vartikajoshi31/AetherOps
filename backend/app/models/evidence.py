from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import BaseModelMixin

class EvidenceItem(Base, BaseModelMixin):
    __tablename__ = "evidence_items"

    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type = Column(String(64), nullable=False) # log, trace, code, git_commit, metric, runbook, documentation
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    raw_content = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=True)
    line_range = Column(String(64), nullable=True)
    confidence = Column(Float, default=1.0)
    is_verified = Column(String(32), default="verified")  # verified, unverified_ai_hypothesis
    evidence_metadata = Column(JSON, default=dict)

    incident = relationship("Incident", back_populates="evidence")

class RetrievedDocument(Base, BaseModelMixin):
    __tablename__ = "retrieved_documents"

    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    query = Column(String(512), nullable=False)
    doc_type = Column(String(64), default="code")  # code, doc, runbook, historical_incident
    repository = Column(String(128), nullable=True)
    file_path = Column(String(512), nullable=False)
    language = Column(String(64), default="python")
    function_name = Column(String(128), nullable=True)
    class_name = Column(String(128), nullable=True)
    commit_sha = Column(String(64), nullable=True)
    chunk_index = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    content = Column(Text, nullable=False)
    source_attribution = Column(JSON, default=dict)
