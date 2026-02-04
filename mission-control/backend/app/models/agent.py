"""
Agent model
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    STANDBY = "standby"
    WORKING = "working"
    BLOCKED = "blocked"
    ERROR = "error"
    OFFLINE = "offline"


class AgentTeam(str, Enum):
    DEV = "dev"
    MARKETING = "marketing"
    CREATIVE = "creative"


class Agent(BaseModel):
    id: str = Field(alias="_id")
    name: str
    team: AgentTeam
    role: str
    description: str
    icon: str
    capabilities: List[str] = []
    status: AgentStatus = AgentStatus.STANDBY
    current_task_id: Optional[str] = None
    current_project_id: Optional[str] = None
    last_active: Optional[datetime] = None

    class Config:
        populate_by_name = True


class AgentResponse(BaseModel):
    id: str
    name: str
    team: str
    role: str
    description: str
    icon: str
    status: AgentStatus
    current_task_id: Optional[str] = None

    class Config:
        from_attributes = True


# Predefined agents (loaded from YAML or hardcoded)
DEV_AGENTS = [
    {"id": "pm", "name": "Project Manager", "team": "dev", "role": "manager", "icon": "👔"},
    {"id": "business_analyst", "name": "Business Analyst", "team": "dev", "role": "analyst", "icon": "📋"},
    {"id": "tech_lead", "name": "Tech Lead", "team": "dev", "role": "architect", "icon": "🏗️"},
    {"id": "uxui_designer", "name": "UX/UI Designer", "team": "dev", "role": "designer", "icon": "🎨"},
    {"id": "frontend_dev", "name": "Frontend Developer", "team": "dev", "role": "developer", "icon": "💻"},
    {"id": "backend_dev", "name": "Backend Developer", "team": "dev", "role": "developer", "icon": "⚙️"},
    {"id": "fullstack_dev", "name": "Fullstack Developer", "team": "dev", "role": "developer", "icon": "🔧"},
    {"id": "mobile_dev", "name": "Mobile Developer", "team": "dev", "role": "developer", "icon": "📱"},
    {"id": "qa_tester", "name": "QA Tester", "team": "dev", "role": "tester", "icon": "🧪"},
    {"id": "security_auditor", "name": "Security Auditor", "team": "dev", "role": "security", "icon": "🔒"},
    {"id": "devops", "name": "DevOps Engineer", "team": "dev", "role": "devops", "icon": "🚀"},
]

MARKETING_AGENTS = [
    {"id": "marketing_lead", "name": "Marketing Lead", "team": "marketing", "role": "lead", "icon": "📊"},
    {"id": "content_writer", "name": "Content Writer", "team": "marketing", "role": "writer", "icon": "✍️"},
    {"id": "seo_specialist", "name": "SEO Specialist", "team": "marketing", "role": "specialist", "icon": "🔍"},
    {"id": "social_media_manager", "name": "Social Media Manager", "team": "marketing", "role": "manager", "icon": "📱"},
    {"id": "copywriter", "name": "Copywriter", "team": "marketing", "role": "writer", "icon": "📝"},
]

CREATIVE_AGENTS = [
    {"id": "creative_director", "name": "Creative Director", "team": "creative", "role": "director", "icon": "🎨"},
    {"id": "graphic_designer", "name": "Graphic Designer", "team": "creative", "role": "designer", "icon": "🖼️"},
    {"id": "ui_designer", "name": "UI Designer", "team": "creative", "role": "designer", "icon": "🎯"},
    {"id": "video_editor", "name": "Video Editor", "team": "creative", "role": "editor", "icon": "🎬"},
    {"id": "motion_designer", "name": "Motion Designer", "team": "creative", "role": "designer", "icon": "✨"},
]

ALL_AGENTS = DEV_AGENTS + MARKETING_AGENTS + CREATIVE_AGENTS
