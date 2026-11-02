import re
import math
from typing import List, Dict, Any, Optional
from app.rag.qdrant_store import qdrant_store
from app.core.logging import logger

class HybridRetriever:
    """
    Production-style Hybrid RAG Retriever.
    Combines dense Qdrant vector search with sparse keyword lexical matching via Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    async def retrieve(
        self,
        query: str,
        limit: int = 5,
        target_file_hint: Optional[str] = None,
        target_func_hint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        # 1. Broad Vector Candidate Search from Qdrant
        candidate_limit = max(limit * 6, 40)
        vector_results = await qdrant_store.search(query=query, limit=candidate_limit)

        # 2. Sparse Lexical Scoring
        query_terms = set(re.findall(r"\w+", query.lower()))

        scored_items = []
        for v_rank, item in enumerate(vector_results):
            content = item["content"].lower()
            file_path = item["file_path"].lower()
            func_name = (item["function_name"] or "").lower()

            # Exact keyword match scoring
            term_matches = sum(1 for term in query_terms if term in content or term in func_name)
            keyword_score = term_matches / max(len(query_terms), 1)

            # Reciprocal Rank Fusion
            # RRF = 1 / (k + rank_vector) + 1 / (k + rank_keyword)
            v_rrf = 1.0 / (self.rrf_k + v_rank + 1)
            k_rrf = keyword_score * 0.05

            combined_score = v_rrf + k_rrf

            # Priority for core application source code over test fixtures
            is_test_file = "/tests/" in file_path or "\\tests\\" in file_path or "test_" in file_path
            if not is_test_file:
                combined_score += 0.03

            # Reranking Boosts:
            # If stack trace or caller gave a hint matching the file or function:
            if target_file_hint and target_file_hint.lower() in file_path:
                combined_score += 0.25
            if target_func_hint and target_func_hint.lower() in func_name:
                combined_score += 0.35

            scored_items.append({
                **item,
                "vector_score": item["score"],
                "keyword_match_score": round(keyword_score, 4),
                "combined_score": round(combined_score, 5),
                "source_attribution": {
                    "repository": item["repository"],
                    "file_path": item["file_path"],
                    "lines": f"{item['line_start']}-{item['line_end']}",
                    "function": item["function_name"] or "module-level",
                    "commit": item["commit_sha"]
                }
            })

        # Sort by preliminary combined score descending
        scored_items.sort(key=lambda x: x["combined_score"], reverse=True)

        # Apply File Diversity (Maximal Marginal Relevance style dampening for duplicate files)
        final_items = []
        file_counts: Dict[str, int] = {}
        for item in scored_items:
            fpath = item["file_path"]
            count = file_counts.get(fpath, 0)
            if count >= 2 and len(final_items) < limit:
                # Deprioritize excessive chunks from the same file to allow diverse files
                continue
            file_counts[fpath] = count + 1
            final_items.append(item)
            if len(final_items) >= limit:
                break

        return final_items[:limit]

    def construct_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """Constructs an evidence-grounded prompt context string with explicit attribution headers."""
        if not retrieved_docs:
            return "No relevant technical documentation or source code was retrieved."

        context_blocks = []
        for idx, doc in enumerate(retrieved_docs, start=1):
            attr = doc["source_attribution"]
            header = f"--- [Document #{idx}] Source: {attr['repository']} | {attr['file_path']}:{attr['lines']} (func: {attr['function']}) | Match Score: {doc['combined_score']} ---"
            block = f"{header}\n{doc['content']}\n"
            context_blocks.append(block)

        return "\n".join(context_blocks)

hybrid_retriever = HybridRetriever()
