import pytest
import os
from sqlalchemy import select
from app.models.incident import Incident
from app.models.agent_run import AgentRun
from app.agents.triage import triage_agent
from app.agents.log_analysis import log_analysis_agent
from app.agents.code_investigation import code_investigation_agent
from app.agents.root_cause import root_cause_agent
from app.agents.fix_generation import fix_generation_agent
from app.agents.validation import validation_agent
from app.agents.review import review_agent
from app.sandbox.runner import sandbox_runner
from app.orchestration.graph import investigation_graph
from app.services.investigation_service import InvestigationService

@pytest.mark.asyncio
async def test_triage_agent():
    state = {
        "title": "Checkout Service Connection Pool Exhaustion",
        "description": "QueuePool limit of size 10 overflow reached",
        "affected_services": ["checkout-service"],
        "severity": "Critical",
        "error_rate": "34.8%"
    }
    res = await triage_agent.run(state)
    assert "data" in res
    data = res["data"]
    assert data["category"] == "database_connection_leak"
    assert data["primary_service"] == "checkout-service"
    assert len(data["recommended_investigation_steps"]) >= 3

@pytest.mark.asyncio
async def test_log_analysis_agent():
    state = {
        "title": "Payment Thundering Herd",
        "description": "504 Gateway Timeout storm",
        "logs": [
            {
                "service_name": "payment-service",
                "level": "ERROR",
                "message": "GatewayTimeout: 504 Gateway Timeout during payment charge",
                "stack_trace": 'File "payment-service/client.py", line 22, in calculate_retry_delay'
            }
        ]
    }
    res = await log_analysis_agent.run(state)
    data = res["data"]
    assert "culprit_module" in data
    assert "payment-service/client.py" in data["culprit_module"]
    assert len(data["extracted_evidence"]) > 0

@pytest.mark.asyncio
async def test_sandbox_validation_runner():
    res = await sandbox_runner.run_sandboxed_validation(
        service_name="checkout-service",
        affected_file="checkout-service/db.py",
        diff_patch="--- a/checkout-service/db.py\n+++ b/checkout-service/db.py\n",
        regression_test_code="def test_sanity(): assert 1 + 1 == 2\n",
        timeout_seconds=15
    )
    assert res.syntax_valid is True
    assert res.success is True
    assert res.duration_seconds > 0.0

@pytest.mark.asyncio
async def test_langgraph_workflow_execution():
    initial_state = {
        "incident_id": "test-inc-001",
        "title": "Order Processing Shipping Null Pointer",
        "description": "AttributeError NoneType object has no attribute country_code",
        "severity": "High",
        "affected_services": ["order-service"],
        "error_rate": "12.4%",
        "logs": [
            {
                "service_name": "order-service",
                "level": "CRITICAL",
                "message": "AttributeError: 'NoneType' object has no attribute 'country_code'",
                "stack_trace": 'File "order-service/shipping.py", line 14, in calculate_shipping_cost'
            }
        ],
        "traces": [],
        "repo_path": "demo-services",
        "retry_count": 0,
        "max_retries": 1,
        "current_stage": "Init",
        "agent_events": [],
        "total_tokens": 0,
        "total_cost": 0.0
    }

    final_state = await investigation_graph.ainvoke(initial_state)

    assert "triage_result" in final_state
    assert "log_analysis_result" in final_state
    assert "code_investigation_result" in final_state
    assert "root_cause_analysis" in final_state
    assert "proposed_patch" in final_state
    assert "validation_result" in final_state
    assert "review_result" in final_state
    assert final_state["current_stage"] == "Awaiting Approval"
    assert len(final_state["agent_events"]) >= 5

@pytest.mark.asyncio
async def test_investigation_service_and_api(db_session, client):
    # Fetch active incident
    stmt = select(Incident).filter(Incident.status != "Resolved").limit(1)
    incident = (await db_session.execute(stmt)).scalar_one_or_none()
    assert incident is not None

    # Call POST /api/incidents/{id}/investigate
    response = await client.post(
        f"/api/incidents/{incident.id}/investigate",
        json={"max_steps": 10}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["incident_id"] == incident.id
    assert res_data["current_stage"] == "Awaiting Approval"

    # Verify AgentRun was persisted in DB
    run_stmt = select(AgentRun).filter(AgentRun.incident_id == incident.id)
    run = (await db_session.execute(run_stmt)).scalars().first()
    assert run is not None
    assert run.status == "paused_awaiting_approval"
    assert run.step_count >= 5

    # Test GET /api/investigations
    inv_res = await client.get("/api/investigations")
    assert inv_res.status_code == 200
    runs = inv_res.json()
    assert len(runs) >= 1

    # Test GET /api/investigations/{run_id}
    detail_res = await client.get(f"/api/investigations/{run.id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["events"]) >= 5
    assert "graph_state" in detail
