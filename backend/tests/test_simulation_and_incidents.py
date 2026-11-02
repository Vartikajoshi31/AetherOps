import pytest

@pytest.mark.asyncio
async def test_get_chaos_scenarios(client):
    res = await client.get("/api/incidents/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) >= 5
    keys = [s["key"] for s in scenarios]
    assert "db_pool_exhaustion" in keys
    assert "payment_retry_storm" in keys
    assert "shipping_npe" in keys

@pytest.mark.asyncio
async def test_simulate_chaos_incident(client):
    res = await client.post("/api/incidents/simulate", json={"scenario_key": "payment_retry_storm"})
    assert res.status_code == 200
    incident = res.json()
    assert incident["severity"] == "High"
    assert "payment-service" in incident["affected_services"]
    inc_id = incident["id"]

    # Verify logs and traces were generated
    detail_res = await client.get(f"/api/incidents/{inc_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["logs"]) >= 1
    assert len(detail["traces"]) >= 1

@pytest.mark.asyncio
async def test_ingest_log_and_trace(client):
    # First get an existing incident
    inc_list = await client.get("/api/incidents")
    inc_id = inc_list.json()[0]["id"]

    # Ingest custom log
    log_res = await client.post(
        f"/api/incidents/{inc_id}/logs",
        json={
            "service_name": "checkout-service",
            "level": "FATAL",
            "message": "Out of memory while processing order payload",
            "stack_trace": "MemoryError: Unable to allocate 512MB"
        }
    )
    assert log_res.status_code == 200
    assert log_res.json()["level"] == "FATAL"

    # Ingest custom trace
    trace_res = await client.post(
        f"/api/incidents/{inc_id}/traces",
        json={
            "service_name": "checkout-service",
            "operation_name": "POST /orders/checkout",
            "duration_ms": 124.5,
            "status_code": "500",
            "error_message": "MemoryError"
        }
    )
    assert trace_res.status_code == 200
    assert trace_res.json()["duration_ms"] == 124.5

@pytest.mark.asyncio
async def test_resolve_and_reopen_incident(client):
    inc_list = await client.get("/api/incidents")
    inc_id = inc_list.json()[0]["id"]

    # Resolve
    res = await client.post(
        f"/api/incidents/{inc_id}/resolve",
        json={"resolution_summary": "Mitigated by increasing DB connection pool to 20."}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "Resolved"

    # Reopen
    reopen_res = await client.post(f"/api/incidents/{inc_id}/reopen")
    assert reopen_res.status_code == 200
    assert reopen_res.json()["status"] == "Investigating"

@pytest.mark.asyncio
async def test_approve_patch(client):
    # Find incident with patch (INC-2026-0842 in seed data)
    patch_res = await client.get("/api/incidents/INC-2026-0842/patch")
    assert patch_res.status_code == 200
    patch = patch_res.json()
    assert patch is not None

    # Submit approval
    approval_res = await client.post(
        "/api/incidents/INC-2026-0842/approve",
        json={
            "action": "approved",
            "feedback": "LGTM, verified against test suite.",
            "create_github_pr": True
        }
    )
    assert approval_res.status_code == 200
    approval = approval_res.json()
    assert approval["action"] == "approved"
    assert approval["created_pr"] is True
    assert "github.com" in approval["github_pr_url"]
