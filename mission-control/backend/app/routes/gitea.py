"""
Gitea API routes - Repository management
"""
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel

from ..services.gitea import gitea_service

router = APIRouter(prefix="/api/gitea", tags=["gitea"])


class RepoInfo(BaseModel):
    id: int
    name: str
    full_name: str
    html_url: str
    description: str
    updated_at: str


class RepoCreateRequest(BaseModel):
    name: str
    description: str = ""
    private: bool = False


@router.get("/repos", response_model=List[RepoInfo])
async def list_repos():
    """List all Gitea repositories"""
    repos = await gitea_service.list_repos()
    return repos


@router.get("/repos/{repo_name}")
async def get_repo(repo_name: str):
    """Get repository info by name"""
    repo = await gitea_service.get_repo(repo_name)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.post("/repos", response_model=RepoInfo)
async def create_repo(request: RepoCreateRequest):
    """Create a new repository"""
    repo = await gitea_service.create_repo(
        name=request.name,
        description=request.description,
        private=request.private
    )
    if not repo:
        raise HTTPException(status_code=500, detail="Failed to create repository")
    return repo


@router.delete("/repos/{repo_name}")
async def delete_repo(repo_name: str):
    """Delete a repository"""
    success = await gitea_service.delete_repo(repo_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete repository")
    return {"status": "deleted", "name": repo_name}


@router.get("/health")
async def gitea_health():
    """Check Gitea connection health"""
    try:
        repos = await gitea_service.list_repos()
        return {
            "status": "ok",
            "url": gitea_service.base_url,
            "user": gitea_service.user,
            "repo_count": len(repos)
        }
    except Exception as e:
        return {
            "status": "error",
            "url": gitea_service.base_url,
            "error": str(e)
        }
