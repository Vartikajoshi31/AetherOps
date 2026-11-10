import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_trace_negative_duration_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Ingest trace with duration_ms < 0 should fail validation
        res = await ac.post("/api/incidents/INC-2026-0891/traces", json={
            "service_name": "checkout-service",
            "operation_name": "db.acquire",
            "duration_ms": -15.5
        })
        assert res.status_code == 422

@pytest.mark.asyncio
async def test_resolve_empty_summary_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Empty resolution summary should fail validation
        res = await ac.post("/api/incidents/INC-2026-0891/resolve", json={
            "resolution_summary": ""
        })
        assert res.status_code == 422

@pytest.mark.asyncio
async def test_log_empty_message_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Empty log message should fail validation
        res = await ac.post("/api/incidents/INC-2026-0891/logs", json={
            "service_name": "checkout-service",
            "message": ""
        })
        assert res.status_code == 422

@pytest.mark.asyncio
async def test_approval_invalid_action_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Invalid approval action
        res = await ac.post("/api/incidents/INC-2026-0891/approve", json={
            "action": "unauthorized_bypass_action",
            "feedback": "Trying to bypass approval enum",
            "create_github_pr": False
        })
        assert res.status_code == 400
        assert "Invalid action" in res.json()["detail"]

@pytest.mark.asyncio
async def test_delete_incident_and_cascade():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create temporary incident
        create_res = await ac.post("/api/incidents", json={
            "title": "Incident To Be Deleted",
            "description": "Transient test incident for delete endpoint verification",
            "severity": "Low",
            "affected_services": ["order-service"]
        })
        assert create_res.status_code == 201
        temp_id = create_res.json()["id"]

        # Ingest log for it
        await ac.post(f"/api/incidents/{temp_id}/logs", json={
            "service_name": "order-service",
            "message": "Temporary log message"
        })

        # Delete it
        del_res = await ac.delete(f"/api/incidents/{temp_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "success"

        # Verify 404 on fetch
        fetch_res = await ac.get(f"/api/incidents/{temp_id}")
        assert fetch_res.status_code == 404

        # Delete again should return 404
        del_again = await ac.delete(f"/api/incidents/{temp_id}")
        assert del_again.status_code == 404

@pytest.mark.asyncio
async def test_csv_export_non_existent_run():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/evaluations/runs/non-existent-run-id-9999/csv")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_service_filter_pagination():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/incidents?service=checkout-service&limit=10&offset=0")
        assert res.status_code == 200
        incidents = res.json()
        for inc in incidents:
            assert "checkout-service" in inc["affected_services"]

@pytest.mark.asyncio
async def test_rag_search_with_hints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/rag/search", json={
            "query": "Database connection pool acquire",
            "limit": 3,
            "target_file_hint": "db.py",
            "target_func_hint": "acquire"
        })
        assert res.status_code == 200
        results = res.json()
        assert len(results) > 0
        assert any("db.py" in r["file_path"] for r in results)
