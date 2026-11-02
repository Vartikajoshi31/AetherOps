from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.incident_service import IncidentService
from app.schemas.evaluation import DashboardMetricsResponse

metrics_router = APIRouter(prefix="/metrics", tags=["Metrics"])

@metrics_router.get("", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    """Fetch computed real-time metrics across all incidents, services, and agent runs."""
    metrics = await IncidentService.get_dashboard_metrics(db)
    return metrics
