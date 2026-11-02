from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.rag.retriever import hybrid_retriever
from app.rag.qdrant_store import qdrant_store
from app.rag.evaluation import RAGEvaluator

rag_router = APIRouter(prefix="/rag", tags=["RAG"])

class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    target_file_hint: Optional[str] = None
    target_func_hint: Optional[str] = None

class SearchResultItem(BaseModel):
    id: str
    content: str
    file_path: str
    doc_type: str
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    line_start: int
    line_end: int
    combined_score: float
    vector_score: float
    keyword_match_score: float
    source_attribution: Dict[str, Any]

class EvaluationCase(BaseModel):
    query: str
    expected_files: List[str]
    top_k: int = 5

class EvaluateRequest(BaseModel):
    test_cases: Optional[List[EvaluationCase]] = None

@rag_router.post("/search", response_model=List[SearchResultItem])
async def search_knowledge_base(req: SearchRequest):
    """Hybrid vector + keyword search over indexed source code, runbooks, and traces."""
    results = await hybrid_retriever.retrieve(
        query=req.query,
        limit=req.limit,
        target_file_hint=req.target_file_hint,
        target_func_hint=req.target_func_hint
    )
    return results

@rag_router.get("/stats")
async def get_rag_stats():
    """Retrieve vector database index statistics."""
    total_indexed = qdrant_store.get_total_indexed_count()
    return {
        "collection_name": qdrant_store.collection_name,
        "vector_dimension": qdrant_store.dimension,
        "total_points_indexed": total_indexed,
        "status": "online" if total_indexed > 0 else "empty"
    }

@rag_router.post("/evaluate")
async def evaluate_rag_retrieval(req: EvaluateRequest):
    """Run retrieval accuracy evaluation (Precision@K, Recall@K, MRR)."""
    default_cases = [
        {
            "query": "QueuePool limit of size 10 overflow 10 reached database connection leak",
            "expected_files": ["checkout-service/db.py", "checkout-service/app.py"],
            "top_k": 5
        },
        {
            "query": "deterministic exponential backoff thundering herd retry without jitter",
            "expected_files": ["payment-service/client.py"],
            "top_k": 5
        },
        {
            "query": "AttributeError NoneType object has no attribute country_code shipping",
            "expected_files": ["order-service/shipping.py"],
            "top_k": 5
        },
        {
            "query": "unbounded cache memory leak SKU invalidation TTL eviction",
            "expected_files": ["inventory-service/cache.py"],
            "top_k": 5
        }
    ]

    cases = [c.model_dump() for c in req.test_cases] if req.test_cases else default_cases
    eval_report = await RAGEvaluator.run_evaluation_suite(cases)
    return eval_report
