"""
Projects API routes
"""
import os
import logging
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List
from datetime import datetime
from bson import ObjectId
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
)
from ..services.team_detector import detect_team

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
        created_at=project.get("created_at", datetime.utcnow()),
        updated_at=project.get("updated_at", datetime.utcnow()),
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


async def dispatch_to_platform(project_id: str, name: str, description: str, team_id: str):
    """Background task to dispatch project to Platform API"""
    print(f"🚀 Dispatching project {project_id} to Platform API at {PLATFORM_API_URL}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{PLATFORM_API_URL}/start",
                json={
                    "project_id": project_id,
                    "name": name,
                    "description": description,
                    "team_id": team_id or "dev",
                    "mission_control_url": "http://192.168.80.203:4000"  # Host IP for Platform API access
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
    """Start a project - triggers PM agent to create tasks"""
    try:
        oid = ObjectId(project_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    project = await projects_collection().find_one({"_id": oid})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update status to planning
    await projects_collection().update_one(
        {"_id": oid},
        {
            "$set": {
                "status": ProjectStatus.PLANNING,
                "started_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # Dispatch to Platform API to trigger PM agent (background task)
    background_tasks.add_task(
        dispatch_to_platform,
        project_id=project_id,
        name=project.get("name", "Unnamed Project"),
        description=project.get("description", ""),
        team_id=project.get("team_id", "dev")
    )

    project = await projects_collection().find_one({"_id": oid})
    return project_to_response(project)
