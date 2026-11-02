from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, Boolean, DateTime, ForeignKey, JSON
from app.database.session import Base
from app.models.base import BaseModelMixin

class BenchmarkIncident(Base, BaseModelMixin):
    __tablename__ = "benchmark_incidents"

    benchmark_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False) # concurrency, database, network_timeout, memory_leak, auth, cache, npe
    service_name = Column(String(128), nullable=False)
    ground_truth_root_cause = Column(Text, nullable=False)
    ground_truth_culprit_files = Column(JSON, default=list)
    ground_truth_patch_diff = Column(Text, nullable=True)
    simulated_logs = Column(JSON, default=list)
    simulated_traces = Column(JSON, default=list)
    test_verification_command = Column(String(255), default="pytest")

class EvaluationRun(Base, BaseModelMixin):
    __tablename__ = "evaluation_runs"

    name = Column(String(128), nullable=False)
    model_name = Column(String(64), default="gpt-4o")
    total_benchmarks = Column(Integer, default=0)
    completed_benchmarks = Column(Integer, default=0)
    status = Column(String(32), default="completed")  # running, completed, failed
    
    # Aggregated metrics
    root_cause_accuracy = Column(Float, default=0.0) # 0.0 - 1.0
    top_3_recall = Column(Float, default=0.0)
    evidence_retrieval_precision = Column(Float, default=0.0)
    evidence_retrieval_recall = Column(Float, default=0.0)
    patch_pass_rate = Column(Float, default=0.0)
    regression_rate = Column(Float, default=0.0)
    mean_time_to_diagnosis_seconds = Column(Float, default=0.0)
    average_tokens_per_incident = Column(Integer, default=0)
    average_cost_per_incident_usd = Column(Float, default=0.0)
    evaluation_metadata = Column(JSON, default=dict)

class EvaluationResult(Base, BaseModelMixin):
    __tablename__ = "evaluation_results"

    run_id = Column(String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    benchmark_id = Column(String(64), nullable=False, index=True)
    incident_title = Column(String(255), nullable=False)
    identified_root_cause = Column(Text, nullable=False)
    ground_truth_root_cause = Column(Text, nullable=False)
    root_cause_correct = Column(Boolean, default=False)
    in_top_3 = Column(Boolean, default=False)
    retrieval_precision = Column(Float, default=0.0)
    retrieval_recall = Column(Float, default=0.0)
    patch_passed_tests = Column(Boolean, default=False)
    execution_time_seconds = Column(Float, default=0.0)
    tokens_consumed = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    details = Column(JSON, default=dict)

class UsageMetric(Base, BaseModelMixin):
    __tablename__ = "usage_metrics"

    metric_type = Column(String(64), nullable=False, index=True)  # llm_tokens, llm_cost, agent_duration, patch_validation
    service_name = Column(String(128), nullable=True)
    incident_id = Column(String(36), nullable=True, index=True)
    run_id = Column(String(36), nullable=True)
    metric_value = Column(Float, default=0.0)
    unit = Column(String(32), default="count")  # count, usd, seconds, bytes
    metric_attributes = Column(JSON, default=dict)
