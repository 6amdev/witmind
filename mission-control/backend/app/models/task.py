"""
Task model
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PLANNED = "planned"
    ASSIGNED = "assigned"
    WORKING = "working"
    TESTING = "testing"
    REVIEW = "review"
    DONE = "done"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(str, Enum):
    FEATURE = "feature"
    BUG = "bug"
    IMPROVEMENT = "improvement"
    DOCS = "docs"
    DESIGN = "design"
    REVIEW = "review"


class ChecklistItem(BaseModel):
    id: str
    text: str
    done: bool = False
    done_at: Optional[datetime] = None


class Attachment(BaseModel):
    id: str
    name: str
    url: str
    type: str
    size: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: TaskType = TaskType.FEATURE
    priority: TaskPriority = TaskPriority.NORMAL
    labels: List[str] = []


class TaskCreate(TaskBase):
    """Task creation - project_id comes from URL path"""
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[str] = None
    labels: Optional[List[str]] = None


class TaskMove(BaseModel):
    status: TaskStatus
    order: Optional[int] = None


class Task(TaskBase):
    id: str = Field(alias="_id")
    project_id: str
    status: TaskStatus = TaskStatus.PLANNED
    assigned_to: Optional[str] = None  # agent_id
    assigned_by: Optional[str] = None  # agent_id or "user"
    checklist: List[ChecklistItem] = []
    attachments: List[Attachment] = []
    order: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class TaskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    type: TaskType
    status: TaskStatus
    priority: TaskPriority
    assigned_to: Optional[str] = None
    labels: List[str] = []
    checklist: List[ChecklistItem] = []
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
