"""
Activity model for logging all actions
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ActivityType(str, Enum):
    COMMENT = "comment"
    STATUS_CHANGE = "status_change"
    ASSIGNMENT = "assignment"
    ATTACHMENT = "attachment"
    CHECKLIST = "checklist"
    CODE_CHANGE = "code_change"
    REVIEW = "review"
    BLOCKER = "blocker"
    CREATED = "created"
    # Agent work activities
    AGENT_STARTED = "agent_started"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"


class ActorType(str, Enum):
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"


class ActivityLink(BaseModel):
    """Link to file, URL, or resource"""
    label: str
    url: Optional[str] = None
    path: Optional[str] = None
    type: str = "file"  # file, url, commit, pr


class ActivityContent(BaseModel):
    # For comment
    text: Optional[str] = None
    mentions: List[str] = []

    # For status_change
    from_status: Optional[str] = None
    to_status: Optional[str] = None

    # For code_change
    files_changed: List[str] = []
    lines_added: int = 0
    lines_removed: int = 0
    commit_message: Optional[str] = None

    # For attachment
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None

    # For checklist
    item_id: Optional[str] = None
    item_text: Optional[str] = None
    checked: Optional[bool] = None

    # For agent work (agent_started, agent_progress, agent_completed, agent_error)
    message: Optional[str] = None  # Human-readable message
    output: Optional[str] = None  # Full output/result
    links: List[ActivityLink] = []  # Links to files, commits, PRs
    error: Optional[str] = None  # Error message if failed
    duration_ms: Optional[int] = None  # How long the work took


class ActivityBase(BaseModel):
    type: ActivityType
    content: ActivityContent = ActivityContent()


class ActivityCreate(ActivityBase):
    project_id: str
    task_id: Optional[str] = None


class Activity(ActivityBase):
    id: str = Field(alias="_id")
    project_id: str
    task_id: Optional[str] = None
    actor_type: ActorType
    actor_id: str
    actor_name: str
    actor_icon: str = "🤖"
    parent_id: Optional[str] = None  # For replies
    reactions: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class ActivityResponse(BaseModel):
    id: str
    project_id: str
    task_id: Optional[str] = None
    type: ActivityType
    actor_type: ActorType
    actor_id: str
    actor_name: str
    actor_icon: str
    content: ActivityContent
    parent_id: Optional[str] = None
    reactions: List[Dict[str, Any]] = []
    created_at: datetime

    class Config:
        from_attributes = True
