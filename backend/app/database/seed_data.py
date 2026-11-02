import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, Organization
from app.models.repository import Repository, Service
from app.models.incident import Incident, IncidentEvent, IncidentLog, IncidentTrace, Deployment
from app.models.agent_run import AgentRun, AgentEvent, RootCauseHypothesis, InvestigationReport
from app.models.evidence import EvidenceItem, RetrievedDocument
from app.models.patch import Patch, PatchValidation, Approval
from app.models.evaluation import BenchmarkIncident, EvaluationRun, EvaluationResult, UsageMetric

async def seed_initial_data(session: AsyncSession):
    # Check if organization already exists
    stmt = select(Organization).filter_by(slug="acme-corp")
    result = await session.execute(stmt)
    existing_org = result.scalar_one_or_none()
    if existing_org:
        return  # Already seeded

    # 1. Create Organization
    org = Organization(
        id=str(uuid.uuid4()),
        name="Acme Global E-Commerce",
        slug="acme-corp",
        plan="enterprise"
    )
    session.add(org)
    await session.flush()

    # 2. Create Default Admin User
    user = User(
        id=str(uuid.uuid4()),
        email="sre@acme.corp",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQmG6KA5WsgM/B5/D2mca", # secret123
        full_name="Staff Reliability Engineer",
        role="admin",
        is_active=True,
        organization_id=org.id
    )
    session.add(user)

    # 3. Create Sample Repositories & Services
    repo = Repository(
        id=str(uuid.uuid4()),
        name="ecommerce-platform",
        full_name="acme/ecommerce-platform",
        default_branch="main",
        clone_url="https://github.com/acme/ecommerce-platform.git",
        local_path="./demo-services",
        indexed_at=datetime.utcnow().isoformat(),
        index_status="indexed",
        total_files=24,
        organization_id=org.id
    )
    session.add(repo)
    await session.flush()

    service_checkout = Service(
        id=str(uuid.uuid4()),
        name="checkout-service",
        description="Checkout workflow and cart transaction processing",
        tier="critical",
        language="python",
        health_status="degraded",
        current_error_rate="18.4%",
        repository_id=repo.id,
        service_metadata={"runtime": "Python 3.12", "port": 8081}
    )
    service_payment = Service(
        id=str(uuid.uuid4()),
        name="payment-service",
        description="Payment gateway integration and tokenization",
        tier="critical",
        language="python",
        health_status="healthy",
        current_error_rate="0.05%",
        repository_id=repo.id,
        service_metadata={"runtime": "Python 3.12", "port": 8082}
    )
    service_inventory = Service(
        id=str(uuid.uuid4()),
        name="inventory-service",
        description="Warehouse stock levels and inventory reservations",
        tier="standard",
        language="python",
        health_status="healthy",
        current_error_rate="0.00%",
        repository_id=repo.id,
        service_metadata={"runtime": "Python 3.12", "port": 8083}
    )
    service_order = Service(
        id=str(uuid.uuid4()),
        name="order-service",
        description="Order fulfillment state machine and notifications",
        tier="critical",
        language="python",
        health_status="healthy",
        current_error_rate="0.10%",
        repository_id=repo.id,
        service_metadata={"runtime": "Python 3.12", "port": 8084}
    )
    session.add_all([service_checkout, service_payment, service_inventory, service_order])
    await session.flush()

    # 4. Deployments
    dep1 = Deployment(
        id=str(uuid.uuid4()),
        service_id=service_checkout.id,
        repository_id=repo.id,
        commit_sha="a7b4c81d",
        commit_message="perf: optimize database connection pooling for high concurrency",
        author="DevOps Team <devops@acme.corp>",
        deployed_at=datetime.utcnow() - timedelta(hours=2),
        status="succeeded",
        environment="production"
    )
    dep2 = Deployment(
        id=str(uuid.uuid4()),
        service_id=service_payment.id,
        repository_id=repo.id,
        commit_sha="3f9e20a4",
        commit_message="feat: add exponential backoff for third-party payment gateway",
        author="Payment Team <payments@acme.corp>",
        deployed_at=datetime.utcnow() - timedelta(days=1),
        status="succeeded",
        environment="production"
    )
    session.add_all([dep1, dep2])
    await session.flush()

    # 5. Create Seed Incidents
    # Incident 1: Critical - Detected
    inc1 = Incident(
        id="INC-2026-0891",
        title="Database Connection Pool Exhaustion in checkout-service",
        description="Spike in HTTP 500 errors during peak checkout traffic. checkout-service reports TimeoutError: QueuePool limit of size 10 overflow 10 reached, connection timed out, timeout 30.00.",
        severity="Critical",
        status="Detected",
        affected_services=["checkout-service", "payment-service"],
        error_rate="18.4%",
        detection_source="Datadog Alert: checkout-service 5xx Error Rate > 5%",
        start_time=datetime.utcnow() - timedelta(minutes=25),
        organization_id=org.id,
        deployment_id=dep1.id,
        tags=["database", "concurrency", "checkout-service", "p0"]
    )
    session.add(inc1)

    # Incident 2: High - Fix Generated
    inc2 = Incident(
        id="INC-2026-0842",
        title="Payment Gateway API Timeout & Thundering Herd Retry Storm",
        description="Upstream payment provider transient 504 errors triggered synchronous retries without jitter, multiplying load 8x and overflowing gateway queues.",
        severity="High",
        status="Fix Generated",
        affected_services=["payment-service"],
        error_rate="7.2%",
        detection_source="Prometheus Alert: PaymentGatewayHighLatency",
        start_time=datetime.utcnow() - timedelta(hours=3),
        organization_id=org.id,
        deployment_id=dep2.id,
        tags=["network", "retry", "payment-service"]
    )
    session.add(inc2)

    # Incident 3: Medium - Resolved
    inc3 = Incident(
        id="INC-2026-0799",
        title="Memory Leak in Inventory Cache Invalidation Loop",
        description="Process RSS grew continuously by 150MB/hour due to unbounded dictionary cache storing redundant SKU invalidation keys.",
        severity="Medium",
        status="Resolved",
        affected_services=["inventory-service"],
        error_rate="0.00%",
        detection_source="AWS CloudWatch: MemoryUtilizationHigh",
        start_time=datetime.utcnow() - timedelta(days=2),
        resolved_at=datetime.utcnow() - timedelta(days=1, hours=22),
        root_cause_summary="Unbounded dictionary in inventory cache missing TTL expiry key evictions.",
        resolution_summary="Applied LRU eviction policy with maxsize=10000 and 300s TTL. Validated in sandbox with 0 regressions.",
        organization_id=org.id,
        tags=["memory", "cache", "inventory-service"]
    )
    session.add(inc3)

    # Incident 4: High - Root Cause Identified
    inc4 = Incident(
        id="INC-2026-0720",
        title="Null Pointer Exception in Order Shipping Calculation",
        description="TypeError: 'NoneType' object has no attribute 'country_code' when orders have digital delivery items without physical address.",
        severity="High",
        status="Root Cause Identified",
        affected_services=["order-service"],
        error_rate="4.1%",
        detection_source="Sentry Issue: TypeError: shipping_address is None",
        start_time=datetime.utcnow() - timedelta(hours=8),
        root_cause_summary="Missing defensive check for optional shipping address on digital goods orders in calculate_shipping_cost.",
        organization_id=org.id,
        tags=["npe", "order-service", "sentry"]
    )
    session.add(inc4)
    await session.flush()

    # 6. Add Detailed Logs for Incident 1
    log1 = IncidentLog(
        id=str(uuid.uuid4()),
        incident_id=inc1.id,
        service_name="checkout-service",
        level="ERROR",
        timestamp=datetime.utcnow() - timedelta(minutes=24),
        message="sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached, connection timed out, timeout 30.00",
        stack_trace="""File "/app/services/checkout/api.py", line 112, in create_checkout_session
    async with get_db_connection() as conn:
File "/app/services/checkout/db.py", line 45, in get_db_connection
    conn = await pool.acquire(timeout=30.0)
sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached, connection timed out, timeout 30.00""",
        log_attributes={"pool_size": 10, "checked_out": 20, "wait_queue": 42}
    )
    log2 = IncidentLog(
        id=str(uuid.uuid4()),
        incident_id=inc1.id,
        service_name="checkout-service",
        level="ERROR",
        timestamp=datetime.utcnow() - timedelta(minutes=23),
        message="HTTP 500 Internal Server Error POST /api/v1/checkout/orders",
        stack_trace=None,
        log_attributes={"status_code": 500, "client_ip": "10.0.4.12", "latency_ms": 30045}
    )
    log3 = IncidentLog(
        id=str(uuid.uuid4()),
        incident_id=inc1.id,
        service_name="payment-service",
        level="WARN",
        timestamp=datetime.utcnow() - timedelta(minutes=22),
        message="Upstream gateway response delayed: 1420ms for merchant_id=m_9941",
        stack_trace=None,
        log_attributes={"merchant_id": "m_9941", "duration_ms": 1420}
    )
    session.add_all([log1, log2, log3])

    # 7. Add Traces for Incident 1
    trace1 = IncidentTrace(
        id=str(uuid.uuid4()),
        incident_id=inc1.id,
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
        span_id="00f067aa0ba902b7",
        parent_span_id=None,
        service_name="checkout-service",
        operation_name="POST /api/v1/checkout/orders",
        duration_ms=30048.2,
        status_code="500",
        error_message="QueuePool limit reached, connection timed out",
        trace_metadata={"http.method": "POST", "http.status_code": 500}
    )
    trace2 = IncidentTrace(
        id=str(uuid.uuid4()),
        incident_id=inc1.id,
        trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
        span_id="5fb397be34d23b0f",
        parent_span_id="00f067aa0ba902b7",
        service_name="checkout-service",
        operation_name="db.acquire_connection",
        duration_ms=30002.1,
        status_code="ERROR",
        error_message="TimeoutError: QueuePool limit of size 10 overflow 10 reached",
        trace_metadata={"db.system": "postgresql", "db.pool.checked_out": 20}
    )
    session.add_all([trace1, trace2])

    # 8. Events for Incident 1
    ev1 = IncidentEvent(
        id=str(uuid.uuid4()),
        incident_id=inc1.id,
        event_type="incident_detected",
        message="Incident detected automatically from Datadog webhook alert: 5xx rate spiked to 18.4%",
        actor="Datadog AlertManager",
        event_metadata={"threshold": "5%", "observed": "18.4%"}
    )
    session.add(ev1)

    # 9. Add Verified Evidence for Incident 2
    patch2 = Patch(
        id=str(uuid.uuid4()),
        incident_id=inc2.id,
        title="Add Full Jitter Exponential Backoff to Payment Gateway Client",
        explanation="Introduces randomized Decorrelated Jitter to payment gateway retries, preventing synchronous client pile-ups on transient timeouts.",
        diff_content="""--- a/services/payment/client.py
+++ b/services/payment/client.py
@@ -34,7 +34,8 @@ class PaymentGatewayClient:
     async def execute_with_retry(self, request_payload: dict, max_retries: int = 3):
         for attempt in range(max_retries):
             try:
                 return await self._send_request(request_payload)
             except GatewayTimeoutException:
-                delay = self.base_backoff * (2 ** attempt)
+                import random
+                delay = random.uniform(0, self.base_backoff * (2 ** attempt))
                 await asyncio.sleep(delay)
""",
        affected_files=["services/payment/client.py"],
        regression_tests="""def test_payment_retry_jitter():
    delays = [calculate_retry_delay(attempt=1, base=1.0) for _ in range(50)]
    assert len(set(delays)) > 30, "Retry delays must contain randomized jitter"
""",
        status="validated_success"
    )
    session.add(patch2)
    await session.flush()

    val2 = PatchValidation(
        id=str(uuid.uuid4()),
        patch_id=patch2.id,
        status="passed",
        syntax_valid=True,
        tests_passed=True,
        total_tests="14",
        passed_tests="14",
        failed_tests="0",
        execution_time_seconds=2.41,
        memory_peak_mb=68.4,
        stdout_output="tests/test_payment.py::test_payment_retry_jitter PASSED [ 7%]\ntests/test_payment.py::test_gateway_idempotency PASSED [14%]\n14 passed in 2.41s",
        stderr_output="",
        regression_detected=False,
        validation_summary="Isolated Docker sandbox run passed all 14 unit and regression tests with zero detected regressions."
    )
    session.add(val2)

    # 10. Benchmark Incidents (Seeded dataset for evaluation)
    benchmarks = [
        BenchmarkIncident(
            id=str(uuid.uuid4()),
            benchmark_id="BENCH-001",
            title="Database Connection Pool Leak in Exception Handler",
            category="database",
            service_name="checkout-service",
            ground_truth_root_cause="Database connection acquired outside try-finally block not returned to pool when PaymentException is raised.",
            ground_truth_culprit_files=["services/checkout/db.py", "services/checkout/api.py"],
            ground_truth_patch_diff="Use 'async with get_db_connection() as conn:' context manager to ensure safe connection release on all exit branches.",
            simulated_logs=[{"message": "QueuePool limit of size 10 overflow 10 reached", "level": "ERROR"}],
            simulated_traces=[{"operation": "db.acquire_connection", "duration_ms": 30000}],
            test_verification_command="pytest tests/test_checkout_pool.py"
        ),
        BenchmarkIncident(
            id=str(uuid.uuid4()),
            benchmark_id="BENCH-002",
            title="Thundering Herd on Payment Gateway Retry Without Jitter",
            category="network_timeout",
            service_name="payment-service",
            ground_truth_root_cause="Deterministic exponential backoff causes all failing client requests to retry at the exact same millisecond interval.",
            ground_truth_culprit_files=["services/payment/client.py"],
            ground_truth_patch_diff="Add random uniform jitter between 0 and exponential backoff interval.",
            simulated_logs=[{"message": "Upstream gateway returned 504 Gateway Timeout", "level": "WARN"}],
            simulated_traces=[{"operation": "gateway.process_charge", "duration_ms": 5000}],
            test_verification_command="pytest tests/test_payment_retry.py"
        ),
        BenchmarkIncident(
            id=str(uuid.uuid4()),
            benchmark_id="BENCH-003",
            title="Unbounded Cache Memory Leak in SKU Invalidation",
            category="memory_leak",
            service_name="inventory-service",
            ground_truth_root_cause="Standard dictionary used for in-memory cache without max size limit or TTL eviction policy.",
            ground_truth_culprit_files=["services/inventory/cache.py"],
            ground_truth_patch_diff="Replace raw dictionary with collections.OrderedDict with LRU eviction and 300-second expiration.",
            simulated_logs=[{"message": "Process memory RSS exceeds 1024MB", "level": "WARN"}],
            simulated_traces=[{"operation": "cache.set_sku", "duration_ms": 0.5}],
            test_verification_command="pytest tests/test_inventory_cache.py"
        ),
        BenchmarkIncident(
            id=str(uuid.uuid4()),
            benchmark_id="BENCH-004",
            title="Null Pointer Dereference on Digital Orders Shipping Address",
            category="npe",
            service_name="order-service",
            ground_truth_root_cause="calculate_shipping_cost directly accesses order.shipping_address.country_code without checking if shipping_address is None.",
            ground_truth_culprit_files=["services/order/shipping.py"],
            ground_truth_patch_diff="Return 0.0 shipping cost early when order is digital or shipping_address is None.",
            simulated_logs=[{"message": "AttributeError: 'NoneType' object has no attribute 'country_code'", "level": "ERROR"}],
            simulated_traces=[{"operation": "order.calculate_shipping", "duration_ms": 2.1}],
            test_verification_command="pytest tests/test_shipping.py"
        ),
        BenchmarkIncident(
            id=str(uuid.uuid4()),
            benchmark_id="BENCH-005",
            title="Race Condition in Warehouse Stock Reservation",
            category="concurrency",
            service_name="inventory-service",
            ground_truth_root_cause="Read-modify-write on available item quantity without atomic database UPDATE with WHERE quantity >= required.",
            ground_truth_culprit_files=["services/inventory/stock.py"],
            ground_truth_patch_diff="Use atomic SQL UPDATE inventory SET quantity = quantity - :qty WHERE sku = :sku AND quantity >= :qty RETURNING id.",
            simulated_logs=[{"message": "Inventory negative stock detected for SKU-4991", "level": "FATAL"}],
            simulated_traces=[{"operation": "stock.reserve", "duration_ms": 15.2}],
            test_verification_command="pytest tests/test_stock_concurrency.py"
        )
    ]
    session.add_all(benchmarks)

    # 11. Initial Evaluation Run
    eval_run = EvaluationRun(
        id=str(uuid.uuid4()),
        name="Production Baseline Evaluation v1.0",
        model_name="gpt-4o",
        total_benchmarks=5,
        completed_benchmarks=5,
        status="completed",
        root_cause_accuracy=0.92,
        top_3_recall=0.98,
        evidence_retrieval_precision=0.89,
        evidence_retrieval_recall=0.94,
        patch_pass_rate=0.88,
        regression_rate=0.02,
        mean_time_to_diagnosis_seconds=34.2,
        average_tokens_per_incident=6240,
        average_cost_per_incident_usd=0.068
    )
    session.add(eval_run)
    await session.flush()

    res1 = EvaluationResult(
        id=str(uuid.uuid4()),
        run_id=eval_run.id,
        benchmark_id="BENCH-001",
        incident_title="Database Connection Pool Leak in Exception Handler",
        identified_root_cause="Connection leak in checkout-service/db.py where connections are unreleased during payment gateway timeouts.",
        ground_truth_root_cause="Database connection acquired outside try-finally block not returned to pool when PaymentException is raised.",
        root_cause_correct=True,
        in_top_3=True,
        retrieval_precision=0.92,
        retrieval_recall=0.96,
        patch_passed_tests=True,
        execution_time_seconds=31.4,
        tokens_consumed=6410,
        cost_usd=0.071
    )
    res2 = EvaluationResult(
        id=str(uuid.uuid4()),
        run_id=eval_run.id,
        benchmark_id="BENCH-002",
        incident_title="Thundering Herd on Payment Gateway Retry Without Jitter",
        identified_root_cause="Missing random jitter in payment retry backoff causing synchronized upstream gateway overload.",
        ground_truth_root_cause="Deterministic exponential backoff causes all failing client requests to retry at the exact same millisecond interval.",
        root_cause_correct=True,
        in_top_3=True,
        retrieval_precision=0.88,
        retrieval_recall=0.91,
        patch_passed_tests=True,
        execution_time_seconds=28.9,
        tokens_consumed=5820,
        cost_usd=0.062
    )
    session.add_all([res1, res2])

    await session.commit()
