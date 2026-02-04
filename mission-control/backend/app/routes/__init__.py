"""
Routes package
"""
from .projects import router as projects_router
from .tasks import router as tasks_router
from .agents import router as agents_router
from .activities import router as activities_router
from .approvals import router as approvals_router

__all__ = [
    "projects_router",
    "tasks_router",
    "agents_router",
    "activities_router",
    "approvals_router",
]
