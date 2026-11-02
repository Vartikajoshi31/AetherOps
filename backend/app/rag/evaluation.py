import os
from typing import List, Dict, Any
from app.rag.retriever import hybrid_retriever

class RAGEvaluator:
    @staticmethod
    async def evaluate_query(
        query: str,
        expected_culprit_files: List[str],
        top_k: int = 5
    ) -> Dict[str, Any]:
        results = await hybrid_retriever.retrieve(query=query, limit=top_k)

        retrieved_files = [r["file_path"].lower() for r in results]
        expected_clean = [f.lower().strip() for f in expected_culprit_files]

        # 1. Precision@K: Matching either full path or basename/fragment
        hits = 0
        first_hit_rank = 0
        for rank, r_file in enumerate(retrieved_files, start=1):
            r_base = os.path.basename(r_file)
            r_norm = r_file.replace("\\", "/")
            is_hit = False
            for exp in expected_clean:
                exp_norm = exp.replace("\\", "/")
                exp_base = os.path.basename(exp_norm)
                if exp_norm in r_norm or r_norm in exp_norm or exp_base == r_base:
                    is_hit = True
                    break

            if is_hit:
                hits += 1
                if first_hit_rank == 0:
                    first_hit_rank = rank

        precision_at_k = hits / max(len(results), 1)

        # 2. Recall@K
        expected_hits = 0
        for exp in expected_clean:
            exp_norm = exp.replace("\\", "/")
            exp_base = os.path.basename(exp_norm)
            found = False
            for r_file in retrieved_files:
                r_norm = r_file.replace("\\", "/")
                r_base = os.path.basename(r_norm)
                if exp_norm in r_norm or r_norm in exp_norm or exp_base == r_base:
                    found = True
                    break
            if found:
                expected_hits += 1

        recall_at_k = expected_hits / max(len(expected_clean), 1)

        # 3. Reciprocal Rank (MRR for single query)
        reciprocal_rank = (1.0 / first_hit_rank) if first_hit_rank > 0 else 0.0

        return {
            "query": query,
            "top_k": top_k,
            "retrieved_count": len(results),
            "expected_culprit_files": expected_culprit_files,
            "retrieved_files": [r["file_path"] for r in results],
            "precision_at_k": round(precision_at_k, 3),
            "recall_at_k": round(recall_at_k, 3),
            "mrr": round(reciprocal_rank, 3),
            "top_result": results[0] if results else None,
            "passed_threshold": recall_at_k >= 0.5
        }

    @staticmethod
    async def run_evaluation_suite(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        eval_results = []
        for case in test_cases:
            res = await RAGEvaluator.evaluate_query(
                query=case["query"],
                expected_culprit_files=case["expected_files"],
                top_k=case.get("top_k", 5)
            )
            eval_results.append(res)

        avg_precision = sum(r["precision_at_k"] for r in eval_results) / max(len(eval_results), 1)
        avg_recall = sum(r["recall_at_k"] for r in eval_results) / max(len(eval_results), 1)
        avg_mrr = sum(r["mrr"] for r in eval_results) / max(len(eval_results), 1)

        return {
            "total_queries_evaluated": len(eval_results),
            "mean_precision": round(avg_precision, 3),
            "mean_recall": round(avg_recall, 3),
            "mean_reciprocal_rank": round(avg_mrr, 3),
            "eval_details": eval_results
        }
