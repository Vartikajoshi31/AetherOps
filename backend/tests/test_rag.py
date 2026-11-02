import pytest
from app.rag.chunking import ASTCodeChunker, MarkdownDocumentChunker, StackTraceParser
from app.rag.embeddings import embedding_service
from app.rag.retriever import hybrid_retriever
from app.rag.evaluation import RAGEvaluator
from app.services.repo_service import RepositoryIndexerService
from app.models.repository import Repository
from sqlalchemy import select

SAMPLE_PYTHON_CODE = '''
class OrderProcessor:
    """Handles order validation and shipping calculations."""

    def __init__(self, currency: str = "USD"):
        self.currency = currency

    def calculate_tax(self, subtotal: float) -> float:
        """Calculates 10% standard sales tax."""
        return subtotal * 0.10

    async def execute_payment(self, order_id: str, amount: float):
        # Charge payment gateway
        return {"order_id": order_id, "status": "PAID"}
'''

def test_ast_code_chunker():
    chunks = ASTCodeChunker.chunk_python_code(
        code_str=SAMPLE_PYTHON_CODE,
        file_path="services/order/processor.py",
        repository="acme/ecommerce-platform"
    )
    assert len(chunks) >= 3  # Class + calculate_tax method + execute_payment method
    funcs = [c.function_name for c in chunks if c.function_name]
    assert "calculate_tax" in funcs
    assert "execute_payment" in funcs

def test_markdown_chunker():
    md = """# Deployment Guide
Here is the deployment overview.

## Rollback Procedure
If error rate exceeds 5%, execute canary rollback:
`kubectl rollout undo deployment/checkout-service`
"""
    chunks = MarkdownDocumentChunker.chunk_markdown(md, "docs/deployment.md")
    assert len(chunks) >= 2
    headers = [c.function_name for c in chunks]
    assert "Deployment Guide" in headers or "Rollback Procedure" in headers

def test_stack_trace_parser():
    trace = '''Traceback (most recent call last):
  File "services/checkout/api.py", line 112, in create_checkout_session
    async with get_db_connection() as conn:
  File "services/checkout/db.py", line 45, in acquire
    conn = await pool.acquire(timeout=30.0)'''
    frames = StackTraceParser.parse_stack_trace(trace)
    assert len(frames) == 2
    assert frames[0]["file_path"] == "services/checkout/api.py"
    assert frames[0]["function_name"] == "create_checkout_session"
    assert frames[1]["file_path"] == "services/checkout/db.py"

@pytest.mark.asyncio
async def test_embedding_generation():
    vec = await embedding_service.get_embedding("QueuePool limit of size 10 overflow reached")
    assert len(vec) == 1536
    # Vector should be normalized
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 0.05

@pytest.mark.asyncio
async def test_repository_indexing_and_rag(db_session, client):
    # Index repository
    repo_stmt = select(Repository).limit(1)
    repo = (await db_session.execute(repo_stmt)).scalar_one()

    index_res = await client.post(f"/api/repositories/{repo.id}/index")
    assert index_res.status_code == 200
    details = index_res.json()["details"]
    assert details["total_files"] >= 4
    assert details["total_chunks"] >= 6

    # Test Hybrid RAG search
    search_res = await client.post(
        "/api/rag/search",
        json={"query": "QueuePool connection timeout pool acquire", "limit": 3}
    )
    assert search_res.status_code == 200
    results = search_res.json()
    assert len(results) > 0
    top = results[0]
    assert "content" in top
    assert "source_attribution" in top
    assert "file_path" in top

    # Test RAG Evaluation
    eval_res = await client.post("/api/rag/evaluate", json={})
    assert eval_res.status_code == 200
    report = eval_res.json()
    assert "mean_precision" in report
    assert "mean_recall" in report
    assert "mean_reciprocal_rank" in report
    assert report["mean_recall"] >= 0.5
