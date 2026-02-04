"""
Mission Control Backend API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

app = FastAPI(
    title="Mission Control API",
    description="Witmind AI Agent Platform API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.io
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)


@app.get("/")
async def root():
    return {"status": "ok", "service": "Mission Control API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/agents")
async def list_agents():
    """List all available agents"""
    # TODO: Load from agent YAML files
    return {"agents": []}


@app.get("/api/projects")
async def list_projects():
    """List all projects"""
    # TODO: Load from database
    return {"projects": []}


@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")


# Export for uvicorn
app = socket_app
