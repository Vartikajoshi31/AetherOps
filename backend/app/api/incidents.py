from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database.session import get_db
from app.models.incident import Incident, IncidentEvent, IncidentLog, IncidentTrace
from app.models.patch import Patch, PatchValidation, Approval
from app.models.evidence import EvidenceItem
from app.models.agent_run import InvestigationReport, AgentRun
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentDetailResponse,
    IncidentEventResponse,
    IncidentLogResponse,
    IncidentTraceResponse
)
from app.schemas.patch import (
    PatchResponse,
    ApprovalRequest,
    ApprovalResponse,
    PatchValidationResponse
)
from app.schemas.agent import InvestigationReportResponse, InvestigationStartRequest
from app.services.incident_service import IncidentService, utcnow
from app.services.simulation_service import SimulationService
from app.api.ws import manager
from pydantic import BaseModel
import uuid
from datetime import datetime

incidents_router = APIRouter(prefix="/incidents", tags=["Incidents"])

class LogIngestRequest(BaseModel):
    service_name: str
    level: str = "ERROR"
    message: str
    stack_trace: Optional[str] = None
    log_attributes: Dict[str, Any] = {}

class TraceIngestRequest(BaseModel):
    service_name: str
    operation_name: str
    duration_ms: float
    status_code: str = "500"
    error_message: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    trace_metadata: Dict[str, Any] = {}

class ResolveIncidentRequest(BaseModel):
    resolution_summary: str

class SimulationRequest(BaseModel):
    scenario_key: str = "db_pool_exhaustion"

@incidents_router.get("/scenarios")
async def list_chaos_scenarios():
    return SimulationService.get_available_scenarios()

@incidents_router.post("/simulate", response_model=IncidentResponse)
async def simulate_chaos_incident(
    req: SimulationRequest,
    db: AsyncSession = Depends(get_db)
):
    incident = await SimulationService.simulate_incident(db, req.scenario_key)
    await manager.broadcast_to_channel("global", {
        "type": "incident_created",
        "incident_id": incident.id,
        "title": incident.title,
        "severity": incident.severity
    })
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        affected_services=incident.affected_services or [],
        error_rate=incident.error_rate,
        detection_source=incident.detection_source,
        tags=incident.tags or [],
        start_time=incident.start_time.isoformat() if incident.start_time else "",
        resolved_at=None,
        root_cause_summary=None,
        resolution_summary=None,
        created_at=incident.created_at.isoformat() if incident.created_at else "",
        updated_at=incident.updated_at.isoformat() if incident.updated_at else "",
        events_count=1,
        logs_count=2,
        traces_count=2,
        patches_count=0
    )

@incidents_router.post("/reset-demo")
async def reset_demo(db: AsyncSession = Depends(get_db)):
    await SimulationService.reset_demo_state(db)
    await manager.broadcast_to_channel("global", {"type": "demo_reset"})
    return {"status": "success", "message": "Demo data reset to pristine baseline state"}

@incidents_router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    service: Optional[str] = Query(None, description="Filter by service"),
    search: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    incidents = await IncidentService.get_all_incidents(
        db, status=status, severity=severity, service=service, search=search, limit=limit, offset=offset
    )
    results = []
    for inc in incidents:
        events_count = len(inc.events) if hasattr(inc, "events") and inc.events is not None else 0
        logs_count = len(inc.logs) if hasattr(inc, "logs") and inc.logs is not None else 0
        traces_count = len(inc.traces) if hasattr(inc, "traces") and inc.traces is not None else 0
        patches_count = len(inc.patches) if hasattr(inc, "patches") and inc.patches is not None else 0
        results.append(
            IncidentResponse(
                id=inc.id,
                title=inc.title,
                description=inc.description,
                severity=inc.severity,
                status=inc.status,
                affected_services=inc.affected_services or [],
                error_rate=inc.error_rate,
                detection_source=inc.detection_source,
                tags=inc.tags or [],
                start_time=inc.start_time.isoformat() if inc.start_time else "",
                resolved_at=inc.resolved_at.isoformat() if inc.resolved_at else None,
                root_cause_summary=inc.root_cause_summary,
                resolution_summary=inc.resolution_summary,
                created_at=inc.created_at.isoformat() if inc.created_at else "",
                updated_at=inc.updated_at.isoformat() if inc.updated_at else "",
                events_count=events_count,
                logs_count=logs_count,
                traces_count=traces_count,
                patches_count=patches_count
            )
        )
    return results

@incidents_router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db)
):
    incident = await IncidentService.create_incident(db, data)
    await manager.broadcast_to_channel("global", {
        "type": "incident_created",
        "incident_id": incident.id,
        "title": incident.title,
        "severity": incident.severity
    })

    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        affected_services=incident.affected_services or [],
        error_rate=incident.error_rate,
        detection_source=incident.detection_source,
        tags=incident.tags or [],
        start_time=incident.start_time.isoformat() if incident.start_time else "",
        resolved_at=None,
        root_cause_summary=None,
        resolution_summary=None,
        created_at=incident.created_at.isoformat() if incident.created_at else "",
        updated_at=incident.updated_at.isoformat() if incident.updated_at else "",
        events_count=1,
        logs_count=1 if data.initial_log_message else 0,
        traces_count=0,
        patches_count=0
    )

@incidents_router.get("/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db)
):
    incident = await IncidentService.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    events_stmt = select(IncidentEvent).filter(IncidentEvent.incident_id == incident_id).order_by(IncidentEvent.created_at)
    events = (await db.execute(events_stmt)).scalars().all()

    logs_stmt = select(IncidentLog).filter(IncidentLog.incident_id == incident_id).order_by(desc(IncidentLog.timestamp))
    logs = (await db.execute(logs_stmt)).scalars().all()

    traces_stmt = select(IncidentTrace).filter(IncidentTrace.incident_id == incident_id).order_by(desc(IncidentTrace.created_at))
    traces = (await db.execute(traces_stmt)).scalars().all()

    patches_count_stmt = select(Patch).filter(Patch.incident_id == incident_id)
    patches_count = len((await db.execute(patches_count_stmt)).scalars().all())

    return IncidentDetailResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        affected_services=incident.affected_services or [],
        error_rate=incident.error_rate,
        detection_source=incident.detection_source,
        tags=incident.tags or [],
        start_time=incident.start_time.isoformat() if incident.start_time else "",
        resolved_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
        root_cause_summary=incident.root_cause_summary,
        resolution_summary=incident.resolution_summary,
        created_at=incident.created_at.isoformat() if incident.created_at else "",
        updated_at=incident.updated_at.isoformat() if incident.updated_at else "",
        events_count=len(events),
        logs_count=len(logs),
        traces_count=len(traces),
        patches_count=patches_count,
        events=[
            IncidentEventResponse(
                id=ev.id,
                incident_id=ev.incident_id,
                event_type=ev.event_type,
                message=ev.message,
                actor=ev.actor,
                event_metadata=ev.event_metadata or {},
                created_at=ev.created_at.isoformat() if ev.created_at else ""
            ) for ev in events
        ],
        logs=[
            IncidentLogResponse(
                id=l.id,
                incident_id=l.incident_id,
                service_name=l.service_name,
                level=l.level,
                timestamp=l.timestamp.isoformat() if l.timestamp else "",
                message=l.message,
                stack_trace=l.stack_trace,
                log_attributes=l.log_attributes or {}
            ) for l in logs
        ],
        traces=[
            IncidentTraceResponse(
                id=t.id,
                incident_id=t.incident_id,
                trace_id=t.trace_id,
                span_id=t.span_id,
                parent_span_id=t.parent_span_id,
                service_name=t.service_name,
                operation_name=t.operation_name,
                duration_ms=t.duration_ms,
                status_code=t.status_code,
                error_message=t.error_message,
                trace_metadata=t.trace_metadata or {}
            ) for t in traces
        ]
    )

@incidents_router.post("/{incident_id}/logs", response_model=IncidentLogResponse)
async def ingest_incident_log(
    incident_id: str,
    log_req: LogIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    incident = await IncidentService.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    log_entry = IncidentLog(
        id=str(uuid.uuid4()),
        incident_id=incident_id,
        service_name=log_req.service_name,
        level=log_req.level.upper(),
        timestamp=utcnow(),
        message=log_req.message,
        stack_trace=log_req.stack_trace,
        log_attributes=log_req.log_attributes
    )
    db.add(log_entry)
    await db.commit()

    await manager.broadcast_to_channel(incident_id, {
        "type": "log_ingested",
        "incident_id": incident_id,
        "service": log_req.service_name,
        "level": log_req.level
    })

    return IncidentLogResponse(
        id=log_entry.id,
        incident_id=log_entry.incident_id,
        service_name=log_entry.service_name,
        level=log_entry.level,
        timestamp=log_entry.timestamp.isoformat(),
        message=log_entry.message,
        stack_trace=log_entry.stack_trace,
        log_attributes=log_entry.log_attributes or {}
    )

@incidents_router.post("/{incident_id}/traces", response_model=IncidentTraceResponse)
async def ingest_incident_trace(
    incident_id: str,
    trace_req: TraceIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    incident = await IncidentService.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    trace_entry = IncidentTrace(
        id=str(uuid.uuid4()),
        incident_id=incident_id,
        trace_id=trace_req.trace_id or uuid.uuid4().hex,
        span_id=trace_req.span_id or uuid.uuid4().hex[:16],
        parent_span_id=trace_req.parent_span_id,
        service_name=trace_req.service_name,
        operation_name=trace_req.operation_name,
        duration_ms=trace_req.duration_ms,
        status_code=trace_req.status_code,
        error_message=trace_req.error_message,
        trace_metadata=trace_req.trace_metadata
    )
    db.add(trace_entry)
    await db.commit()

    await manager.broadcast_to_channel(incident_id, {
        "type": "trace_ingested",
        "incident_id": incident_id,
        "operation": trace_req.operation_name
    })

    return IncidentTraceResponse(
        id=trace_entry.id,
        incident_id=trace_entry.incident_id,
        trace_id=trace_entry.trace_id,
        span_id=trace_entry.span_id,
        parent_span_id=trace_entry.parent_span_id,
        service_name=trace_entry.service_name,
        operation_name=trace_entry.operation_name,
        duration_ms=trace_entry.duration_ms,
        status_code=trace_entry.status_code,
        error_message=trace_entry.error_message,
        trace_metadata=trace_entry.trace_metadata or {}
    )

@incidents_router.post("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: str,
    req: ResolveIncidentRequest,
    db: AsyncSession = Depends(get_db)
):
    incident = await IncidentService.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "Resolved"
    incident.resolved_at = utcnow()
    incident.resolution_summary = req.resolution_summary

    ev = IncidentEvent(
        id=str(uuid.uuid4()),
        incident_id=incident.id,
        event_type="incident_resolved",
        message=f"Incident marked Resolved by engineer. Resolution: {req.resolution_summary}",
        actor="Human Engineer"
    )
    db.add(ev)
    await db.commit()

    await manager.broadcast_to_channel(incident_id, {
        "type": "incident_resolved",
        "incident_id": incident.id
    })

    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        affected_services=incident.affected_services or [],
        error_rate=incident.error_rate,
        detection_source=incident.detection_source,
        tags=incident.tags or [],
        start_time=incident.start_time.isoformat() if incident.start_time else "",
        resolved_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
        root_cause_summary=incident.root_cause_summary,
        resolution_summary=incident.resolution_summary,
        created_at=incident.created_at.isoformat() if incident.created_at else "",
        updated_at=incident.updated_at.isoformat() if incident.updated_at else "",
        events_count=1,
        logs_count=0,
        traces_count=0,
        patches_count=0
    )

@incidents_router.post("/{incident_id}/reopen", response_model=IncidentResponse)
async def reopen_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db)
):
    incident = await IncidentService.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "Investigating"
    incident.resolved_at = None

    ev = IncidentEvent(
        id=str(uuid.uuid4()),
        incident_id=incident.id,
        event_type="incident_reopened",
        message="Incident reopened for continuous investigation",
        actor="Human Engineer"
    )
    db.add(ev)
    await db.commit()

    await manager.broadcast_to_channel(incident_id, {
        "type": "incident_reopened",
        "incident_id": incident.id
    })

    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        affected_services=incident.affected_services or [],
        error_rate=incident.error_rate,
        detection_source=incident.detection_source,
        tags=incident.tags or [],
        start_time=incident.start_time.isoformat() if incident.start_time else "",
        resolved_at=None,
        root_cause_summary=incident.root_cause_summary,
        resolution_summary=incident.resolution_summary,
        created_at=incident.created_at.isoformat() if incident.created_at else "",
        updated_at=incident.updated_at.isoformat() if incident.updated_at else "",
        events_count=1,
        logs_count=0,
        traces_count=0,
        patches_count=0
    )

@incidents_router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    data: IncidentUpdate,
    db: AsyncSession = Depends(get_db)
):
    incident = await IncidentService.update_incident(db, incident_id, data)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    await manager.broadcast_to_channel(incident_id, {
        "type": "incident_updated",
        "incident_id": incident.id,
        "status": incident.status
    })

    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        affected_services=incident.affected_services or [],
        error_rate=incident.error_rate,
        detection_source=incident.detection_source,
        tags=incident.tags or [],
        start_time=incident.start_time.isoformat() if incident.start_time else "",
        resolved_at=incident.resolved_at.isoformat() if incident.resolved_at else None,
        root_cause_summary=incident.root_cause_summary,
        resolution_summary=incident.resolution_summary,
        created_at=incident.created_at.isoformat() if incident.created_at else "",
        updated_at=incident.updated_at.isoformat() if incident.updated_at else "",
        events_count=0,
        logs_count=0,
        traces_count=0,
        patches_count=0
    )

@incidents_router.get("/{incident_id}/timeline", response_model=List[IncidentEventResponse])
async def get_incident_timeline(incident_id: str, db: AsyncSession = Depends(get_db)):
    events_stmt = select(IncidentEvent).filter(IncidentEvent.incident_id == incident_id).order_by(IncidentEvent.created_at)
    events = (await db.execute(events_stmt)).scalars().all()
    return [
        IncidentEventResponse(
            id=ev.id,
            incident_id=ev.incident_id,
            event_type=ev.event_type,
            message=ev.message,
            actor=ev.actor,
            event_metadata=ev.event_metadata or {},
            created_at=ev.created_at.isoformat() if ev.created_at else ""
        ) for ev in events
    ]

@incidents_router.get("/{incident_id}/report", response_model=Optional[InvestigationReportResponse])
async def get_incident_report(incident_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(InvestigationReport).filter(InvestigationReport.incident_id == incident_id).order_by(desc(InvestigationReport.created_at))
    report = (await db.execute(stmt)).scalars().first()
    if not report:
        return None
    return InvestigationReportResponse(
        id=report.id,
        incident_id=report.incident_id,
        run_id=report.run_id,
        title=report.title,
        executive_summary=report.executive_summary,
        severity_assessment=report.severity_assessment,
        affected_services_summary=report.affected_services_summary or [],
        timeline_chronology=report.timeline_chronology or [],
        error_patterns=report.error_patterns or [],
        relevant_logs_summary=report.relevant_logs_summary,
        related_code_summary=report.related_code_summary,
        primary_root_cause=report.primary_root_cause,
        confidence_score=report.confidence_score,
        confidence_rationale=report.confidence_rationale,
        missing_information=report.missing_information or [],
        regression_risks=report.regression_risks or [],
        recommended_next_steps=report.recommended_next_steps or [],
        status=report.status,
        created_at=report.created_at.isoformat() if report.created_at else ""
    )

@incidents_router.get("/{incident_id}/evidence")
async def get_incident_evidence(incident_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(EvidenceItem).filter(EvidenceItem.incident_id == incident_id).order_by(desc(EvidenceItem.created_at))
    evidence = (await db.execute(stmt)).scalars().all()
    return [ev.to_dict() for ev in evidence]

@incidents_router.get("/{incident_id}/patch", response_model=Optional[PatchResponse])
async def get_incident_patch(incident_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Patch).filter(Patch.incident_id == incident_id).order_by(desc(Patch.created_at))
    patch = (await db.execute(stmt)).scalars().first()
    if not patch:
        return None
    
    val_stmt = select(PatchValidation).filter(PatchValidation.patch_id == patch.id).order_by(desc(PatchValidation.created_at))
    validations = (await db.execute(val_stmt)).scalars().all()

    return PatchResponse(
        id=patch.id,
        incident_id=patch.incident_id,
        run_id=patch.run_id,
        title=patch.title,
        explanation=patch.explanation,
        diff_content=patch.diff_content,
        affected_files=patch.affected_files or [],
        regression_tests=patch.regression_tests,
        status=patch.status,
        github_pr_url=patch.github_pr_url,
        created_at=patch.created_at.isoformat() if patch.created_at else "",
        validations=[
            PatchValidationResponse(
                id=v.id,
                patch_id=v.patch_id,
                status=v.status,
                syntax_valid=v.syntax_valid,
                tests_passed=v.tests_passed,
                total_tests=v.total_tests,
                passed_tests=v.passed_tests,
                failed_tests=v.failed_tests,
                execution_time_seconds=v.execution_time_seconds,
                memory_peak_mb=v.memory_peak_mb,
                stdout_output=v.stdout_output,
                stderr_output=v.stderr_output,
                regression_detected=v.regression_detected,
                validation_summary=v.validation_summary,
                created_at=v.created_at.isoformat() if v.created_at else ""
            ) for v in validations
        ]
    )

@incidents_router.post("/{incident_id}/approve", response_model=ApprovalResponse)
async def approve_incident_patch(
    incident_id: str,
    approval_req: ApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    patch_stmt = select(Patch).filter(Patch.incident_id == incident_id).order_by(desc(Patch.created_at))
    patch = (await db.execute(patch_stmt)).scalars().first()
    if not patch:
        raise HTTPException(status_code=404, detail="No patch found for this incident to approve")

    pr_url = f"https://github.com/acme/ecommerce-platform/pull/{uuid.uuid4().hex[:6]}" if approval_req.create_github_pr else None
    
    patch.status = "approved" if approval_req.action == "approved" else "rejected"
    if pr_url:
        patch.status = "pr_created"
        patch.github_pr_url = pr_url

    approval = Approval(
        id=str(uuid.uuid4()),
        patch_id=patch.id,
        incident_id=incident_id,
        action=approval_req.action,
        feedback=approval_req.feedback,
        created_pr=approval_req.create_github_pr,
        github_pr_url=pr_url
    )
    db.add(approval)

    event = IncidentEvent(
        id=str(uuid.uuid4()),
        incident_id=incident_id,
        event_type="patch_approval",
        message=f"Human engineer decision: {approval_req.action.upper()}. Feedback: {approval_req.feedback or 'Approved without comment'}. PR: {pr_url or 'None'}",
        actor="Human Engineer (Reviewer)",
        event_metadata={"action": approval_req.action, "pr_url": pr_url}
    )
    db.add(event)

    incident = await IncidentService.get_incident_by_id(db, incident_id)
    if incident and approval_req.action == "approved":
        incident.status = "Resolved"
        incident.resolved_at = utcnow()
        incident.resolution_summary = f"Patch approved and applied. {f'Pull Request created: {pr_url}' if pr_url else ''}"

    await db.commit()

    await manager.broadcast_to_channel(incident_id, {
        "type": "patch_decision",
        "incident_id": incident_id,
        "action": approval_req.action,
        "pr_url": pr_url
    })

    return ApprovalResponse(
        id=approval.id,
        patch_id=patch.id,
        incident_id=incident_id,
        reviewer_id=None,
        action=approval.action,
        feedback=approval.feedback,
        created_pr=approval.created_pr,
        github_pr_url=approval.github_pr_url,
        created_at=approval.created_at.isoformat() if approval.created_at else ""
    )
