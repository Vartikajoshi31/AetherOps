from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.database.session import get_db
from app.models.agent_run import AgentRun, AgentEvent
from app.models.incident import Incident
from pydantic import BaseModel

investigations_router = APIRouter(prefix="/investigations", tags=["Investigations"])

class AgentEventItem(BaseModel):
    id: str
    agent_name: str
    stage: str
    message: str
    step_index: int
    duration_ms: float
    created_at: str

class AgentRunSummary(BaseModel):
    id: str
    incident_id: str
    incident_title: str
    workflow_name: str
    status: str
    current_agent: str
    step_count: int
    total_tokens_used: int
    estimated_cost_usd: float
    started_at: str
    completed_at: Optional[str] = None

class AgentRunDetail(AgentRunSummary):
    graph_state: Dict[str, Any]
    error_message: Optional[str] = None
    events: List[AgentEventItem]

@investigations_router.get("", response_model=List[AgentRunSummary])
async def list_investigations(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(AgentRun)
        .options(selectinload(AgentRun.incident))
        .order_by(desc(AgentRun.started_at))
    )
    runs = (await db.execute(stmt)).scalars().all()
    results = []
    for r in runs:
        results.append(
            AgentRunSummary(
                id=r.id,
                incident_id=r.incident_id,
                incident_title=r.incident.title if r.incident else "Unknown Incident",
                workflow_name=r.workflow_name,
                status=r.status,
                current_agent=r.current_agent,
                step_count=r.step_count,
                total_tokens_used=r.total_tokens_used,
                estimated_cost_usd=round(r.estimated_cost_usd, 6),
                started_at=r.started_at.isoformat() if r.started_at else "",
                completed_at=r.completed_at.isoformat() if r.completed_at else None
            )
        )
    return results

@investigations_router.get("/{run_id}", response_model=AgentRunDetail)
async def get_investigation_run(run_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(AgentRun)
        .options(
            selectinload(AgentRun.incident),
            selectinload(AgentRun.events)
        )
        .filter(AgentRun.id == run_id)
    )
    run = (await db.execute(stmt)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Investigation run not found")

    events = [
        AgentEventItem(
            id=ev.id,
            agent_name=ev.agent_name,
            stage=ev.event_type,
            message=ev.message,
            step_index=ev.step_index,
            duration_ms=ev.duration_ms,
            created_at=ev.created_at.isoformat() if ev.created_at else ""
        )
        for ev in run.events
    ]

    return AgentRunDetail(
        id=run.id,
        incident_id=run.incident_id,
        incident_title=run.incident.title if run.incident else "Unknown Incident",
        workflow_name=run.workflow_name,
        status=run.status,
        current_agent=run.current_agent,
        step_count=run.step_count,
        total_tokens_used=run.total_tokens_used,
        estimated_cost_usd=round(run.estimated_cost_usd, 6),
        started_at=run.started_at.isoformat() if run.started_at else "",
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        graph_state=run.graph_state or {},
        error_message=run.error_message,
        events=events
    )

@investigations_router.get("/incident/{incident_id}", response_model=Optional[AgentRunDetail])
async def get_latest_incident_investigation(incident_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(AgentRun)
        .options(
            selectinload(AgentRun.incident),
            selectinload(AgentRun.events)
        )
        .filter(AgentRun.incident_id == incident_id)
        .order_by(desc(AgentRun.started_at))
    )
    run = (await db.execute(stmt)).scalars().first()
    if not run:
        return None

    events = [
        AgentEventItem(
            id=ev.id,
            agent_name=ev.agent_name,
            stage=ev.event_type,
            message=ev.message,
            step_index=ev.step_index,
            duration_ms=ev.duration_ms,
            created_at=ev.created_at.isoformat() if ev.created_at else ""
        )
        for ev in run.events
    ]

    return AgentRunDetail(
        id=run.id,
        incident_id=run.incident_id,
        incident_title=run.incident.title if run.incident else "Unknown Incident",
        workflow_name=run.workflow_name,
        status=run.status,
        current_agent=run.current_agent,
        step_count=run.step_count,
        total_tokens_used=run.total_tokens_used,
        estimated_cost_usd=round(run.estimated_cost_usd, 6),
        started_at=run.started_at.isoformat() if run.started_at else "",
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        graph_state=run.graph_state or {},
        error_message=run.error_message,
        events=events
    )
