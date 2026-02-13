#!/usr/bin/env python3
"""
Workflow Dashboard Backend - Port 5000

Real-time AI workflow execution dashboard
"""

import sys
from pathlib import Path

# Add platform to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'platform'))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import logging

from core.workflow_templates import list_templates, get_template, suggest_template
from core.workflow_executor import WorkflowExecutor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dashboard')

# Create app
app = FastAPI(title="Witmind Workflow Dashboard", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
AGENTS_DIR = Path(__file__).parent.parent.parent / 'platform' / 'teams'
PROJECTS_DIR = Path(__file__).parent.parent.parent / 'workflow_projects'
METRICS_DIR = Path(__file__).parent.parent.parent / 'metrics'

# Ensure directories exist
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)

# Executor
executor = WorkflowExecutor(
    agents_dir=AGENTS_DIR,
    projects_dir=PROJECTS_DIR,
    metrics_dir=METRICS_DIR
)

# WebSocket connections
active_connections: List[WebSocket] = []


# ============================================================================
# Models
# ============================================================================

class ProjectRequest(BaseModel):
    name: str
    description: str
    template_id: Optional[str] = None  # If None, auto-detect
    auto_approve: bool = True


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    agents: List[str]


# ============================================================================
# API Routes
# ============================================================================

@app.get("/")
async def root():
    return {
        "name": "Witmind Workflow Dashboard",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/templates", response_model=List[TemplateResponse])
async def get_templates():
    """Get all available workflow templates"""
    templates = list_templates()
    return [
        TemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            agents=t.agents
        )
        for t in templates
    ]


@app.get("/api/templates/suggest")
async def suggest_template_api(description: str):
    """Suggest best template for a description"""
    template = suggest_template(description)
    return TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        agents=template.agents
    )


@app.post("/api/projects/execute")
async def execute_project(request: ProjectRequest):
    """Execute a workflow"""
    try:
        logger.info(f"Starting workflow: {request.name}")

        # Broadcast start to WebSocket clients
        await broadcast({
            'type': 'workflow_start',
            'project': request.name,
            'description': request.description
        })

        # Execute workflow
        if request.template_id:
            result = executor.execute_from_template(
                template_id=request.template_id,
                project_name=request.name,
                project_description=request.description,
                auto_approve=request.auto_approve
            )
        else:
            result = executor.execute_auto(
                project_name=request.name,
                project_description=request.description,
                auto_approve=request.auto_approve
            )

        # Broadcast completion
        await broadcast({
            'type': 'workflow_complete',
            'project': request.name,
            'result': result
        })

        return {
            'success': True,
            'result': result
        }

    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        await broadcast({
            'type': 'workflow_error',
            'project': request.name,
            'error': str(e)
        })
        return {
            'success': False,
            'error': str(e)
        }


@app.get("/api/projects")
async def list_projects():
    """List all projects"""
    projects = []
    for project_dir in PROJECTS_DIR.iterdir():
        if project_dir.is_dir():
            projects.append({
                'name': project_dir.name,
                'path': str(project_dir)
            })
    return projects


# ============================================================================
# WebSocket
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back (or handle commands)
            await websocket.send_json({
                'type': 'pong',
                'data': data
            })

    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast(message: Dict):
    """Broadcast message to all connected clients"""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            pass


# ============================================================================
# Serve static files (frontend)
# ============================================================================

# Mount static files at the end
frontend_dir = Path(__file__).parent.parent / 'frontend'
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")


if __name__ == '__main__':
    import uvicorn

    print("🚀 Starting Witmind Workflow Dashboard")
    print("   Backend: http://localhost:5000")
    print("   API Docs: http://localhost:5000/docs")
    print()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
