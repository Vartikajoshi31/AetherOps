from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.sandbox.runner import sandbox_runner, SandboxResult

sandbox_router = APIRouter(prefix="/sandbox", tags=["Sandbox"])

class SandboxValidateRequest(BaseModel):
    service_name: str = Field(..., min_length=1, json_schema_extra={"example": "checkout-service"})
    affected_file: str = Field(..., min_length=1, json_schema_extra={"example": "checkout-service/db.py"})
    diff_patch: str = Field(..., json_schema_extra={"example": "--- a/checkout-service/db.py\n+++ b/checkout-service/db.py\n..."})
    regression_test_code: Optional[str] = None
    timeout_seconds: Optional[int] = Field(30, ge=1, le=120)

@sandbox_router.post("/validate", response_model=SandboxResult)
async def validate_patch_in_sandbox(req: SandboxValidateRequest):
    """
    Executes candidate code and regression tests inside an isolated sandbox workspace.
    Guarantees zero mutations to host production codebase.
    """
    try:
        result = await sandbox_runner.run_sandboxed_validation(
            service_name=req.service_name,
            affected_file=req.affected_file,
            diff_patch=req.diff_patch,
            regression_test_code=req.regression_test_code,
            timeout_seconds=req.timeout_seconds or 30
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sandbox validation execution failed: {str(e)}"
        )

@sandbox_router.get("/status")
async def get_sandbox_status():
    """Returns sandbox security controls, runtime isolation profile, and health."""
    return {
        "status": "online",
        "isolation_engine": "process_isolated_tempfs",
        "host_filesystem_mutation": "strictly_prevented",
        "default_timeout_seconds": 30,
        "max_memory_mb": 512,
        "cleanup_policy": "automatic_ephemeral_rmtree",
        "ast_syntax_prevalidation": True
    }

@sandbox_router.get("/examples")
async def get_sandbox_examples():
    """Provides validated patch cases across the 4 demo microservices."""
    return [
        {
            "service": "checkout-service",
            "file": "checkout-service/db.py",
            "patch": "--- a/checkout-service/db.py\n+++ b/checkout-service/db.py\n@@ -32,3 +32,5 @@\n+    conn.in_use = True\n",
            "test": "from db import DatabaseConnectionPool\nimport pytest\n\n@pytest.mark.asyncio\nasync def test_pool_connection_release():\n    pool = DatabaseConnectionPool(max_size=2)\n    conn = await pool.acquire()\n    await pool.release(conn)\n    assert len(pool._available) == 2\n"
        },
        {
            "service": "payment-service",
            "file": "payment-service/client.py",
            "patch": "--- a/payment-service/client.py\n+++ b/payment-service/client.py\n@@ -20,2 +20,4 @@\n+        import random\n+        return self.base_backoff * (2 ** attempt) + random.uniform(0.1, 0.5)\n",
            "test": "from client import PaymentGatewayClient\n\ndef test_jittered_delays():\n    client = PaymentGatewayClient(base_backoff=1.0, use_jitter=True)\n    delays = [client.calculate_retry_delay(2) for _ in range(10)]\n    assert len(set(delays)) > 5\n"
        },
        {
            "service": "order-service",
            "file": "order-service/shipping.py",
            "patch": "--- a/order-service/shipping.py\n+++ b/order-service/shipping.py\n@@ -12,2 +12,4 @@\n+    if not order.shipping_address:\n+        return 0.0\n",
            "test": "from shipping import Order, calculate_shipping_cost\n\ndef test_digital_order():\n    order = Order(id='d-1', is_digital=True, shipping_address=None)\n    assert calculate_shipping_cost(order) == 0.0\n"
        },
        {
            "service": "inventory-service",
            "file": "inventory-service/cache.py",
            "patch": "--- a/inventory-service/cache.py\n+++ b/inventory-service/cache.py\n@@ -14,2 +14,4 @@\n+        if len(self._store) >= self.maxsize:\n+            self.evict_oldest()\n",
            "test": "from cache import InventoryCache\n\ndef test_cache_capacity():\n    cache = InventoryCache(maxsize=2, ttl_seconds=60)\n    cache.set('k1', 'v1')\n    cache.set('k2', 'v2')\n    cache.set('k3', 'v3')\n    assert cache.size <= 2\n"
        }
    ]
