import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_sandbox_status_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/sandbox/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["isolation_engine"] == "process_isolated_tempfs"
        assert data["host_filesystem_mutation"] == "strictly_prevented"
        assert data["ast_syntax_prevalidation"] is True

@pytest.mark.asyncio
async def test_sandbox_examples_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/sandbox/examples")
        assert response.status_code == 200
        examples = response.json()
        assert len(examples) >= 4
        services = [ex["service"] for ex in examples]
        assert "checkout-service" in services
        assert "payment-service" in services
        assert "order-service" in services
        assert "inventory-service" in services

@pytest.mark.asyncio
async def test_sandbox_validate_execution():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "service_name": "checkout-service",
            "affected_file": "checkout-service/db.py",
            "diff_patch": "--- a/checkout-service/db.py\n+++ b/checkout-service/db.py\n@@ -32,3 +32,5 @@\n+    conn.in_use = True\n",
            "regression_test_code": (
                "from db import DatabaseConnectionPool\n"
                "import pytest\n\n"
                "@pytest.mark.asyncio\n"
                "async def test_pool_connection_release():\n"
                "    pool = DatabaseConnectionPool(max_size=2)\n"
                "    conn = await pool.acquire()\n"
                "    await pool.release(conn)\n"
                "    assert len(pool._available) == 2\n"
            ),
            "timeout_seconds": 20
        }
        response = await ac.post("/api/sandbox/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["syntax_valid"] is True
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert data["tests_run"] >= 2
        assert data["tests_passed"] >= 2

@pytest.mark.asyncio
async def test_sandbox_syntax_error_prevalidation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Intentionally malformed Python syntax
        payload = {
            "service_name": "checkout-service",
            "affected_file": "checkout-service/db.py",
            "diff_patch": "",
            "regression_test_code": "def broken_syntax(:\n    assert True",
            "timeout_seconds": 10
        }
        response = await ac.post("/api/sandbox/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["syntax_valid"] is False
        assert data["success"] is False
        assert "SyntaxError" in data["stderr"]

@pytest.mark.asyncio
async def test_auth_registration_and_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:6]}@nexora.ai"
        reg_payload = {
            "email": unique_email,
            "password": "SecurePassword123!",
            "full_name": "QA Test Engineer",
            "role": "engineer"
        }
        reg_res = await ac.post("/api/auth/register", json=reg_payload)
        assert reg_res.status_code == 201
        user_data = reg_res.json()
        assert user_data["email"] == unique_email
        assert user_data["full_name"] == "QA Test Engineer"

        # Duplicate registration should return 400
        dup_res = await ac.post("/api/auth/register", json=reg_payload)
        assert dup_res.status_code == 400
        assert "already exists" in dup_res.json()["detail"]

        # Login with correct password
        login_res = await ac.post("/api/auth/login", json={
            "email": unique_email,
            "password": "SecurePassword123!"
        })
        assert login_res.status_code == 200
        token_data = login_res.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        # Access /api/auth/me with Bearer token
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        me_res = await ac.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == unique_email

@pytest.mark.asyncio
async def test_auth_unauthorized_access():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # No token
        res_no_token = await ac.get("/api/auth/me")
        assert res_no_token.status_code == 401

        # Bad token
        res_bad_token = await ac.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token_123"})
        assert res_bad_token.status_code == 401

@pytest.mark.asyncio
async def test_repository_creation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        import uuid
        unique_name = f"test-repo-{uuid.uuid4().hex[:6]}"
        repo_payload = {
            "name": unique_name,
            "full_name": f"acme/{unique_name}",
            "default_branch": "main",
            "local_path": "./demo-services"
        }
        res = await ac.post("/api/repositories", json=repo_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == unique_name
        assert data["full_name"] == f"acme/{unique_name}"

        # Duplicate should return 400
        dup = await ac.post("/api/repositories", json=repo_payload)
        assert dup.status_code == 400
