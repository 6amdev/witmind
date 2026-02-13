"""
Events Router - Receive events from Platform API and broadcast via Socket.io
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Any, Dict
from enum import Enum


router = APIRouter(prefix="/api/events", tags=["events"])


class EventType(str, Enum):
    AGENT_STATUS = "agent:status"
    AGENT_OUTPUT = "agent:output"
    AGENT_ACTION = "agent:action"
    AGENT_COMPLETE = "agent:complete"
    TASK_UPDATE = "task:update"
    PROJECT_COMPLETE = "project:complete"


class EventPayload(BaseModel):
    event_type: EventType
    data: Dict[str, Any]
    project_id: Optional[str] = None


@router.post("")
async def receive_event(payload: EventPayload):
    """
    Receive events from Platform API and broadcast via Socket.io

    This endpoint acts as a bridge between Platform API (task runner)
    and the frontend Socket.io clients.
    """
    from ..main import sio

    event_type = payload.event_type
    data = payload.data
    project_id = payload.project_id

    try:
        if event_type == EventType.AGENT_STATUS:
            # Broadcast agent status to all clients
            await sio.emit("agent:status", {
                "agent_id": data.get("agentId"),
                "status": data.get("status"),
                "task_id": data.get("taskId"),
            })

        elif event_type == EventType.AGENT_OUTPUT:
            # Broadcast agent output - streaming text
            await sio.emit("agent:output", {
                "agent_id": data.get("agentId"),
                "task_id": data.get("taskId"),
                "output": data.get("output"),
            })
            # Also send to project room if project_id provided
            if project_id:
                await sio.emit("agent:output", {
                    "agent_id": data.get("agentId"),
                    "task_id": data.get("taskId"),
                    "output": data.get("output"),
                }, room=f"project:{project_id}")

        elif event_type == EventType.AGENT_ACTION:
            # Agent action events (started, tool use, etc.)
            await sio.emit("agent:action", {
                "agent_id": data.get("agentId"),
                "task_id": data.get("taskId"),
                "action": data.get("type"),
                "message": data.get("message"),
            })

        elif event_type == EventType.AGENT_COMPLETE:
            # Agent completed task
            await sio.emit("agent:complete", {
                "agent_id": data.get("agentId"),
                "task_id": data.get("taskId"),
                "success": data.get("success"),
                "duration_ms": data.get("duration_ms"),
            })

        elif event_type == EventType.TASK_UPDATE:
            # Task status changed
            if project_id:
                await sio.emit("task:update", {
                    "task": data.get("task"),
                }, room=f"project:{project_id}")
            else:
                await sio.emit("task:update", {
                    "task": data.get("task"),
                })

        elif event_type == EventType.PROJECT_COMPLETE:
            # Project completed - all tasks done
            await sio.emit("project:complete", {
                "project_id": data.get("projectId"),
                "tasks_completed": data.get("tasksCompleted"),
            })
            # Also send to project room
            if project_id:
                await sio.emit("project:complete", {
                    "project_id": data.get("projectId"),
                    "tasks_completed": data.get("tasksCompleted"),
                }, room=f"project:{project_id}")

        return {"status": "ok", "event_type": event_type}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent-status")
async def broadcast_agent_status(
    agent_id: str,
    status: str,
    task_id: Optional[str] = None,
    project_id: Optional[str] = None
):
    """Shorthand endpoint for agent status updates"""
    from ..main import sio

    await sio.emit("agent:status", {
        "agent_id": agent_id,
        "status": status,
        "task_id": task_id,
    })

    return {"status": "ok"}


@router.post("/agent-output")
async def broadcast_agent_output(
    agent_id: str,
    task_id: str,
    output: str,
    project_id: Optional[str] = None
):
    """Shorthand endpoint for streaming agent output"""
    from ..main import sio

    data = {
        "agent_id": agent_id,
        "task_id": task_id,
        "output": output,
    }

    await sio.emit("agent:output", data)

    if project_id:
        await sio.emit("agent:output", data, room=f"project:{project_id}")

    return {"status": "ok"}
