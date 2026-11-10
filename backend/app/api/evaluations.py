from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database.session import get_db
from app.models.evaluation import EvaluationRun, EvaluationResult, BenchmarkIncident
from app.schemas.evaluation import (
    EvaluationRunRequest,
    EvaluationRunResponse,
    EvaluationResultResponse,
    BenchmarkIncidentResponse
)
from app.services.benchmark_service import BenchmarkService
import uuid

evaluations_router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

@evaluations_router.get("/benchmarks", response_model=List[BenchmarkIncidentResponse])
async def list_benchmarks(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    await BenchmarkService.ensure_benchmarks_loaded(db)
    query = select(BenchmarkIncident).order_by(BenchmarkIncident.benchmark_id)
    if category:
        query = query.filter(BenchmarkIncident.category == category)
    items = (await db.execute(query)).scalars().all()
    return [
        BenchmarkIncidentResponse(
            id=b.id,
            benchmark_id=b.benchmark_id,
            title=b.title,
            category=b.category,
            service_name=b.service_name,
            ground_truth_root_cause=b.ground_truth_root_cause,
            ground_truth_culprit_files=b.ground_truth_culprit_files or [],
            created_at=b.created_at.isoformat() if b.created_at else ""
        ) for b in items
    ]

@evaluations_router.get("/runs", response_model=List[EvaluationRunResponse])
async def list_evaluation_runs(db: AsyncSession = Depends(get_db)):
    stmt = select(EvaluationRun).order_by(desc(EvaluationRun.created_at))
    runs = (await db.execute(stmt)).scalars().all()
    
    response = []
    for r in runs:
        res_stmt = select(EvaluationResult).filter(EvaluationResult.run_id == r.id).order_by(EvaluationResult.benchmark_id)
        results = (await db.execute(res_stmt)).scalars().all()
        response.append(
            EvaluationRunResponse(
                id=r.id,
                name=r.name,
                model_name=r.model_name,
                total_benchmarks=r.total_benchmarks,
                completed_benchmarks=r.completed_benchmarks,
                status=r.status,
                root_cause_accuracy=r.root_cause_accuracy,
                top_3_recall=r.top_3_recall,
                evidence_retrieval_precision=r.evidence_retrieval_precision,
                evidence_retrieval_recall=r.evidence_retrieval_recall,
                patch_pass_rate=r.patch_pass_rate,
                regression_rate=r.regression_rate,
                mean_time_to_diagnosis_seconds=r.mean_time_to_diagnosis_seconds,
                average_tokens_per_incident=r.average_tokens_per_incident,
                average_cost_per_incident_usd=r.average_cost_per_incident_usd,
                created_at=r.created_at.isoformat() if r.created_at else "",
                results=[
                    EvaluationResultResponse(
                        id=res.id,
                        benchmark_id=res.benchmark_id,
                        incident_title=res.incident_title,
                        identified_root_cause=res.identified_root_cause,
                        ground_truth_root_cause=res.ground_truth_root_cause,
                        root_cause_correct=res.root_cause_correct,
                        in_top_3=res.in_top_3,
                        retrieval_precision=res.retrieval_precision,
                        retrieval_recall=res.retrieval_recall,
                        patch_passed_tests=res.patch_passed_tests,
                        execution_time_seconds=res.execution_time_seconds,
                        tokens_consumed=res.tokens_consumed,
                        cost_usd=res.cost_usd,
                        created_at=res.created_at.isoformat() if res.created_at else ""
                    ) for res in results
                ]
            )
        )
    return response

@evaluations_router.post("/run", response_model=EvaluationRunResponse)
async def run_evaluation_benchmark(
    req: EvaluationRunRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes an autonomous benchmark evaluation run across benchmark incidents.
    """
    try:
        new_run = await BenchmarkService.run_evaluation_suite(
            db=db,
            name=req.name,
            model_name=req.model_name,
            limit=req.limit or 5
        )

        res_stmt = select(EvaluationResult).filter(EvaluationResult.run_id == new_run.id).order_by(EvaluationResult.benchmark_id)
        results = (await db.execute(res_stmt)).scalars().all()

        return EvaluationRunResponse(
            id=new_run.id,
            name=new_run.name,
            model_name=new_run.model_name,
            total_benchmarks=new_run.total_benchmarks,
            completed_benchmarks=new_run.completed_benchmarks,
            status=new_run.status,
            root_cause_accuracy=new_run.root_cause_accuracy,
            top_3_recall=new_run.top_3_recall,
            evidence_retrieval_precision=new_run.evidence_retrieval_precision,
            evidence_retrieval_recall=new_run.evidence_retrieval_recall,
            patch_pass_rate=new_run.patch_pass_rate,
            regression_rate=new_run.regression_rate,
            mean_time_to_diagnosis_seconds=new_run.mean_time_to_diagnosis_seconds,
            average_tokens_per_incident=new_run.average_tokens_per_incident,
            average_cost_per_incident_usd=new_run.average_cost_per_incident_usd,
            created_at=new_run.created_at.isoformat() if new_run.created_at else "",
            results=[
                EvaluationResultResponse(
                    id=res.id,
                    benchmark_id=res.benchmark_id,
                    incident_title=res.incident_title,
                    identified_root_cause=res.identified_root_cause,
                    ground_truth_root_cause=res.ground_truth_root_cause,
                    root_cause_correct=res.root_cause_correct,
                    in_top_3=res.in_top_3,
                    retrieval_precision=res.retrieval_precision,
                    retrieval_recall=res.retrieval_recall,
                    patch_passed_tests=res.patch_passed_tests,
                    execution_time_seconds=res.execution_time_seconds,
                    tokens_consumed=res.tokens_consumed,
                    cost_usd=res.cost_usd,
                    created_at=res.created_at.isoformat() if res.created_at else ""
                ) for res in results
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark evaluation failed: {e}")

@evaluations_router.get("/runs/{run_id}/csv")
async def export_evaluation_run_csv(run_id: str, db: AsyncSession = Depends(get_db)):
    """Exports an evaluation run's detailed results as a downloadable CSV."""
    run_stmt = select(EvaluationRun).filter(EvaluationRun.id == run_id)
    run = (await db.execute(run_stmt)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{run_id}' not found")

    csv_data = await BenchmarkService.export_run_to_csv(db, run_id=run_id)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=evaluation_run_{run_id[:8]}.csv"}
    )

@evaluations_router.get("/summary")
async def get_evaluations_summary(db: AsyncSession = Depends(get_db)):
    """Summary of model evaluation comparisons."""
    stmt = select(EvaluationRun).order_by(desc(EvaluationRun.created_at))
    runs = (await db.execute(stmt)).scalars().all()
    return {
        "total_evaluation_runs": len(runs),
        "models_evaluated": list(set(r.model_name for r in runs)),
        "recent_runs": [
            {
                "id": r.id,
                "name": r.name,
                "model": r.model_name,
                "accuracy": f"{(r.root_cause_accuracy * 100):.1f}%",
                "top_3_recall": f"{(r.top_3_recall * 100):.1f}%",
                "patch_pass_rate": f"{(r.patch_pass_rate * 100):.1f}%",
                "mttd": f"{r.mean_time_to_diagnosis_seconds:.1f}s",
                "avg_cost": f"${r.average_cost_per_incident_usd:.4f}",
                "date": r.created_at.isoformat() if r.created_at else ""
            } for r in runs[:6]
        ]
    }
