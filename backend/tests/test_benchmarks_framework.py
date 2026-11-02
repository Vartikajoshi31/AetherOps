import pytest
from sqlalchemy import select, func
from app.models.evaluation import BenchmarkIncident, EvaluationRun
from app.models.repository import Repository
from app.services.benchmark_service import BenchmarkService
from app.services.repo_service import RepositoryIndexerService

@pytest.mark.asyncio
async def test_ensure_50_benchmarks_loaded(db_session):
    total = await BenchmarkService.ensure_benchmarks_loaded(db_session)
    assert total >= 50

    count_stmt = select(func.count(BenchmarkIncident.id))
    actual_count = (await db_session.execute(count_stmt)).scalar()
    assert actual_count >= 50

@pytest.mark.asyncio
async def test_run_benchmark_evaluation_suite(db_session):
    # Ensure repo is indexed in Qdrant for RAG recall evaluation
    repo_stmt = select(Repository).limit(1)
    repo = (await db_session.execute(repo_stmt)).scalar_one_or_none()
    if repo:
        await RepositoryIndexerService.index_repository(db_session, repository_id=repo.id)

    await BenchmarkService.ensure_benchmarks_loaded(db_session)
    run = await BenchmarkService.run_evaluation_suite(
        db=db_session,
        name="Automated Test Suite Run",
        model_name="gpt-4o",
        limit=3
    )
    assert run.completed_benchmarks == 3
    assert run.root_cause_accuracy > 0.0
    assert run.top_3_recall > 0.0
    assert run.evidence_retrieval_recall > 0.0
    assert run.status == "completed"

    csv_data = await BenchmarkService.export_run_to_csv(db_session, run_id=run.id)
    assert "Benchmark ID" in csv_data
    assert "Incident Title" in csv_data
    assert "Root Cause Correct" in csv_data

@pytest.mark.asyncio
async def test_evaluations_api_endpoints(client):
    # Test GET /api/evaluations/benchmarks
    res = await client.get("/api/evaluations/benchmarks")
    assert res.status_code == 200
    benchmarks = res.json()
    assert len(benchmarks) >= 50

    # Test GET /api/evaluations/summary
    summary_res = await client.get("/api/evaluations/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert "total_evaluation_runs" in summary
    assert "recent_runs" in summary
