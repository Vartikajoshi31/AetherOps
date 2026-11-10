from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database.session import get_db
from app.models.repository import Repository, Service
from app.services.repo_service import RepositoryIndexerService
from pydantic import BaseModel, ConfigDict

repositories_router = APIRouter(prefix="/repositories", tags=["Repositories"])

class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

@repositories_router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    data: RepositoryCreate,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Repository).filter(Repository.full_name == data.full_name)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"Repository {data.full_name} is already registered")

    repo = Repository(
        id=str(uuid.uuid4()),
        name=data.name,
        full_name=data.full_name,
        default_branch=data.default_branch or "main",
        clone_url=data.clone_url,
        local_path=data.local_path,
        index_status="pending",
        total_files=0
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    return RepositoryResponse(
        id=repo.id,
        name=repo.name,
        full_name=repo.full_name,
        default_branch=repo.default_branch,
        clone_url=repo.clone_url,
        local_path=repo.local_path,
        indexed_at=repo.indexed_at,
        index_status=repo.index_status,
        total_files=repo.total_files,
        created_at=repo.created_at.isoformat() if repo.created_at else ""
    )

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
