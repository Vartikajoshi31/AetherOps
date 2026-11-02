import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.incident import Incident, IncidentEvent, IncidentLog, IncidentTrace, Deployment
from app.models.repository import Service, Repository
from app.models.patch import Patch, PatchValidation, Approval
from app.models.agent_run import AgentRun, AgentEvent, RootCauseHypothesis, InvestigationReport
from app.models.evidence import EvidenceItem, RetrievedDocument
from app.database.seed_data import seed_initial_data

def utcnow():
    return datetime.now(timezone.utc)

CHAOS_SCENARIOS = {
    "db_pool_exhaustion": {
        "title": "Database Connection Pool Exhaustion in checkout-service",
        "description": "Peak checkout traffic exhausted database pool. checkout-service reports QueuePool limit reached with 10 overflow connections after slow gateway responses.",
        "severity": "Critical",
        "service": "checkout-service",
        "error_rate": "28.4%",
        "detection_source": "Datadog 5xx Alert",
        "tags": ["database", "concurrency", "p0"],
        "logs": [
            {
                "level": "ERROR",
                "message": "sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached, connection timed out, timeout 30.00",
                "stack_trace": """File "services/checkout/db.py", line 45, in acquire\n    conn = await pool.acquire(timeout=30.0)\nsqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached""",
                "attributes": {"pool_size": 10, "checked_out": 20, "waiters": 45}
            },
            {
                "level": "ERROR",
                "message": "HTTP 500 Internal Server Error POST /api/v1/checkout/orders",
                "stack_trace": None,
                "attributes": {"status_code": 500, "latency_ms": 30045}
            }
        ],
        "traces": [
            {"op": "POST /api/v1/checkout/orders", "duration_ms": 30045.0, "status": "500", "error": "QueuePool limit reached"},
            {"op": "db.acquire_connection", "duration_ms": 30001.2, "status": "ERROR", "error": "TimeoutError: QueuePool limit of size 10 overflow 10 reached"}
        ],
        "root_cause": "Database connection acquired outside try-finally block in checkout-service/db.py not returned to pool when payment gateway timeout is raised."
    },
    "payment_retry_storm": {
        "title": "Payment Gateway API Timeout & Thundering Herd Retry Storm",
        "description": "Upstream payment provider transient 504 errors triggered synchronous retries without jitter, multiplying load 8x and overwhelming the payment service.",
        "severity": "High",
        "service": "payment-service",
        "error_rate": "12.8%",
        "detection_source": "Prometheus Alert: PaymentGatewayHighLatency",
        "tags": ["network", "retry", "payment-service"],
        "logs": [
            {
                "level": "WARN",
                "message": "Upstream gateway response delayed: 504 Gateway Timeout for merchant_id=m_9941",
                "stack_trace": None,
                "attributes": {"merchant_id": "m_9941", "retry_attempt": 3}
            },
            {
                "level": "ERROR",
                "message": "GatewayTimeoutException: Synchronous backoff retry surge flooded outbound connection pool",
                "stack_trace": """File "services/payment/client.py", line 22, in calculate_retry_delay\n    backoff = self.base_backoff * (2 ** attempt)\nGatewayTimeoutException: Synchronous retry storm""",
                "attributes": {"retries_count": 850}
            }
        ],
        "traces": [
            {"op": "POST /api/v1/payments/charge", "duration_ms": 5020.0, "status": "504", "error": "Upstream 504 Gateway Timeout"},
            {"op": "http.retry_backoff", "duration_ms": 4000.0, "status": "WARN", "error": "Synchronized retry spike"}
        ],
        "root_cause": "Deterministic exponential backoff causes all failing client requests to retry at the exact same millisecond interval without randomized jitter."
    },
    "cache_memory_leak": {
        "title": "Memory Starvation in Inventory Cache Invalidation Loop",
        "description": "Process RSS grew continuously by 150MB/hour due to unbounded dictionary cache storing redundant SKU invalidation keys without TTL eviction.",
        "severity": "Medium",
        "service": "inventory-service",
        "error_rate": "0.00%",
        "detection_source": "AWS CloudWatch: MemoryUtilizationHigh",
        "tags": ["memory", "cache", "inventory-service"],
        "logs": [
            {
                "level": "WARN",
                "message": "Process memory RSS exceeds 1024MB (threshold: 750MB)",
                "stack_trace": None,
                "attributes": {"current_rss_mb": 1140, "growth_rate": "150MB/hr"}
            }
        ],
        "traces": [
            {"op": "cache.set_sku_invalidation", "duration_ms": 0.4, "status": "200", "error": None}
        ],
        "root_cause": "Raw dictionary used for in-memory cache without max size limit or TTL eviction policy in inventory-service/cache.py."
    },
    "shipping_npe": {
        "title": "Null Pointer Exception in Order Shipping Calculation",
        "description": "TypeError: 'NoneType' object has no attribute 'country_code' when orders containing digital goods have no physical shipping address.",
        "severity": "High",
        "service": "order-service",
        "error_rate": "6.3%",
        "detection_source": "Sentry Issue: TypeError: shipping_address is None",
        "tags": ["npe", "order-service", "sentry"],
        "logs": [
            {
                "level": "ERROR",
                "message": "TypeError: 'NoneType' object has no attribute 'country_code'",
                "stack_trace": """File "services/order/shipping.py", line 26, in calculate_shipping_cost\n    country = order.shipping_address.country_code.upper()\nAttributeError: 'NoneType' object has no attribute 'country_code'""",
                "attributes": {"order_id": "ord-8812", "is_digital": True}
            }
        ],
        "traces": [
            {"op": "POST /api/v1/orders/checkout", "duration_ms": 14.2, "status": "500", "error": "TypeError: 'NoneType' object has no attribute 'country_code'"}
        ],
        "root_cause": "calculate_shipping_cost directly accesses order.shipping_address.country_code without checking if shipping_address is None on digital items."
    },
    "stock_race_condition": {
        "title": "Race Condition in Warehouse Stock Reservation",
        "description": "Concurrent checkout requests for limited stock resulted in negative inventory levels due to non-atomic read-modify-write queries.",
        "severity": "Critical",
        "service": "inventory-service",
        "error_rate": "15.7%",
        "detection_source": "Database Integrity Constraint Check",
        "tags": ["concurrency", "inventory", "p0"],
        "logs": [
            {
                "level": "FATAL",
                "message": "Negative inventory level detected for SKU-4991: quantity = -3",
                "stack_trace": """File "services/inventory/stock.py", line 32, in reserve_stock\n    raise IntegrityError("Negative stock quantity detected")""",
                "attributes": {"sku": "SKU-4991", "observed_quantity": -3}
            }
        ],
        "traces": [
            {"op": "stock.reserve", "duration_ms": 28.4, "status": "409", "error": "IntegrityError: Negative inventory level detected"}
        ],
        "root_cause": "Non-atomic inventory check and deduct allows interleaved concurrent transactions to oversell stock."
    }
}

class SimulationService:
    @staticmethod
    def get_available_scenarios() -> List[Dict[str, Any]]:
        return [
            {
                "key": k,
                "title": v["title"],
                "service": v["service"],
                "severity": v["severity"],
                "description": v["description"]
            }
            for k, v in CHAOS_SCENARIOS.items()
        ]

    @staticmethod
    async def simulate_incident(session: AsyncSession, scenario_key: str = "db_pool_exhaustion") -> Incident:
        scenario = CHAOS_SCENARIOS.get(scenario_key, CHAOS_SCENARIOS["db_pool_exhaustion"])
        now = utcnow()
        inc_id = f"INC-{now.year}-{str(uuid.uuid4())[:4].upper()}"

        incident = Incident(
            id=inc_id,
            title=scenario["title"],
            description=scenario["description"],
            severity=scenario["severity"],
            status="Detected",
            affected_services=[scenario["service"]],
            error_rate=scenario["error_rate"],
            detection_source=scenario["detection_source"],
            tags=scenario["tags"],
            start_time=now,
            root_cause_summary=None
        )
        session.add(incident)
        await session.flush()

        # Audit Event
        ev = IncidentEvent(
            id=str(uuid.uuid4()),
            incident_id=incident.id,
            event_type="chaos_injected",
            message=f"Chaos injection triggered: {scenario['title']}",
            actor="Chaos Simulator Engine",
            event_metadata={"scenario": scenario_key, "service": scenario["service"]}
        )
        session.add(ev)

        # Ingest simulated logs
        for log_data in scenario.get("logs", []):
            log_item = IncidentLog(
                id=str(uuid.uuid4()),
                incident_id=incident.id,
                service_name=scenario["service"],
                level=log_data["level"],
                timestamp=now,
                message=log_data["message"],
                stack_trace=log_data.get("stack_trace"),
                log_attributes=log_data.get("attributes", {})
            )
            session.add(log_item)

        # Ingest simulated distributed traces
        trace_id = uuid.uuid4().hex
        for tr in scenario.get("traces", []):
            trace_item = IncidentTrace(
                id=str(uuid.uuid4()),
                incident_id=incident.id,
                trace_id=trace_id,
                span_id=uuid.uuid4().hex[:16],
                service_name=scenario["service"],
                operation_name=tr["op"],
                duration_ms=tr["duration_ms"],
                status_code=tr["status"],
                error_message=tr.get("error"),
                trace_metadata={"http.method": "POST", "scenario": scenario_key}
            )
            session.add(trace_item)

        await session.commit()
        return incident

    @staticmethod
    async def reset_demo_state(session: AsyncSession):
        """Wipe incidents and re-seed clean pristine demo state."""
        await session.execute(delete(Approval))
        await session.execute(delete(PatchValidation))
        await session.execute(delete(Patch))
        await session.execute(delete(EvidenceItem))
        await session.execute(delete(RetrievedDocument))
        await session.execute(delete(InvestigationReport))
        await session.execute(delete(RootCauseHypothesis))
        await session.execute(delete(AgentEvent))
        await session.execute(delete(AgentRun))
        await session.execute(delete(IncidentTrace))
        await session.execute(delete(IncidentLog))
        await session.execute(delete(IncidentEvent))
        await session.execute(delete(Incident))
        await session.execute(delete(Deployment))
        await session.execute(delete(Service))
        await session.execute(delete(Repository))
        await session.commit()

        await seed_initial_data(session)
