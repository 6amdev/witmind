"""
Approval Request model - For human-in-the-loop agent approvals
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalType(str, Enum):
    CODE_CHANGE = "code_change"      # Agent wants to make code changes
    DEPLOY = "deploy"                # Agent wants to deploy
    EXTERNAL_API = "external_api"    # Agent wants to call external API
    FILE_DELETE = "file_delete"      # Agent wants to delete files
    INSTALL_PACKAGE = "install_package"  # Agent wants to install packages
    CUSTOM = "custom"                # Custom approval request


class ApprovalOption(BaseModel):
    """Option for approval (e.g., different approaches)"""
    id: str
    label: str
    description: Optional[str] = None


class ApprovalRequestCreate(BaseModel):
    """Create a new approval request"""
    agent_id: str
    project_id: str
    task_id: Optional[str] = None
    type: ApprovalType
    title: str
    description: str
    details: Optional[str] = None  # Markdown content for detailed view
    options: List[ApprovalOption] = []  # If multiple choices
    timeout_minutes: int = 30  # Auto-expire after this time
    metadata: Dict[str, Any] = {}  # Extra data for agent to use


class ApprovalRequest(BaseModel):
    """Approval request document"""
    id: str = Field(alias="_id")
    agent_id: str
    agent_name: str
    agent_icon: str
    project_id: str
    task_id: Optional[str] = None
    type: ApprovalType
    title: str
    description: str
    details: Optional[str] = None
    options: List[ApprovalOption] = []
    status: ApprovalStatus = ApprovalStatus.PENDING
    selected_option_id: Optional[str] = None
    response_note: Optional[str] = None
    responded_by: Optional[str] = None
    timeout_minutes: int = 30
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
    expires_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class ApprovalResponse(BaseModel):
    """API response for approval request"""
    id: str
    agent_id: str
    agent_name: str
    agent_icon: str
    project_id: str
    task_id: Optional[str] = None
    type: ApprovalType
    title: str
    description: str
    details: Optional[str] = None
    options: List[ApprovalOption] = []
    status: ApprovalStatus
    selected_option_id: Optional[str] = None
    response_note: Optional[str] = None
    responded_by: Optional[str] = None
    created_at: datetime
    responded_at: Optional[datetime] = None
    expires_at: datetime

    class Config:
        from_attributes = True


class ApprovalAction(BaseModel):
    """Action to approve or reject"""
    action: str  # "approve" or "reject"
    selected_option_id: Optional[str] = None
    note: Optional[str] = None


# Agent Command types
class AgentCommandType(str, Enum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    ABORT = "abort"


class AgentCommand(BaseModel):
    """Command to send to an agent"""
    command: AgentCommandType
    task_id: Optional[str] = None
    message: Optional[str] = None
