"""
Tasks API routes
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from ..database import tasks_collection, projects_collection, activities_collection
from ..models import (
    Task,
    TaskCreate,
    TaskUpdate,
    TaskMove,
    TaskResponse,
    TaskStatus,
    ActivityType,
    ActorType,
)

router = APIRouter(prefix="/api", tags=["tasks"])


def task_to_response(task: dict) -> TaskResponse:
    """Convert MongoDB document to TaskResponse"""
    return TaskResponse(
        id=str(task["_id"]),
        project_id=task["project_id"],
        title=task["title"],
        description=task.get("description"),
        type=task.get("type", "feature"),
        status=task.get("status", TaskStatus.PLANNED),
        priority=task.get("priority", "normal"),
        assigned_to=task.get("assigned_to"),
        labels=task.get("labels", []),
        checklist=task.get("checklist", []),
        order=task.get("order", 0),
        created_at=task.get("created_at", datetime.utcnow()),
        updated_at=task.get("updated_at", datetime.utcnow()),
    )


@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
async def list_project_tasks(project_id: str, status: Optional[TaskStatus] = None):
    """List all tasks for a project"""
    query = {"project_id": project_id}
    if status:
        query["status"] = status

    cursor = tasks_collection().find(query).sort([("status", 1), ("order", 1)])
    tasks = await cursor.to_list(500)
    return [task_to_response(t) for t in tasks]


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(project_id: str, task: TaskCreate):
    """Create a new task"""
    # Verify project exists
    try:
        project = await projects_collection().find_one({"_id": ObjectId(project_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get next order number
    last_task = await tasks_collection().find_one(
        {"project_id": project_id, "status": TaskStatus.PLANNED},
        sort=[("order", -1)]
    )
    next_order = (last_task.get("order", 0) + 1) if last_task else 0

    doc = {
        "project_id": project_id,
        "title": task.title,
        "description": task.description,
        "type": task.type,
        "priority": task.priority,
        "labels": task.labels,
        "status": TaskStatus.PLANNED,
        "checklist": [],
        "attachments": [],
        "order": next_order,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await tasks_collection().insert_one(doc)
    doc["_id"] = result.inserted_id

    # Log activity
    await activities_collection().insert_one({
        "project_id": project_id,
        "task_id": str(result.inserted_id),
        "type": ActivityType.CREATED,
        "actor_type": ActorType.SYSTEM,
        "actor_id": "system",
        "actor_name": "System",
        "actor_icon": "🤖",
        "content": {"text": f"Task created: {task.title}"},
        "created_at": datetime.utcnow(),
    })

    return task_to_response(doc)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a task by ID"""
    try:
        task = await tasks_collection().find_one({"_id": ObjectId(task_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_to_response(task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, update: TaskUpdate):
    """Update a task"""
    try:
        oid = ObjectId(task_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    task = await tasks_collection().find_one({"_id": oid})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.get("status")
    old_assigned = task.get("assigned_to")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()

    await tasks_collection().update_one({"_id": oid}, {"$set": update_data})

    # Log status change
    if update.status and update.status != old_status:
        await activities_collection().insert_one({
            "project_id": task["project_id"],
            "task_id": task_id,
            "type": ActivityType.STATUS_CHANGE,
            "actor_type": ActorType.SYSTEM,
            "actor_id": "system",
            "actor_name": "System",
            "actor_icon": "🤖",
            "content": {"from_status": old_status, "to_status": update.status},
            "created_at": datetime.utcnow(),
        })

    # Log assignment
    if update.assigned_to and update.assigned_to != old_assigned:
        await activities_collection().insert_one({
            "project_id": task["project_id"],
            "task_id": task_id,
            "type": ActivityType.ASSIGNMENT,
            "actor_type": ActorType.SYSTEM,
            "actor_id": "system",
            "actor_name": "System",
            "actor_icon": "🤖",
            "content": {"text": f"Assigned to {update.assigned_to}"},
            "created_at": datetime.utcnow(),
        })

    task = await tasks_collection().find_one({"_id": oid})
    return task_to_response(task)


@router.patch("/tasks/{task_id}/move", response_model=TaskResponse)
async def move_task(task_id: str, move: TaskMove):
    """Move a task to a new status/position"""
    try:
        oid = ObjectId(task_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    task = await tasks_collection().find_one({"_id": oid})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.get("status")

    update_data = {
        "status": move.status,
        "updated_at": datetime.utcnow(),
    }

    if move.order is not None:
        update_data["order"] = move.order

    # Set started_at when moving to WORKING
    if move.status == TaskStatus.WORKING and not task.get("started_at"):
        update_data["started_at"] = datetime.utcnow()

    # Set completed_at when moving to DONE
    if move.status == TaskStatus.DONE:
        update_data["completed_at"] = datetime.utcnow()

    await tasks_collection().update_one({"_id": oid}, {"$set": update_data})

    # Log status change
    if move.status != old_status:
        await activities_collection().insert_one({
            "project_id": task["project_id"],
            "task_id": task_id,
            "type": ActivityType.STATUS_CHANGE,
            "actor_type": ActorType.USER,
            "actor_id": "user",
            "actor_name": "User",
            "actor_icon": "👤",
            "content": {"from_status": old_status, "to_status": move.status},
            "created_at": datetime.utcnow(),
        })

    task = await tasks_collection().find_one({"_id": oid})
    return task_to_response(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str):
    """Delete a task"""
    try:
        oid = ObjectId(task_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid task ID")

    result = await tasks_collection().delete_one({"_id": oid})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    # Delete associated activities
    await activities_collection().delete_many({"task_id": task_id})
