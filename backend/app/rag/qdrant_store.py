import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.core.config import settings
from app.core.logging import logger
from app.rag.chunking import CodeChunk
from app.rag.embeddings import embedding_service
import uuid

class QdrantStore:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.dimension = 1536
        self.client: QdrantClient = self._init_client()
        self._ensure_collection()

    def _init_client(self) -> QdrantClient:
        try:
            client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0)
            client.get_collections()
            logger.info(f"Connected to remote Qdrant vector database at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
            return client
        except Exception:
            logger.info(f"Remote Qdrant unavailable. Initializing embedded local Qdrant storage at {settings.QDRANT_STORAGE_PATH}")
            os.makedirs(settings.QDRANT_STORAGE_PATH, exist_ok=True)
            try:
                return QdrantClient(path=settings.QDRANT_STORAGE_PATH)
            except Exception as lock_err:
                logger.warning(f"Storage path {settings.QDRANT_STORAGE_PATH} is locked or busy ({lock_err}). Initializing in-memory Qdrant store.")
                return QdrantClient(":memory:")

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            names = [c.name for c in collections]
            if self.collection_name not in names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.dimension,
                        distance=qmodels.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection '{self.collection_name}' with 1536 dimensions (Cosine distance).")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")

    async def upsert_chunks(self, chunks: List[CodeChunk]) -> int:
        if not chunks:
            return 0

        texts = [chunk.content for chunk in chunks]
        embeddings = await embedding_service.get_embeddings_batch(texts)

        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            payload = chunk.to_dict()
            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} chunks into Qdrant collection '{self.collection_name}'.")
        return len(points)

    async def search(
        self,
        query: str,
        limit: int = 10,
        doc_type: Optional[str] = None,
        file_path_prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query_vector = await embedding_service.get_embedding(query)

        query_filter = None
        conditions = []
        if doc_type:
            conditions.append(
                qmodels.FieldCondition(
                    key="doc_type",
                    match=qmodels.MatchValue(value=doc_type)
                )
            )
        if file_path_prefix:
            conditions.append(
                qmodels.FieldCondition(
                    key="file_path",
                    match=qmodels.MatchText(text=file_path_prefix)
                )
            )

        if conditions:
            query_filter = qmodels.Filter(must=conditions)

        query_response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )

        results = []
        for hit in query_response.points:
            results.append({
                "id": str(hit.id),
                "score": float(hit.score),
                "content": hit.payload.get("content", ""),
                "file_path": hit.payload.get("file_path", ""),
                "doc_type": hit.payload.get("doc_type", "code"),
                "function_name": hit.payload.get("function_name"),
                "class_name": hit.payload.get("class_name"),
                "line_start": hit.payload.get("line_start", 1),
                "line_end": hit.payload.get("line_end", 1),
                "repository": hit.payload.get("repository", "acme/ecommerce-platform"),
                "commit_sha": hit.payload.get("commit_sha", "main"),
                "metadata": hit.payload.get("metadata", {}),
            })

        return results

    def get_total_indexed_count(self) -> int:
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count or 0
        except Exception:
            return 0

qdrant_store = QdrantStore()
