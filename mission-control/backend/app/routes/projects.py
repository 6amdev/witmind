"""
Projects API routes
"""
import os
import io
import zipfile
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel
import httpx

from ..database import projects_collection, tasks_collection

logger = logging.getLogger(__name__)

# Platform API URL (for triggering agents)
PLATFORM_API_URL = os.getenv("PLATFORM_API_URL", "http://192.168.80.203:4005")
from ..models import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectStatus,
    ProjectType,
    ExecutionMode,
)
from ..services.team_detector import detect_team
from ..services.gitea import gitea_service

router = APIRouter(prefix="/api/projects", tags=["projects"])


def project_to_response(project: dict) -> ProjectResponse:
    """Convert MongoDB document to ProjectResponse"""
    return ProjectResponse(
        id=str(project["_id"]),
        name=project["name"],
        description=project["description"],
        type=project.get("type"),
        team_id=project.get("team_id"),
        status=project.get("status", ProjectStatus.DRAFT),
        progress=project.get("progress", 0),
        execution_mode=project.get("execution_mode", ExecutionMode.REVIEW_FIRST),
        created_at=project.get("created_at", datetime.utcnow()),
        updated_at=project.get("updated_at", datetime.utcnow()),
        completed_at=project.get("completed_at"),
        output_dir=project.get("output_dir"),
        preview_url=project.get("preview_url"),
        git_repo_name=project.get("git_repo_name"),
        git_repo_url=project.get("git_repo_url"),
        git_clone_url=project.get("git_clone_url"),
    )


@router.get("", response_model=List[ProjectResponse])
async def list_projects():
    """List all projects"""
    cursor = projects_collection().find().sort("created_at", -1)
    projects = await cursor.to_list(100)
    return [project_to_response(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate):
    """Create a new project with auto team detection"""
    # Auto-detect project type and team from description
    detected = detect_team(project.description)

    doc = {
        "name": project.name,
        "description": project.description,
        "type": project.type or detected["type"],
        "team_id": project.team_id or detected["team_id"],
        "execution_mode": project.execution_mode or ExecutionMode.REVIEW_FIRST,
        "status": ProjectStatus.DRAFT,
        "progress": 0,
        "members": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await projects_collection().insert_one(doc)
    doc["_id"] = result.inserted_id

    return project_to_response(doc)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a project by ID"""
    try:
        project = await projects_collection().find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project_to_response(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, update: ProjectUpdate):
    """Update a project"""
    try:
        oid = ObjectId(project_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()

    result = await projects_collection().update_one(
        {"_id": oid}, {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")

    project = await projects_collection().find_one({"_id": oid})
    return project_to_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str):
    """Delete a project and its tasks"""
    try:
        oid = ObjectId(project_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    result = await projects_collection().delete_one({"_id": oid})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete associated tasks
    await tasks_collection().delete_many({"project_id": project_id})


async def dispatch_to_platform(project_id: str, name: str, description: str, team_id: str, execution_mode: str, git_clone_url: str = None):
    """Background task to dispatch project to Platform API"""
    print(f"🚀 Dispatching project {project_id} to Platform API at {PLATFORM_API_URL}")
    print(f"   Execution mode: {execution_mode}")
    if git_clone_url:
        print(f"   Git repo: {git_clone_url.split('@')[1] if '@' in git_clone_url else git_clone_url}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{PLATFORM_API_URL}/start",
                json={
                    "project_id": project_id,
                    "name": name,
                    "description": description,
                    "team_id": team_id or "dev",
                    "execution_mode": execution_mode,
                    "mission_control_url": "http://192.168.80.203:4000",  # Host IP for Platform API access
                    "git_clone_url": git_clone_url  # Git repo URL for committing code
                }
            )
            if response.status_code == 200:
                print(f"✅ Successfully dispatched project {project_id} to Platform API")
            else:
                print(f"❌ Platform API error: {response.status_code} - {response.text}")
    except httpx.ConnectError as e:
        print(f"⚠️ Platform API not available at {PLATFORM_API_URL}: {e}")
    except Exception as e:
        print(f"❌ Failed to dispatch to Platform API: {e}")


@router.post("/{project_id}/start", response_model=ProjectResponse)
async def start_project(project_id: str, background_tasks: BackgroundTasks):
    """Start a project - creates Git repo and triggers PM agent to create tasks"""
    try:
        oid = ObjectId(project_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    project = await projects_collection().find_one({"_id": oid})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_name = project.get("name", "Unnamed Project")
    project_desc = project.get("description", "")

    # Create Gitea repository for the project
    git_data = {}
    try:
        # Create repo name from project_id for uniqueness
        repo_name = f"project-{project_id}"
        repo = await gitea_service.create_repo(
            name=repo_name,
            description=f"{project_name}: {project_desc[:100]}",
            private=False
        )
        if repo:
            git_data = {
                "git_repo_name": repo["name"],
                "git_repo_url": repo["html_url"],
                "git_clone_url": gitea_service.get_clone_url_with_token(repo["name"]),
            }
            logger.info(f"Created Gitea repo for project {project_id}: {repo['html_url']}")
        else:
            logger.warning(f"Failed to create Gitea repo for project {project_id}")
    except Exception as e:
        logger.error(f"Error creating Gitea repo: {e}")

    # Update status to planning and add git info
    update_data = {
        "status": ProjectStatus.PLANNING,
        "started_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **git_data
    }
    await projects_collection().update_one({"_id": oid}, {"$set": update_data})

    # Dispatch to Platform API to trigger PM agent (background task)
    background_tasks.add_task(
        dispatch_to_platform,
        project_id=project_id,
        name=project_name,
        description=project_desc,
        team_id=project.get("team_id", "dev"),
        execution_mode=project.get("execution_mode", ExecutionMode.REVIEW_FIRST),
        git_clone_url=git_data.get("git_clone_url")
    )

    project = await projects_collection().find_one({"_id": oid})
    return project_to_response(project)


# Project working directory on the platform server
PLATFORM_PROJECTS_DIR = os.getenv("PLATFORM_PROJECTS_DIR", str(Path.home() / "witmind-data" / "projects" / "active"))


class ProjectCompleteRequest(BaseModel):
    output_dir: Optional[str] = None
    preview_url: Optional[str] = None


@router.post("/{project_id}/complete", response_model=ProjectResponse)
async def complete_project(project_id: str, request: Optional[ProjectCompleteRequest] = None):
    """
    Mark a project as completed.
    Sets completed_at timestamp and optionally output_dir/preview_url.
    """
    try:
        oid = ObjectId(project_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    project = await projects_collection().find_one({"_id": oid})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine output_dir - use provided or default to platform projects dir
    output_dir = None
    if request and request.output_dir:
        output_dir = request.output_dir
    else:
        # Default output dir on platform server
        output_dir = f"{PLATFORM_PROJECTS_DIR}/{project_id}"

    update_data = {
        "status": ProjectStatus.COMPLETED,
        "completed_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "output_dir": output_dir,
    }

    if request and request.preview_url:
        update_data["preview_url"] = request.preview_url

    await projects_collection().update_one(
        {"_id": oid},
        {"$set": update_data}
    )

    project = await projects_collection().find_one({"_id": oid})
    return project_to_response(project)


@router.get("/{project_id}/files")
async def list_project_files(project_id: str):
    """
    List files generated for a project.
    Returns a list of files in the project output directory.
    """
    try:
        oid = ObjectId(project_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    project = await projects_collection().find_one({"_id": oid})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    output_dir = project.get("output_dir")
    if not output_dir:
        output_dir = f"{PLATFORM_PROJECTS_DIR}/{project_id}"

    # List files from the platform server via Platform API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{PLATFORM_API_URL}/project-files/{project_id}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                # Return empty list if endpoint not available
                return {"files": [], "total_size": 0, "output_dir": output_dir}
    except:
        return {"files": [], "total_size": 0, "output_dir": output_dir}


@router.get("/{project_id}/download")
async def download_project(project_id: str):
    """
    Download all project files as a ZIP archive.
    Proxies the download from Platform API.
    """
    try:
        oid = ObjectId(project_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    project = await projects_collection().find_one({"_id": oid})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_name = project.get("name", "project").replace(" ", "_").lower()

    # Proxy download from Platform API
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"{PLATFORM_API_URL}/project-download/{project_id}",
                follow_redirects=True
            )
            if response.status_code == 200:
                return StreamingResponse(
                    io.BytesIO(response.content),
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f"attachment; filename={project_name}.zip"
                    }
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to download project files"
                )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Platform API not available"
        )
