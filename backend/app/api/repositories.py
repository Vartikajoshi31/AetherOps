from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database.session import get_db
from app.models.repository import Repository, Service
from app.services.repo_service import RepositoryIndexerService
from pydantic import BaseModel

repositories_router = APIRouter(prefix="/repositories", tags=["Repositories"])

class RepositoryResponse(BaseModel):
    id: str
    name: str
    full_name: str
    default_branch: str
    clone_url: Optional[str] = None
    local_path: Optional[str] = None
    indexed_at: Optional[str] = None
    index_status: str
    total_files: int
    created_at: str

    class Config:
        from_attributes = True

class RepositoryCreate(BaseModel):
    name: str
    full_name: str
    default_branch: str = "main"
    clone_url: Optional[str] = None
    local_path: Optional[str] = None

@repositories_router.get("", response_model=List[RepositoryResponse])
async def list_repositories(db: AsyncSession = Depends(get_db)):
    stmt = select(Repository).order_by(desc(Repository.created_at))
    repos = (await db.execute(stmt)).scalars().all()
    return [
        RepositoryResponse(
            id=r.id,
            name=r.name,
            full_name=r.full_name,
            default_branch=r.default_branch,
            clone_url=r.clone_url,
            local_path=r.local_path,
            indexed_at=r.indexed_at,
            index_status=r.index_status,
            total_files=r.total_files,
            created_at=r.created_at.isoformat() if r.created_at else ""
        ) for r in repos
    ]

@repositories_router.post("/{repo_id}/index")
async def trigger_repository_index(repo_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Repository).filter(Repository.id == repo_id)
    repo = (await db.execute(stmt)).scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    result = await RepositoryIndexerService.index_repository(db, repository_id=repo_id)
    return {
        "status": "indexed",
        "repo_id": repo.id,
        "message": f"Successfully indexed {result['total_files']} files and stored {result['total_chunks']} AST code chunks in Qdrant.",
        "details": result
    }
