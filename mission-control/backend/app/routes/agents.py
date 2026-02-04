"""
Agents API routes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from ..models import AgentResponse, AgentStatus, ALL_AGENTS, DEV_AGENTS, MARKETING_AGENTS, CREATIVE_AGENTS

router = APIRouter(prefix="/api/agents", tags=["agents"])

# In-memory agent status (will be replaced with Redis in production)
agent_statuses = {agent["id"]: AgentStatus.STANDBY for agent in ALL_AGENTS}
agent_tasks = {agent["id"]: None for agent in ALL_AGENTS}
agent_projects = {agent["id"]: None for agent in ALL_AGENTS}


def agent_to_response(agent: dict) -> AgentResponse:
    """Convert agent dict to AgentResponse"""
    return AgentResponse(
        id=agent["id"],
        name=agent["name"],
        team=agent["team"],
        role=agent["role"],
        description=agent.get("description", ""),
        icon=agent["icon"],
        status=agent_statuses.get(agent["id"], AgentStatus.STANDBY),
        current_task_id=agent_tasks.get(agent["id"]),
    )


@router.get("", response_model=List[AgentResponse])
async def list_agents(team: Optional[str] = None):
    """List all agents, optionally filtered by team"""
    if team == "dev":
        agents = DEV_AGENTS
    elif team == "marketing":
        agents = MARKETING_AGENTS
    elif team == "creative":
        agents = CREATIVE_AGENTS
    else:
        agents = ALL_AGENTS

    return [agent_to_response(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get an agent by ID"""
    for agent in ALL_AGENTS:
        if agent["id"] == agent_id:
            return agent_to_response(agent)

    raise HTTPException(status_code=404, detail="Agent not found")


@router.get("/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get current status of an agent"""
    if agent_id not in agent_statuses:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "agent_id": agent_id,
        "status": agent_statuses[agent_id],
        "current_task_id": agent_tasks[agent_id],
    }


@router.patch("/{agent_id}/status")
async def update_agent_status(agent_id: str, status: str, task_id: Optional[str] = None, project_id: Optional[str] = None):
    """
    Update agent status (called by agent or orchestrator).

    Example:
    ```
    PATCH /api/agents/backend_dev/status?status=working&task_id=task-123
    ```

    Valid statuses: standby, working, blocked, error, offline
    """
    if agent_id not in agent_statuses:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        new_status = AgentStatus(status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {[s.value for s in AgentStatus]}"
        )

    agent_statuses[agent_id] = new_status
    agent_tasks[agent_id] = task_id
    if project_id:
        agent_projects[agent_id] = project_id

    return {
        "agent_id": agent_id,
        "status": new_status,
        "current_task_id": task_id,
        "current_project_id": agent_projects.get(agent_id),
    }


# Internal functions for updating agent status (called by orchestrator)
def set_agent_status(agent_id: str, status: AgentStatus, task_id: Optional[str] = None):
    """Update agent status (internal use)"""
    if agent_id in agent_statuses:
        agent_statuses[agent_id] = status
        agent_tasks[agent_id] = task_id


def get_available_agents(team: str) -> List[str]:
    """Get list of available agents in a team"""
    if team == "dev":
        agents = DEV_AGENTS
    elif team == "marketing":
        agents = MARKETING_AGENTS
    elif team == "creative":
        agents = CREATIVE_AGENTS
    else:
        return []

    return [
        a["id"]
        for a in agents
        if agent_statuses.get(a["id"]) == AgentStatus.STANDBY
    ]
