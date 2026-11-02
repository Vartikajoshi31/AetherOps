import os
import json
import uuid

CATEGORIES_DATA = [
    {
        "category": "database_pool_exhaustion",
        "title": "QueuePool Limit Overflow in Async DB Checkout Session",
        "service": "checkout-service",
        "severity": "Critical",
        "culprit_file": "checkout-service/db.py",
        "culprit_function": "acquire",
        "root_cause": "Async database connections acquired from QueuePool are not released back to the pool in exception branches when downstream HTTP requests timeout.",
        "log_msg": "TimeoutError: QueuePool limit of size 10 overflow 10 reached, connection timed out, timeout 5.0s",
        "trace_op": "db.acquire_connection",
        "patch_diff": "--- a/checkout-service/db.py\n+++ b/checkout-service/db.py\n@@ -35,3 +35,5 @@\n+    finally:\n+        await pool.release(conn)\n"
    },
    {
        "category": "slow_query_missing_index",
        "title": "Full Table Sequential Scan on Orders Table Without Index",
        "service": "order-service",
        "severity": "High",
        "culprit_file": "order-service/repository.py",
        "culprit_function": "find_by_customer_and_status",
        "root_cause": "Missing composite B-tree index on (customer_id, order_status) triggers sequential scans across 4M rows, increasing latency to 12s.",
        "log_msg": "SlowQueryWarning: Query executed in 11840ms: SELECT * FROM orders WHERE customer_id = $1 AND status = 'PENDING'",
        "trace_op": "postgres.orders_scan",
        "patch_diff": "--- a/order-service/migrations/004_index.sql\n+++ b/order-service/migrations/004_index.sql\n+CREATE INDEX CONCURRENTLY idx_orders_cust_status ON orders(customer_id, status);\n"
    },
    {
        "category": "memory_leak",
        "title": "Unbounded Cache Dict Growth in Inventory SKU Tracker",
        "service": "inventory-service",
        "severity": "Critical",
        "culprit_file": "inventory-service/cache.py",
        "culprit_function": "set",
        "root_cause": "In-memory dictionary cache stores all requested SKU items without max size eviction or TTL expiry, causing memory consumption to exceed 2GB container limit.",
        "log_msg": "MemoryError: Container memory cgroup limit reached (1024MB), process received SIGKILL (OOMKilled)",
        "trace_op": "cache.store_sku",
        "patch_diff": "--- a/inventory-service/cache.py\n+++ b/inventory-service/cache.py\n+    if len(self._store) >= self.maxsize: self.evict_oldest()\n"
    },
    {
        "category": "deadlock",
        "title": "Cross-Table Transaction Lock Order Inversion Deadlock",
        "service": "order-service",
        "severity": "Critical",
        "culprit_file": "order-service/transaction.py",
        "culprit_function": "transfer_funds",
        "root_cause": "Concurrent checkout transfers acquire row locks in arbitrary account ID order rather than sorted order, creating circular lock dependency graph.",
        "log_msg": "DeadlockDetected: Process 4104 waits for ExclusiveLock on transaction 891; process 4105 waits for ShareLock on transaction 892",
        "trace_op": "sql.acquire_row_lock",
        "patch_diff": "--- a/order-service/transaction.py\n+++ b/order-service/transaction.py\n+    first_acc, second_acc = sorted([acc_a, acc_b], key=lambda x: x.id)\n"
    },
    {
        "category": "cpu_saturation",
        "title": "ReDoS Catastrophic Backtracking on Email Regex Validation",
        "service": "checkout-service",
        "severity": "High",
        "culprit_file": "checkout-service/validator.py",
        "culprit_function": "validate_customer_email",
        "root_cause": "Regular expression ^([a-zA-Z0-9_\\.-]+)+@([a-zA-Z0-9_-]+)+$ exhibits polynomial/exponential backtracking when evaluated against malformed payloads.",
        "log_msg": "CPUSaturationWarning: Worker thread pinned at 100% CPU for >15000ms in regex evaluation",
        "trace_op": "regex.email_match",
        "patch_diff": "--- a/checkout-service/validator.py\n+++ b/checkout-service/validator.py\n-EMAIL_REGEX = r'^([a-zA-Z0-9_\\.-]+)+@([a-zA-Z0-9_-]+)+$'\n+EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'\n"
    },
    {
        "category": "network_timeout",
        "title": "Missing Socket Read Timeout in Shipping Carrier REST Client",
        "service": "order-service",
        "severity": "High",
        "culprit_file": "order-service/shipping_client.py",
        "culprit_function": "fetch_shipping_rates",
        "root_cause": "HTTP client initialized without read timeout (timeout=None); when external carrier gateway drops packets, connection hangs indefinitely until worker pool starves.",
        "log_msg": "ConnectionPoolTimeout: All 50 worker threads blocked waiting for carrier socket response",
        "trace_op": "http.carrier_rates",
        "patch_diff": "--- a/order-service/shipping_client.py\n+++ b/order-service/shipping_client.py\n-    client = httpx.AsyncClient()\n+    client = httpx.AsyncClient(timeout=httpx.Timeout(connect=2.0, read=5.0))\n"
    },
    {
        "category": "cascading_failure",
        "title": "Downstream Stock Service Degradation Cascading to Cart Service",
        "service": "inventory-service",
        "severity": "Critical",
        "culprit_file": "inventory-service/client.py",
        "culprit_function": "query_availability",
        "root_cause": "Absence of a circuit breaker between checkout and inventory allows inventory slow responses to saturate upstream connection pools across all services.",
        "log_msg": "UpstreamCircuitOpenError: Cascade failure propagated across 4 microservices",
        "trace_op": "inventory.check_stock",
        "patch_diff": "--- a/inventory-service/client.py\n+++ b/inventory-service/client.py\n+    if circuit_breaker.is_open(): return get_cached_stock(sku)\n"
    },
    {
        "category": "upstream_outage",
        "title": "Payment Provider API 503 Outage Without Fallback Processor",
        "service": "payment-service",
        "severity": "Critical",
        "culprit_file": "payment-service/gateway.py",
        "culprit_function": "process_charge",
        "root_cause": "Payment gateway client does not implement secondary payment provider failover when primary provider returns persistent 503 Service Unavailable.",
        "log_msg": "HTTPStatusError: 503 Service Unavailable received from Stripe Gateway",
        "trace_op": "payment.primary_gateway",
        "patch_diff": "--- a/payment-service/gateway.py\n+++ b/payment-service/gateway.py\n+    except UpstreamProviderError:\n+        return await self.secondary_gateway.process_charge(req)\n"
    },
    {
        "category": "configuration_error",
        "title": "Invalid Redis Cluster Max Memory Policy Eviction Setting",
        "service": "inventory-service",
        "severity": "Medium",
        "culprit_file": "inventory-service/config.py",
        "culprit_function": "load_redis_settings",
        "root_cause": "Configuration defaulted maxmemory-policy to 'noeviction', causing Redis to reject all write commands with OOM command errors when capacity was reached.",
        "log_msg": "ResponseError: OOM command not allowed when used memory > 'maxmemory' in Redis cluster",
        "trace_op": "redis.write_key",
        "patch_diff": "--- a/inventory-service/config.py\n+++ b/inventory-service/config.py\n-REDIS_MAXMEMORY_POLICY = 'noeviction'\n+REDIS_MAXMEMORY_POLICY = 'volatile-lru'\n"
    },
    {
        "category": "bad_deployment",
        "title": "Missing Database Column in Release v2.4.1 Schema Mismatch",
        "service": "checkout-service",
        "severity": "Critical",
        "culprit_file": "checkout-service/models.py",
        "culprit_function": "OrderModel",
        "root_cause": "New application deployment expects 'discount_code_id' column in orders table, but Alembic database migration was not executed prior to container rollout.",
        "log_msg": "ProgrammingError: column orders.discount_code_id does not exist",
        "trace_op": "sql.insert_order",
        "patch_diff": "--- a/checkout-service/models.py\n+++ b/checkout-service/models.py\n-    discount_code_id = Column(String(36), nullable=False)\n+    discount_code_id = Column(String(36), nullable=True)\n"
    },
    {
        "category": "thread_pool_exhaustion",
        "title": "Synchronous Blocking IO in Async FastApi Event Loop",
        "service": "order-service",
        "severity": "High",
        "culprit_file": "order-service/pdf.py",
        "culprit_function": "generate_invoice_pdf",
        "root_cause": "Synchronous file writing and PDF rendering executed directly inside async route handler, blocking the single event loop thread for all requests.",
        "log_msg": "EventLoopBlockedWarning: Async event loop was blocked for 2480ms by synchronous PDF generation",
        "trace_op": "pdf.render_invoice",
        "patch_diff": "--- a/order-service/pdf.py\n+++ b/order-service/pdf.py\n-    return render_pdf(invoice_data)\n+    return await asyncio.to_thread(render_pdf, invoice_data)\n"
    },
    {
        "category": "unhandled_exception",
        "title": "Unhandled KeyError in Multi-Currency Exchange Rate Parser",
        "service": "checkout-service",
        "severity": "Medium",
        "culprit_file": "checkout-service/currency.py",
        "culprit_function": "convert_to_usd",
        "root_cause": "Currency converter accesses rates[target_currency] directly; when an unsupported currency is passed in checkout, an unhandled KeyError crashes the handler.",
        "log_msg": "KeyError: 'AED' currency code not present in exchange rates dictionary",
        "trace_op": "currency.convert",
        "patch_diff": "--- a/checkout-service/currency.py\n+++ b/checkout-service/currency.py\n-    return amount / rates[currency]\n+    rate = rates.get(currency) or 1.0\n+    return amount / rate\n"
    },
    {
        "category": "concurrency_race",
        "title": "Non-Atomic Stock Decrement Leading to Negative Inventory",
        "service": "inventory-service",
        "severity": "High",
        "culprit_file": "inventory-service/stock.py",
        "culprit_function": "reserve_item",
        "root_cause": "Stock reservation reads current quantity, checks if > 0 in memory, and writes back decremented value, leading to race conditions under concurrent load.",
        "log_msg": "IntegrityError: Check constraint violation on inventory_stock.quantity >= 0",
        "trace_op": "stock.reserve_item",
        "patch_diff": "--- a/inventory-service/stock.py\n+++ b/inventory-service/stock.py\n-    stock.quantity -= qty\n+    # Atomic conditional update\n+    await db.execute(update(Stock).where(Stock.id == id, Stock.quantity >= qty).values(quantity=Stock.quantity - qty))\n"
    },
    {
        "category": "circuit_breaker_tripped",
        "title": "Circuit Breaker Permanently Latched Open Due to High Reset Timeout",
        "service": "payment-service",
        "severity": "High",
        "culprit_file": "payment-service/circuit.py",
        "culprit_function": "can_execute",
        "root_cause": "Circuit breaker reset timeout configured to 3600 seconds (1 hour); after 5 transient failures, the breaker remains open rejecting all valid requests.",
        "log_msg": "CircuitBreakerOpenException: Payment gateway circuit breaker is OPEN. Fast failing request.",
        "trace_op": "circuit_breaker.evaluate",
        "patch_diff": "--- a/payment-service/circuit.py\n+++ b/payment-service/circuit.py\n-RESET_TIMEOUT = 3600\n+RESET_TIMEOUT = 30\n"
    },
    {
        "category": "serialization_error",
        "title": "UUID Object Serialization Failure in JSON Audit Logger",
        "service": "order-service",
        "severity": "Medium",
        "culprit_file": "order-service/audit.py",
        "culprit_function": "log_order_event",
        "root_cause": "Standard json.dumps() does not support Python uuid.UUID objects without a custom encoder, causing audit logging to raise TypeError on every order.",
        "log_msg": "TypeError: Object of type UUID is not JSON serializable in json.dumps()",
        "trace_op": "audit.record_event",
        "patch_diff": "--- a/order-service/audit.py\n+++ b/order-service/audit.py\n-    return json.dumps(payload)\n+    return json.dumps(payload, default=str)\n"
    },
    {
        "category": "disk_space_exhaustion",
        "title": "Unrotated Application Access Logs Filling Root Volume",
        "service": "checkout-service",
        "severity": "Critical",
        "culprit_file": "checkout-service/logging_conf.py",
        "culprit_function": "setup_file_handler",
        "root_cause": "Logging handler configured as standard FileHandler instead of RotatingFileHandler, causing stdout logs to accumulate 120GB and exhaust disk space.",
        "log_msg": "OSError: [Errno 28] No space left on device: '/var/log/checkout.log'",
        "trace_op": "logger.write_disk",
        "patch_diff": "--- a/checkout-service/logging_conf.py\n+++ b/checkout-service/logging_conf.py\n-    handler = logging.FileHandler('/var/log/checkout.log')\n+    handler = logging.handlers.RotatingFileHandler('/var/log/checkout.log', maxBytes=50*1024*1024, backupCount=5)\n"
    },
    {
        "category": "cache_stampede",
        "title": "Cache Stampede on Top-Selling Product Page Expiry",
        "service": "inventory-service",
        "severity": "High",
        "culprit_file": "inventory-service/cache.py",
        "culprit_function": "get_product_details",
        "root_cause": "Popular cache key expires simultaneously for 5000 concurrent clients, causing all threads to query PostgreSQL database simultaneously.",
        "log_msg": "DBPoolOverloadWarning: 1200 concurrent queries for product_id=PROD-9988 upon cache expiration",
        "trace_op": "db.select_product",
        "patch_diff": "--- a/inventory-service/cache.py\n+++ b/inventory-service/cache.py\n+    # Implement probabilistic early expiration (XFetch algorithm)\n+    if should_early_refresh(key, ttl):\n+        asyncio.create_task(refresh_cache_background(key))\n"
    },
    {
        "category": "thundering_herd",
        "title": "Deterministic Exponential Backoff Without Random Jitter",
        "service": "payment-service",
        "severity": "Critical",
        "culprit_file": "payment-service/client.py",
        "culprit_function": "calculate_retry_delay",
        "root_cause": "Payment retries use deterministic 2^attempt backoff without jitter, causing waves of synchronized retry storms that hammer recovering servers.",
        "log_msg": "GatewayTimeout: 504 Gateway Timeout recurring in exact 2.0s, 4.0s harmonic bursts",
        "trace_op": "payment.retry_delay",
        "patch_diff": "--- a/payment-service/client.py\n+++ b/payment-service/client.py\n-    return self.base_backoff * (2 ** attempt)\n+    import random\n+    return self.base_backoff * (2 ** attempt) + random.uniform(0.1, 0.5)\n"
    },
    {
        "category": "corrupted_cache_state",
        "title": "Partial Write Deserialization Failure in Redis Session Store",
        "service": "checkout-service",
        "severity": "High",
        "culprit_file": "checkout-service/session.py",
        "culprit_function": "get_cart_session",
        "root_cause": "Session state written without transaction or pipeline; network disconnection left truncated JSON in Redis key, throwing JSONDecodeError on read.",
        "log_msg": "json.decoder.JSONDecodeError: Unterminated string starting at line 1 column 124",
        "trace_op": "session.deserialize_cart",
        "patch_diff": "--- a/checkout-service/session.py\n+++ b/checkout-service/session.py\n+    except json.JSONDecodeError:\n+        logger.warning('Corrupted session cache detected. Resetting session.')\n+        return CartSession()\n"
    },
    {
        "category": "dns_resolution_failure",
        "title": "Internal Kubernetes CoreDNS Service Discovery Flapping",
        "service": "order-service",
        "severity": "High",
        "culprit_file": "order-service/dns.py",
        "culprit_function": "resolve_service_ip",
        "root_cause": "Default resolver does not cache DNS records and queries CoreDNS on every outgoing HTTP request, failing when CoreDNS pods throttle UDP packets.",
        "log_msg": "gaierror: [Errno -3] Temporary failure in name resolution for payment.ecommerce.svc.cluster.local",
        "trace_op": "dns.resolve_host",
        "patch_diff": "--- a/order-service/dns.py\n+++ b/order-service/dns.py\n+    # Enable connection keep-alive and local DNS caching\n+    transport = httpx.AsyncHTTPTransport(retries=2, keepalive_expiry=30.0)\n"
    }
]

def generate_50_incidents():
    incidents = []
    base_id = 1

    # Loop and generate 50 distinct realistic incidents across the 20 categories
    while len(incidents) < 50:
        for template in CATEGORIES_DATA:
            if len(incidents) >= 50:
                break

            idx = len(incidents) + 1
            cat = template["category"]
            svc = template["service"]
            bench_id = f"BENCH-{idx:03d}"

            # Variations for unique incidents
            variant = (idx - 1) // 20
            suffix = f" (Cluster Partition {variant + 1})" if variant > 0 else ""
            title = f"{template['title']}{suffix}"

            item = {
                "id": str(uuid.uuid4()),
                "benchmark_id": bench_id,
                "title": title,
                "category": cat,
                "severity": template["severity"],
                "service_name": svc,
                "ground_truth_root_cause": template["root_cause"],
                "ground_truth_culprit_files": [template["culprit_file"]],
                "ground_truth_culprit_function": template["culprit_function"],
                "ground_truth_patch_diff": template["patch_diff"],
                "simulated_logs": [
                    {
                        "service_name": svc,
                        "level": "ERROR" if template["severity"] in ["Critical", "High"] else "WARN",
                        "message": template["log_msg"],
                        "stack_trace": f'File "{template["culprit_file"]}", line 42, in {template["culprit_function"]}\n    {template["log_msg"]}'
                    }
                ],
                "simulated_traces": [
                    {
                        "service_name": svc,
                        "operation_name": template["trace_op"],
                        "duration_ms": 3200.0 if template["severity"] == "Critical" else 450.0,
                        "status_code": "500" if template["severity"] == "Critical" else "400",
                        "error_message": template["log_msg"]
                    }
                ],
                "test_verification_command": f"pytest {svc}/tests/ -v"
            }
            incidents.append(item)

    return incidents

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)
    dataset = generate_50_incidents()
    out_path = os.path.join(out_dir, "synthetic_incidents.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    print(f"Generated {len(dataset)} synthetic incident benchmarks at {out_path}")
