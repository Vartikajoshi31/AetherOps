import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.repository import Repository
from app.rag.chunking import ASTCodeChunker, MarkdownDocumentChunker, CodeChunk
from app.rag.qdrant_store import qdrant_store
from app.core.logging import logger

def utcnow():
    return datetime.now(timezone.utc)

class RepositoryIndexerService:
    @staticmethod
    async def index_repository(
        session: AsyncSession,
        repository_id: str,
        target_path: Optional[str] = None
    ) -> Dict[str, Any]:
        stmt = select(Repository).filter(Repository.id == repository_id)
        repo = (await session.execute(stmt)).scalar_one_or_none()
        if not repo:
            raise ValueError(f"Repository {repository_id} not found")

        repo_path = target_path or repo.local_path or "./demo-services"
        if not os.path.exists(repo_path):
            # If running from backend/ subdirectory, try parent
            parent_candidate = os.path.join("..", repo_path.lstrip("./\\"))
            if os.path.exists(parent_candidate):
                repo_path = parent_candidate
            else:
                repo_path = os.path.abspath(repo_path)

        logger.info(f"Indexing repository {repo.full_name} from path: {repo_path}")
        repo.index_status = "indexing"
        await session.commit()

        chunks: List[CodeChunk] = []
        file_count = 0

        # Walk repository files
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".venv", "venv", "node_modules", ".next", ".pytest_cache"]]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path).replace("\\", "/")

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    if ext == ".py":
                        file_chunks = ASTCodeChunker.chunk_python_code(
                            code_str=content,
                            file_path=rel_path,
                            repository=repo.full_name
                        )
                        chunks.extend(file_chunks)
                        file_count += 1
                    elif ext in [".md", ".txt", ".rst"]:
                        doc_chunks = MarkdownDocumentChunker.chunk_markdown(
                            doc_str=content,
                            file_path=rel_path,
                            repository=repo.full_name
                        )
                        chunks.extend(doc_chunks)
                        file_count += 1
                except Exception as e:
                    logger.warning(f"Error parsing file {rel_path}: {e}")

        # Upsert chunks into Qdrant
        indexed_points = await qdrant_store.upsert_chunks(chunks)

        # Update Repository record
        repo.index_status = "indexed"
        repo.total_files = file_count
        repo.indexed_at = utcnow().isoformat()
        await session.commit()

        logger.info(f"Repository {repo.full_name} indexed successfully: {file_count} files, {len(chunks)} AST chunks stored in Qdrant.")

        return {
            "repository_id": repo.id,
            "status": "indexed",
            "total_files": file_count,
            "total_chunks": len(chunks),
            "qdrant_points_upserted": indexed_points
        }
