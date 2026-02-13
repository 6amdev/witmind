"""
Services package
"""
from .team_detector import detect_team, get_team_agents
from .gitea import gitea_service, GiteaService

__all__ = ["detect_team", "get_team_agents", "gitea_service", "GiteaService"]
