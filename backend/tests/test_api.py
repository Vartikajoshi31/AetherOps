import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "AgentOps AI" in data["service"]

@pytest.mark.asyncio
async def test_get_dashboard_metrics(client):
    response = await client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_incidents" in data
    assert data["total_incidents"] >= 4
    assert "active_incidents" in data
    assert "service_health" in data
    assert len(data["service_health"]) == 4

@pytest.mark.asyncio
async def test_list_incidents(client):
    response = await client.get("/api/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert len(incidents) >= 4
    first = incidents[0]
    assert "id" in first
    assert "title" in first
    assert "severity" in first
    assert "status" in first

@pytest.mark.asyncio
async def test_create_and_fetch_incident(client):
    payload = {
        "title": "E2E Test Database Connection Timeout",
        "description": "Simulated connection pool timeout in order-service",
        "severity": "Critical",
        "affected_services": ["order-service"],
        "error_rate": "22.5%",
        "detection_source": "Automated Unit Test",
        "initial_log_message": "OperationalError: connection refused"
    }
    create_res = await client.post("/api/incidents", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["title"] == payload["title"]
    assert created["severity"] == "Critical"
    inc_id = created["id"]

    # Fetch detail
    get_res = await client.get(f"/api/incidents/{inc_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["id"] == inc_id
    assert len(detail["events"]) >= 1
    assert len(detail["logs"]) >= 1

@pytest.mark.asyncio
async def test_benchmarks_list(client):
    response = await client.get("/api/evaluations/benchmarks")
    assert response.status_code == 200
    benchmarks = response.json()
    assert len(benchmarks) >= 5
    assert benchmarks[0]["benchmark_id"] == "BENCH-001"
