"""
Routes package
"""
from .projects import router as projects_router
from .tasks import router as tasks_router
from .agents import router as agents_router
from .activities import router as activities_router
from .approvals import router as approvals_router
from .events import router as events_router
from .auth import router as auth_router
from .gitea import router as gitea_router

__all__ = [
    "projects_router",
    "tasks_router",
    "agents_router",
    "activities_router",
    "approvals_router",
    "events_router",
    "auth_router",
    "gitea_router",
]
