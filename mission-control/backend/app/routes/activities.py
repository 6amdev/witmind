"""
Activities API routes
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime
from bson import ObjectId

from ..database import activities_collection, tasks_collection
from pydantic import BaseModel
from typing import Optional, List

from ..models import (
    Activity,
    ActivityCreate,
    ActivityResponse,
    ActivityType,
    ActorType,
    ActivityContent,
    AgentStatus,
    ALL_AGENTS,
)
from .agents import set_agent_status


# Simple request models for agent work
class AgentActivityLink(BaseModel):
    label: str
    url: Optional[str] = None
    path: Optional[str] = None
    type: str = "file"


class AgentActivityRequest(BaseModel):
    """Simple request for agents to report their work"""
    agent_id: str
    project_id: str
    task_id: Optional[str] = None
    type: str  # agent_started, agent_progress, agent_completed, agent_error
    message: str  # Human readable message
    output: Optional[str] = None  # Full output
    links: List[AgentActivityLink] = []  # Files, commits, etc.
    error: Optional[str] = None
    duration_ms: Optional[int] = None

router = APIRouter(prefix="/api", tags=["activities"])


def activity_to_response(activity: dict) -> ActivityResponse:
    """Convert MongoDB document to ActivityResponse"""
    return ActivityResponse(
        id=str(activity["_id"]),
        project_id=activity["project_id"],
        task_id=activity.get("task_id"),
        type=activity["type"],
        actor_type=activity["actor_type"],
        actor_id=activity["actor_id"],
        actor_name=activity["actor_name"],
        actor_icon=activity.get("actor_icon", "🤖"),
        content=ActivityContent(**activity.get("content", {})),
        parent_id=activity.get("parent_id"),
        reactions=activity.get("reactions", []),
        created_at=activity.get("created_at", datetime.utcnow()),
    )


@router.get("/projects/{project_id}/activities", response_model=List[ActivityResponse])
async def list_project_activities(project_id: str, limit: int = 50):
    """List all activities for a project"""
    cursor = (
        activities_collection()
        .find({"project_id": project_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    activities = await cursor.to_list(limit)
    return [activity_to_response(a) for a in activities]


@router.get("/tasks/{task_id}/activities", response_model=List[ActivityResponse])
async def list_task_activities(task_id: str, limit: int = 100):
    """List all activities for a task"""
    cursor = (
        activities_collection()
        .find({"task_id": task_id})
        .sort("created_at", 1)  # Chronological order for task activities
        .limit(limit)
    )
    activities = await cursor.to_list(limit)
    return [activity_to_response(a) for a in activities]


@router.post("/tasks/{task_id}/comments", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(task_id: str, text: str, parent_id: str = None):
    """Add a comment to a task"""
    # Verify task exists
    try:
        task = await tasks_collection().find_one({"_id": ObjectId(task_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    doc = {
        "project_id": task["project_id"],
        "task_id": task_id,
        "type": ActivityType.COMMENT,
        "actor_type": ActorType.USER,
        "actor_id": "user",  # TODO: Get from auth
        "actor_name": "User",  # TODO: Get from auth
        "actor_icon": "👤",
        "content": {"text": text, "mentions": []},
        "parent_id": parent_id,
        "reactions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await activities_collection().insert_one(doc)
    doc["_id"] = result.inserted_id

    return activity_to_response(doc)


@router.patch("/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(activity_id: str, text: str):
    """Update a comment"""
    try:
        oid = ObjectId(activity_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid activity ID")

    activity = await activities_collection().find_one({"_id": oid})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if activity["type"] != ActivityType.COMMENT:
        raise HTTPException(status_code=400, detail="Only comments can be edited")

    await activities_collection().update_one(
        {"_id": oid},
        {
            "$set": {
                "content.text": text,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    activity = await activities_collection().find_one({"_id": oid})
    return activity_to_response(activity)


@router.delete("/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(activity_id: str):
    """Delete an activity"""
    try:
        oid = ObjectId(activity_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid activity ID")

    result = await activities_collection().delete_one({"_id": oid})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Activity not found")


@router.post("/activities/{activity_id}/reactions")
async def add_reaction(activity_id: str, emoji: str):
    """Add a reaction to an activity"""
    try:
        oid = ObjectId(activity_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid activity ID")

    activity = await activities_collection().find_one({"_id": oid})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    reaction = {
        "emoji": emoji,
        "user_id": "user",  # TODO: Get from auth
        "created_at": datetime.utcnow(),
    }

    await activities_collection().update_one(
        {"_id": oid},
        {"$push": {"reactions": reaction}},
    )

    return {"status": "ok", "emoji": emoji}


# ============================================================================
# Agent Work Activities - Simple endpoints for agents to report their work
# ============================================================================

@router.post("/agent/activity", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_activity(request: AgentActivityRequest):
    """
    Simple endpoint for agents to report their work.

    Example:
    ```
    POST /api/agent/activity
    {
        "agent_id": "frontend_dev",
        "project_id": "proj-123",
        "task_id": "task-456",
        "type": "agent_started",
        "message": "Starting work on Login UI component"
    }
    ```

    Types:
    - agent_started: Agent started working on a task
    - agent_progress: Agent made progress (created file, etc.)
    - agent_completed: Agent finished the task
    - agent_error: Agent encountered an error
    """
    # Validate activity type
    type_map = {
        "agent_started": ActivityType.AGENT_STARTED,
        "agent_progress": ActivityType.AGENT_PROGRESS,
        "agent_completed": ActivityType.AGENT_COMPLETED,
        "agent_error": ActivityType.AGENT_ERROR,
    }

    if request.type not in type_map:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type. Must be one of: {list(type_map.keys())}"
        )

    # Get agent info (ALL_AGENTS is a list of dicts)
    agent = next((a for a in ALL_AGENTS if a["id"] == request.agent_id), None)
    if not agent:
        # Use default if agent not found
        agent_name = request.agent_id
        agent_icon = "🤖"
    else:
        agent_name = agent.get("name", request.agent_id)
        agent_icon = agent.get("icon", "🤖")

    # Build content
    content = {
        "message": request.message,
        "output": request.output,
        "links": [link.model_dump() for link in request.links],
        "error": request.error,
        "duration_ms": request.duration_ms,
    }

    doc = {
        "project_id": request.project_id,
        "task_id": request.task_id,
        "type": type_map[request.type],
        "actor_type": ActorType.AGENT,
        "actor_id": request.agent_id,
        "actor_name": agent_name,
        "actor_icon": agent_icon,
        "content": content,
        "parent_id": None,
        "reactions": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await activities_collection().insert_one(doc)
    doc["_id"] = result.inserted_id

    # Auto-update agent status based on activity type
    if request.type == "agent_started":
        set_agent_status(request.agent_id, AgentStatus.WORKING, request.task_id)
    elif request.type == "agent_completed":
        set_agent_status(request.agent_id, AgentStatus.STANDBY, None)
    elif request.type == "agent_error":
        set_agent_status(request.agent_id, AgentStatus.ERROR, request.task_id)

    return activity_to_response(doc)


@router.get("/activities/recent", response_model=List[ActivityResponse])
async def list_recent_activities(limit: int = 20, agent_types_only: bool = True):
    """
    List recent activities across all projects.
    Useful for a global activity feed.

    If agent_types_only=True, only returns agent work activities.
    """
    query = {}
    if agent_types_only:
        query["type"] = {
            "$in": [
                ActivityType.AGENT_STARTED,
                ActivityType.AGENT_PROGRESS,
                ActivityType.AGENT_COMPLETED,
                ActivityType.AGENT_ERROR,
            ]
        }

    cursor = (
        activities_collection()
        .find(query)
        .sort("created_at", -1)
        .limit(limit)
    )
    activities = await cursor.to_list(limit)
    return [activity_to_response(a) for a in activities]
