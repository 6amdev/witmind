"""
Approvals API routes - Human-in-the-loop approval system
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime, timedelta
from bson import ObjectId

from ..database import approvals_collection, agent_commands_collection
from ..models import (
    ApprovalRequest,
    ApprovalRequestCreate,
    ApprovalResponse,
    ApprovalAction,
    ApprovalStatus,
    ApprovalType,
    AgentCommand,
    AgentCommandType,
    ALL_AGENTS,
)

router = APIRouter(prefix="/api", tags=["approvals"])


def approval_to_response(doc: dict) -> ApprovalResponse:
    """Convert MongoDB document to ApprovalResponse"""
    return ApprovalResponse(
        id=str(doc["_id"]),
        agent_id=doc["agent_id"],
        agent_name=doc["agent_name"],
        agent_icon=doc["agent_icon"],
        project_id=doc["project_id"],
        task_id=doc.get("task_id"),
        type=doc["type"],
        title=doc["title"],
        description=doc["description"],
        details=doc.get("details"),
        options=doc.get("options", []),
        status=doc["status"],
        selected_option_id=doc.get("selected_option_id"),
        response_note=doc.get("response_note"),
        responded_by=doc.get("responded_by"),
        created_at=doc["created_at"],
        responded_at=doc.get("responded_at"),
        expires_at=doc["expires_at"],
    )


# ============================================================================
# Approval Requests - Created by agents, responded to by humans
# ============================================================================

@router.post("/approvals", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
async def create_approval_request(request: ApprovalRequestCreate):
    """
    Create a new approval request (called by agents).

    Example:
    ```
    POST /api/approvals
    {
        "agent_id": "backend_dev",
        "project_id": "proj-123",
        "task_id": "task-456",
        "type": "code_change",
        "title": "Deploy to Production?",
        "description": "Ready to deploy v2.0.0 to production server",
        "details": "## Changes\\n- Feature A\\n- Feature B\\n\\n## Risk: Low",
        "options": [
            {"id": "now", "label": "Deploy Now", "description": "Deploy immediately"},
            {"id": "later", "label": "Schedule", "description": "Deploy at 2am"}
        ],
        "timeout_minutes": 60
    }
    ```
    """
    # Get agent info
    agent = next((a for a in ALL_AGENTS if a["id"] == request.agent_id), None)
    agent_name = agent.get("name", request.agent_id) if agent else request.agent_id
    agent_icon = agent.get("icon", "🤖") if agent else "🤖"

    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=request.timeout_minutes)

    doc = {
        "agent_id": request.agent_id,
        "agent_name": agent_name,
        "agent_icon": agent_icon,
        "project_id": request.project_id,
        "task_id": request.task_id,
        "type": request.type,
        "title": request.title,
        "description": request.description,
        "details": request.details,
        "options": [opt.model_dump() for opt in request.options],
        "status": ApprovalStatus.PENDING,
        "selected_option_id": None,
        "response_note": None,
        "responded_by": None,
        "timeout_minutes": request.timeout_minutes,
        "metadata": request.metadata,
        "created_at": now,
        "responded_at": None,
        "expires_at": expires_at,
    }

    result = await approvals_collection().insert_one(doc)
    doc["_id"] = result.inserted_id

    return approval_to_response(doc)


@router.get("/approvals", response_model=List[ApprovalResponse])
async def list_approvals(
    project_id: str = None,
    status: ApprovalStatus = None,
    pending_only: bool = True,
    limit: int = 20
):
    """
    List approval requests.

    - pending_only=True (default): Only show pending approvals
    - status: Filter by specific status
    - project_id: Filter by project
    """
    query = {}

    if project_id:
        query["project_id"] = project_id

    if status:
        query["status"] = status
    elif pending_only:
        query["status"] = ApprovalStatus.PENDING
        # Also filter out expired ones
        query["expires_at"] = {"$gt": datetime.utcnow()}

    cursor = (
        approvals_collection()
        .find(query)
        .sort("created_at", -1)
        .limit(limit)
    )
    approvals = await cursor.to_list(limit)
    return [approval_to_response(a) for a in approvals]


@router.get("/approvals/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: str):
    """Get a specific approval request"""
    try:
        oid = ObjectId(approval_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid approval ID")

    doc = await approvals_collection().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Approval not found")

    return approval_to_response(doc)


@router.post("/approvals/{approval_id}/respond", response_model=ApprovalResponse)
async def respond_to_approval(approval_id: str, action: ApprovalAction):
    """
    Respond to an approval request (approve or reject).

    Example:
    ```
    POST /api/approvals/{id}/respond
    {
        "action": "approve",
        "selected_option_id": "now",
        "note": "Approved - proceed with deployment"
    }
    ```
    """
    try:
        oid = ObjectId(approval_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid approval ID")

    doc = await approvals_collection().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Approval not found")

    if doc["status"] != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Approval already {doc['status']}")

    # Check if expired
    if datetime.utcnow() > doc["expires_at"]:
        await approvals_collection().update_one(
            {"_id": oid},
            {"$set": {"status": ApprovalStatus.EXPIRED}}
        )
        raise HTTPException(status_code=400, detail="Approval has expired")

    # Validate action
    if action.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")

    new_status = ApprovalStatus.APPROVED if action.action == "approve" else ApprovalStatus.REJECTED

    await approvals_collection().update_one(
        {"_id": oid},
        {
            "$set": {
                "status": new_status,
                "selected_option_id": action.selected_option_id,
                "response_note": action.note,
                "responded_by": "user",  # TODO: Get from auth
                "responded_at": datetime.utcnow(),
            }
        }
    )

    doc = await approvals_collection().find_one({"_id": oid})
    return approval_to_response(doc)


# ============================================================================
# Agent Commands - Sent by humans to control agents
# ============================================================================

@router.post("/agents/{agent_id}/command")
async def send_agent_command(agent_id: str, command: AgentCommand):
    """
    Send a command to an agent (start, pause, resume, abort).

    Example:
    ```
    POST /api/agents/backend_dev/command
    {
        "command": "pause",
        "task_id": "task-123",
        "message": "Please wait for approval"
    }
    ```

    The agent should poll for commands or receive via WebSocket.
    """
    # Validate agent exists
    agent = next((a for a in ALL_AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    doc = {
        "agent_id": agent_id,
        "command": command.command,
        "task_id": command.task_id,
        "message": command.message,
        "status": "pending",  # pending, delivered, executed
        "created_at": datetime.utcnow(),
        "delivered_at": None,
        "executed_at": None,
    }

    result = await agent_commands_collection().insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "agent_id": agent_id,
        "command": command.command,
        "status": "pending",
        "message": f"Command '{command.command}' sent to {agent['name']}"
    }


@router.get("/agents/{agent_id}/commands")
async def get_agent_commands(agent_id: str, pending_only: bool = True, limit: int = 10):
    """
    Get commands for an agent (called by agent to check for commands).
    """
    query = {"agent_id": agent_id}
    if pending_only:
        query["status"] = "pending"

    cursor = (
        agent_commands_collection()
        .find(query)
        .sort("created_at", -1)
        .limit(limit)
    )
    commands = await cursor.to_list(limit)

    return [
        {
            "id": str(c["_id"]),
            "command": c["command"],
            "task_id": c.get("task_id"),
            "message": c.get("message"),
            "created_at": c["created_at"],
        }
        for c in commands
    ]


@router.post("/agents/{agent_id}/commands/{command_id}/ack")
async def acknowledge_command(agent_id: str, command_id: str, executed: bool = True):
    """
    Acknowledge a command (called by agent after receiving/executing).
    """
    try:
        oid = ObjectId(command_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid command ID")

    doc = await agent_commands_collection().find_one({"_id": oid, "agent_id": agent_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Command not found")

    update = {
        "status": "executed" if executed else "delivered",
        "delivered_at": datetime.utcnow(),
    }
    if executed:
        update["executed_at"] = datetime.utcnow()

    await agent_commands_collection().update_one(
        {"_id": oid},
        {"$set": update}
    )

    return {"status": "ok", "command_id": command_id}
