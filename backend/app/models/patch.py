from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base
from app.models.base import BaseModelMixin

class Patch(Base, BaseModelMixin):
    __tablename__ = "patches"

    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    diff_content = Column(Text, nullable=False)
    affected_files = Column(JSON, default=list)  # ["services/checkout/db.py"]
    regression_tests = Column(Text, nullable=True)
    status = Column(String(32), default="generated")  
    # generated, validating, validated_success, validated_failed, approved, rejected, pr_created
    github_pr_url = Column(String(512), nullable=True)

    incident = relationship("Incident", back_populates="patches")
    validations = relationship("PatchValidation", back_populates="patch", cascade="all, delete-orphan", order_by="desc(PatchValidation.created_at)")
    approvals = relationship("Approval", back_populates="patch", cascade="all, delete-orphan")

class PatchValidation(Base, BaseModelMixin):
    __tablename__ = "patch_validations"

    patch_id = Column(String(36), ForeignKey("patches.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), default="passed")  # passed, failed, timeout, syntax_error, security_violation
    syntax_valid = Column(Boolean, default=True)
    tests_passed = Column(Boolean, default=True)
    total_tests = Column(String(32), default="0")
    passed_tests = Column(String(32), default="0")
    failed_tests = Column(String(32), default="0")
    execution_time_seconds = Column(Float, default=0.0)
    memory_peak_mb = Column(Float, default=0.0)
    stdout_output = Column(Text, nullable=True)
    stderr_output = Column(Text, nullable=True)
    regression_detected = Column(Boolean, default=False)
    validation_summary = Column(Text, nullable=False)

    patch = relationship("Patch", back_populates="validations")

class Approval(Base, BaseModelMixin):
    __tablename__ = "approvals"

    patch_id = Column(String(36), ForeignKey("patches.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(32), nullable=False)  # approved, rejected, modified
    feedback = Column(Text, nullable=True)
    created_pr = Column(Boolean, default=False)
    github_pr_url = Column(String(512), nullable=True)

    patch = relationship("Patch", back_populates="approvals")
    reviewer = relationship("User", back_populates="approvals")
