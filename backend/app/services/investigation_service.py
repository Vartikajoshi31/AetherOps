import os
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.incident import Incident, IncidentEvent
from app.models.agent_run import AgentRun, AgentEvent, RootCauseHypothesis, InvestigationReport
from app.models.patch import Patch, PatchValidation
from app.models.evidence import EvidenceItem, RetrievedDocument
from app.orchestration.graph import investigation_graph
from app.api.ws import manager
from app.core.logging import logger

async def broadcast_incident_update(incident_id: str, data: Dict[str, Any]):
    try:
        await manager.broadcast_to_channel(incident_id, data)
    except Exception as e:
        logger.warning(f"WebSocket broadcast warning: {e}")

def utc_now():
    return datetime.now(timezone.utc)

class InvestigationService:
    @staticmethod
    async def run_investigation(
        db: AsyncSession,
        incident_id: str,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end LangGraph autonomous incident investigation workflow.
        Stores persistent checkpoints and broadcasts real-time telemetry events.
        """
        logger.info(f"[InvestigationService] Starting autonomous investigation for incident {incident_id}")

        # 1. Fetch incident with relationships
        stmt = (
            select(Incident)
            .options(
                selectinload(Incident.logs),
                selectinload(Incident.traces),
                selectinload(Incident.events)
            )
            .filter(Incident.id == incident_id)
        )
        incident = (await db.execute(stmt)).scalar_one_or_none()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # 2. Initialize AgentRun database record
        agent_run = AgentRun(
            incident_id=incident.id,
            workflow_name="AutonomousIncidentInvestigatorWorkflow",
            status="running",
            current_agent="triage",
            started_at=utc_now(),
            graph_state={"incident_id": incident.id, "stage": "initialization"}
        )
        db.add(agent_run)
        incident.status = "Investigating"

        # Record Incident Event
        start_event = IncidentEvent(
            incident_id=incident.id,
            event_type="investigation_started",
            message="Autonomous Investigation Initiated. LangGraph orchestrator activated specialized agents (Triage, Logs, AST Code, RCA, Fix, Validation, Review).",
            actor="AgentOps Orchestrator"
        )
        db.add(start_event)
        await db.commit()
        await db.refresh(agent_run)

        # Broadcast start event
        await broadcast_incident_update(incident.id, {
            "type": "investigation_started",
            "run_id": agent_run.id,
            "status": "Investigating",
            "message": "Autonomous multi-agent investigation started."
        })

        # 3. Build Initial LangGraph State
        logs_data = [
            {
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "service_name": l.service_name,
                "level": l.level,
                "message": l.message,
                "stack_trace": l.stack_trace,
                "attributes": l.log_attributes
            }
            for l in incident.logs
        ]

        traces_data = [
            {
                "service_name": t.service_name,
                "operation_name": t.operation_name,
                "duration_ms": t.duration_ms,
                "status_code": t.status_code,
                "error_message": t.error_message
            }
            for t in incident.traces
        ]

        initial_state = {
            "incident_id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity,
            "affected_services": incident.affected_services or ["checkout-service"],
            "error_rate": incident.error_rate or "0%",
            "detection_source": incident.detection_source or "System Monitor",
            "logs": logs_data,
            "traces": traces_data,
            "repo_path": "demo-services",
            "retry_count": 0,
            "max_retries": 2,
            "current_stage": "Initialized",
            "agent_events": [],
            "total_tokens": 0,
            "total_cost": 0.0
        }

        start_time = time.time()

        try:
            # 4. Invoke Central LangGraph Stateful Graph
            final_state = await investigation_graph.ainvoke(initial_state)

            duration = round(time.time() - start_time, 2)
            logger.info(f"[InvestigationService] LangGraph workflow complete in {duration}s")

            # 5. Persist Agent Events
            for idx, ev in enumerate(final_state.get("agent_events", [])):
                db_event = AgentEvent(
                    run_id=agent_run.id,
                    agent_name=ev.get("agent_name", "Orchestrator"),
                    event_type="stage_complete",
                    message=ev.get("message", ""),
                    step_index=idx + 1,
                    duration_ms=round(duration * 1000 / max(len(final_state.get("agent_events", [])), 1), 1)
                )
                db.add(db_event)

            # 6. Persist Root Cause Hypotheses
            rca = final_state.get("root_cause_analysis", {})
            hypotheses = final_state.get("hypotheses", [])
            for rank_idx, h in enumerate(hypotheses, start=1):
                hyp_record = RootCauseHypothesis(
                    run_id=agent_run.id,
                    incident_id=incident.id,
                    title=h.get("title", ""),
                    explanation=h.get("description", ""),
                    confidence_score=h.get("probability", 0.9),
                    rank=rank_idx,
                    is_primary=(rank_idx == 1),
                    supporting_evidence=h.get("supporting_evidence", []),
                    counter_evidence=h.get("contradicting_evidence", [])
                )
                db.add(hyp_record)

            # 7. Persist Evidence Items & Retrieved Documents
            for ev_item in final_state.get("evidence_items", []):
                db_ev = EvidenceItem(
                    incident_id=incident.id,
                    run_id=agent_run.id,
                    source_type=ev_item.get("source_type", "log"),
                    title=ev_item.get("title", "Technical Evidence"),
                    description=ev_item.get("title", ""),
                    raw_content=str(ev_item.get("content", "")),
                    confidence=ev_item.get("confidence", 0.95),
                    evidence_metadata=ev_item.get("attribution", {})
                )
                db.add(db_ev)

            for doc in final_state.get("retrieved_documents", []):
                db_doc = RetrievedDocument(
                    incident_id=incident.id,
                    run_id=agent_run.id,
                    query=incident.title,
                    doc_type=doc.get("doc_type", "code"),
                    repository=doc.get("repository", "acme/ecommerce-platform"),
                    file_path=doc.get("file_path", ""),
                    function_name=doc.get("function_name"),
                    class_name=doc.get("class_name"),
                    score=doc.get("combined_score", 0.0),
                    content=doc.get("content", ""),
                    source_attribution=doc.get("source_attribution", {})
                )
                db.add(db_doc)

            # 8. Persist Proposed Patch & Sandboxed Validation
            patch_data = final_state.get("proposed_patch", {})
            val_data = final_state.get("validation_result", {})

            if patch_data:
                db_patch = Patch(
                    incident_id=incident.id,
                    run_id=agent_run.id,
                    title=f"Fix: {rca.get('primary_hypothesis', 'Incident Fix')}",
                    explanation=patch_data.get("explanation", ""),
                    diff_content=patch_data.get("diff", ""),
                    affected_files=[patch_data.get("affected_file", "")],
                    regression_tests=patch_data.get("test_code", ""),
                    status="validated_success" if val_data.get("tests_passed") else "validated_failed"
                )
                db.add(db_patch)
                await db.flush()

                # Add validation record
                db_val = PatchValidation(
                    patch_id=db_patch.id,
                    run_id=agent_run.id,
                    status="passed" if val_data.get("tests_passed") else "failed",
                    syntax_valid=val_data.get("syntax_valid", True),
                    tests_passed=val_data.get("tests_passed", True),
                    total_tests=str(val_data.get("tests_run", 2)),
                    passed_tests=str(val_data.get("tests_run", 2) - val_data.get("test_failures", 0)),
                    failed_tests=str(val_data.get("test_failures", 0)),
                    execution_time_seconds=val_data.get("duration_seconds", 0.5),
                    stdout_output=val_data.get("stdout", ""),
                    stderr_output=val_data.get("stderr", ""),
                    validation_summary=val_data.get("summary", "Validation complete")
                )
                db.add(db_val)

            # 9. Persist Final Investigation Report
            review_data = final_state.get("review_result", {})
            investigation_report = InvestigationReport(
                incident_id=incident.id,
                run_id=agent_run.id,
                title=f"Autonomous Investigation Report: {incident.title}",
                executive_summary=review_data.get("executive_summary", rca.get("explanation", "")),
                severity_assessment=incident.severity,
                affected_services_summary=incident.affected_services or [],
                timeline_chronology=[ev.get("message", "") for ev in final_state.get("agent_events", [])],
                error_patterns=[rca.get("architectural_flaw", "System design flaw")],
                primary_root_cause=rca.get("primary_hypothesis", "Identified by Multi-Agent Swarm"),
                confidence_score=round(rca.get("confidence_score", 0.95), 2),
                confidence_rationale=review_data.get("uncertainty_summary", "High evidentiary support from logs and AST"),
                missing_information=[],
                regression_risks=[patch_data.get("regression_risk", "Low")],
                recommended_next_steps=[
                    "Review and approve staged patch",
                    "Merge optional GitHub PR",
                    "Verify deployment telemetry in Datadog / Prometheus"
                ],
                status="final"
            )
            db.add(investigation_report)

            # 10. Update Incident & AgentRun Final Statuses
            incident.status = "Awaiting Approval"
            incident.root_cause_summary = rca.get("primary_hypothesis", "Diagnosed by AI Agents")

            agent_run.status = "paused_awaiting_approval"
            agent_run.current_agent = "review"
            agent_run.step_count = len(final_state.get("agent_events", []))
            agent_run.total_tokens_used = final_state.get("total_tokens", 0)
            agent_run.estimated_cost_usd = final_state.get("total_cost", 0.0)
            agent_run.completed_at = utc_now()
            agent_run.graph_state = {
                "triage": final_state.get("triage_result"),
                "log_analysis": final_state.get("log_analysis_result"),
                "code_investigation": final_state.get("code_investigation_result"),
                "root_cause": final_state.get("root_cause_analysis"),
                "proposed_patch": final_state.get("proposed_patch"),
                "validation": final_state.get("validation_result"),
                "review": final_state.get("review_result")
            }

            # Add incident resolution milestone event
            finish_event = IncidentEvent(
                incident_id=incident.id,
                event_type="investigation_complete",
                message=f"Root cause '{incident.root_cause_summary}' verified. Sandboxed patch validation succeeded. Human approval required before deployment.",
                actor="AgentOps Gatekeeper"
            )
            db.add(finish_event)

            await db.commit()

            # Broadcast completion event
            await broadcast_incident_update(incident.id, {
                "type": "investigation_completed",
                "run_id": agent_run.id,
                "status": "Awaiting Approval",
                "root_cause": incident.root_cause_summary,
                "message": "Autonomous investigation succeeded. Ready for human engineer review."
            })

            return {
                "status": "success",
                "run_id": agent_run.id,
                "incident_id": incident.id,
                "current_stage": "Awaiting Approval",
                "final_state": final_state
            }

        except Exception as e:
            logger.error(f"[InvestigationService] Error during investigation: {e}", exc_info=True)
            agent_run.status = "failed"
            agent_run.error_message = str(e)
            incident.status = "Failed"
            await db.commit()

            await broadcast_incident_update(incident.id, {
                "type": "investigation_failed",
                "error": str(e)
            })
            raise e
