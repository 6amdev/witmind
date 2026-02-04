"""
Mission Control v2 - Main Application
"""
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .database import connect_db, disconnect_db
from .routes import projects_router, tasks_router, agents_router, activities_router, approvals_router


# Socket.io server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.CORS_ORIGINS,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    # Startup
    print("🚀 Starting Mission Control v2...")
    await connect_db()
    yield
    # Shutdown
    await disconnect_db()
    print("👋 Mission Control v2 stopped")


# FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI Agent Task Management System",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(agents_router)
app.include_router(activities_router)
app.include_router(approvals_router)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}


# Root
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "2.0.0",
        "docs": "/docs",
    }


# =============================================================================
# Socket.io Events
# =============================================================================

@sio.event
async def connect(sid, environ):
    """Client connected"""
    print(f"🔌 Client connected: {sid}")


@sio.event
async def disconnect(sid):
    """Client disconnected"""
    print(f"🔌 Client disconnected: {sid}")


@sio.event
async def join_project(sid, data):
    """Join a project room for real-time updates"""
    project_id = data.get("project_id")
    if project_id:
        sio.enter_room(sid, f"project:{project_id}")
        print(f"📁 {sid} joined project:{project_id}")


@sio.event
async def leave_project(sid, data):
    """Leave a project room"""
    project_id = data.get("project_id")
    if project_id:
        sio.leave_room(sid, f"project:{project_id}")
        print(f"📁 {sid} left project:{project_id}")


# =============================================================================
# Helper functions for broadcasting events
# =============================================================================

async def broadcast_task_update(project_id: str, task: dict):
    """Broadcast task update to project room"""
    await sio.emit("task:update", {"task": task}, room=f"project:{project_id}")


async def broadcast_activity(project_id: str, activity: dict):
    """Broadcast new activity to project room"""
    await sio.emit("activity:new", {"activity": activity}, room=f"project:{project_id}")


async def broadcast_agent_status(agent_id: str, status: str, task_id: str = None):
    """Broadcast agent status change"""
    await sio.emit("agent:status", {
        "agent_id": agent_id,
        "status": status,
        "task_id": task_id,
    })


async def broadcast_agent_output(agent_id: str, task_id: str, output: str):
    """Broadcast agent output (streaming)"""
    await sio.emit("agent:output", {
        "agent_id": agent_id,
        "task_id": task_id,
        "output": output,
    })


# Mount Socket.io
socket_app = socketio.ASGIApp(sio, app)


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:socket_app",
        host="0.0.0.0",
        port=4000,
        reload=True,
    )
