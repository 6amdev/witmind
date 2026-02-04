"""
Team detector service - Auto-detect project type and team from description
"""
import re
from typing import Dict


# Keywords for each project type
TYPE_KEYWORDS = {
    "web": [
        "website", "web app", "web application", "landing page", "frontend",
        "react", "vue", "angular", "html", "css", "responsive", "dashboard",
        "admin panel", "portal", "single page", "spa", "เว็บไซต์", "เว็บ",
        "หน้าเว็บ", "แดชบอร์ด"
    ],
    "api": [
        "api", "backend", "rest", "graphql", "microservice", "service",
        "endpoint", "server", "authentication", "database", "เซิร์ฟเวอร์",
        "แบ็คเอนด์"
    ],
    "mobile": [
        "mobile", "ios", "android", "app", "flutter", "react native",
        "swift", "kotlin", "แอพ", "แอปพลิเคชัน", "มือถือ"
    ],
    "marketing": [
        "marketing", "campaign", "content", "seo", "social media", "ads",
        "advertisement", "promotion", "email marketing", "การตลาด", "โฆษณา",
        "แคมเปญ"
    ],
    "creative": [
        "design", "logo", "branding", "graphics", "video", "animation",
        "motion", "ui/ux", "prototype", "mockup", "ออกแบบ", "โลโก้",
        "กราฟิก", "วิดีโอ"
    ],
}

# Team mapping
TYPE_TO_TEAM = {
    "web": "dev",
    "api": "dev",
    "mobile": "dev",
    "marketing": "marketing",
    "creative": "creative",
}


def detect_team(description: str) -> Dict[str, str]:
    """
    Detect project type and team from description

    Args:
        description: Project description text

    Returns:
        Dict with 'type' and 'team_id' keys
    """
    description_lower = description.lower()

    # Count keyword matches for each type
    scores = {ptype: 0 for ptype in TYPE_KEYWORDS}

    for ptype, keywords in TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in description_lower:
                scores[ptype] += 1

    # Get type with highest score
    max_score = max(scores.values())

    if max_score == 0:
        # Default to web/dev if no keywords matched
        return {"type": "web", "team_id": "dev"}

    # Get best matching type
    best_type = max(scores, key=scores.get)

    return {
        "type": best_type,
        "team_id": TYPE_TO_TEAM[best_type],
    }


def get_team_agents(team_id: str) -> list:
    """Get list of agent IDs for a team"""
    from ..models import DEV_AGENTS, MARKETING_AGENTS, CREATIVE_AGENTS

    if team_id == "dev":
        return [a["id"] for a in DEV_AGENTS]
    elif team_id == "marketing":
        return [a["id"] for a in MARKETING_AGENTS]
    elif team_id == "creative":
        return [a["id"] for a in CREATIVE_AGENTS]
    return []
