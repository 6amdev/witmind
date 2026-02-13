"""
Project model
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProjectType(str, Enum):
    WEB = "web"
    API = "api"
    MOBILE = "mobile"
    MARKETING = "marketing"
    CREATIVE = "creative"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ExecutionMode(str, Enum):
    FULL_AUTO = "full_auto"      # PM creates tasks → auto dispatch to dev agents → auto complete
    REVIEW_FIRST = "review_first"  # PM creates tasks → user reviews → manual dispatch
    MANUAL = "manual"            # User creates tasks manually → manual dispatch


class ProjectMember(BaseModel):
    user_id: str
    role: str = "editor"  # owner, editor, viewer
    added_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectBase(BaseModel):
    name: str
    description: str
    type: Optional[ProjectType] = None
    team_id: Optional[str] = None  # dev, marketing, creative
    execution_mode: ExecutionMode = ExecutionMode.REVIEW_FIRST


class ProjectCreate(ProjectBase):
    execution_mode: ExecutionMode = ExecutionMode.REVIEW_FIRST


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None


class Project(ProjectBase):
    id: str = Field(alias="_id")
    status: ProjectStatus = ProjectStatus.DRAFT
    progress: int = 0
    owner_id: Optional[str] = None
    members: List[ProjectMember] = []
    execution_mode: ExecutionMode = ExecutionMode.REVIEW_FIRST
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # Completion data
    output_dir: Optional[str] = None  # Directory with generated files
    preview_url: Optional[str] = None  # URL to preview the result
    # Git integration
    git_repo_name: Optional[str] = None  # Repository name in Gitea
    git_repo_url: Optional[str] = None  # Web URL for viewing repo
    git_clone_url: Optional[str] = None  # URL for cloning (with token)

    class Config:
        populate_by_name = True


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    type: Optional[ProjectType] = None
    team_id: Optional[str] = None
    status: ProjectStatus
    progress: int
    execution_mode: ExecutionMode = ExecutionMode.REVIEW_FIRST
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    output_dir: Optional[str] = None
    preview_url: Optional[str] = None
    # Git integration
    git_repo_name: Optional[str] = None
    git_repo_url: Optional[str] = None
    git_clone_url: Optional[str] = None

    class Config:
        from_attributes = True
