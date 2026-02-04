#!/usr/bin/env python3
"""
6AMDev AI Platform - Orchestrator Engine
Main workflow management system
"""

import os
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from task_queue import TaskQueue
from llm_router import LLMRouter
from agent_runner import AgentRunner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger('orchestrator')


class ProjectStatus(Enum):
    INBOX = "inbox"
    ACTIVE = "active"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


class StageStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Project:
    id: str
    name: str
    description: str
    team: str
    status: ProjectStatus
    current_stage: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict


class Orchestrator:
    """Main orchestration engine for managing AI team workflows"""

    def __init__(self, config_path: str = None):
        self.root_path = Path(os.environ.get('WITMIND_ROOT', '/home/wit/6amdev'))
        self.config_path = config_path or self.root_path / 'core' / 'config'

        # Load configuration
        self.settings = self._load_yaml('settings.yaml')
        self.llm_config = self._load_yaml('llm_providers.yaml')

        # Initialize components
        self.task_queue = TaskQueue()
        self.llm_router = LLMRouter(self.llm_config)
        self.agent_runner = AgentRunner(self.root_path, self.llm_router)

        # Load teams
        self.teams = self._load_teams()

        logger.info(f"Orchestrator initialized with {len(self.teams)} teams")

    def _load_yaml(self, filename: str) -> Dict:
        """Load YAML configuration file"""
        filepath = self.config_path / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def _load_teams(self) -> Dict:
        """Load all team configurations"""
        teams = {}
        teams_path = self.root_path / 'teams'

        for team_dir in teams_path.iterdir():
            if team_dir.is_dir() and not team_dir.name.startswith('_'):
                team_yaml = team_dir / 'team.yaml'
                if team_yaml.exists():
                    with open(team_yaml, 'r', encoding='utf-8') as f:
                        team_config = yaml.safe_load(f)
                        team_id = team_config.get('team', {}).get('id')
                        if team_id:
                            teams[team_id] = team_config
                            logger.info(f"Loaded team: {team_id}")

        return teams

    def watch_inbox(self):
        """Watch inbox for new project requests"""
        inbox_path = self.root_path / 'projects' / 'inbox'

        for request_file in inbox_path.glob('*.yaml'):
            logger.info(f"Found new request: {request_file.name}")
            self.process_request(request_file)

    def process_request(self, request_path: Path):
        """Process a new project request"""
        with open(request_path, 'r', encoding='utf-8') as f:
            request = yaml.safe_load(f)

        # Determine which team should handle this
        team_id = self._select_team(request)
        if not team_id:
            logger.error(f"No team found for request: {request_path.name}")
            return None

        # Create project
        project = self._create_project(request, team_id)

        # Start workflow
        self.start_workflow(project)

        # Move request file to processed
        request_path.unlink()

        return project

    def _select_team(self, request: Dict) -> Optional[str]:
        """Select appropriate team based on request"""
        request_type = request.get('type', '').lower()
        keywords = request.get('description', '').lower()

        for team_id, team_config in self.teams.items():
            handles = team_config.get('team', {}).get('handles', [])
            for handle in handles:
                if handle in request_type or handle in keywords:
                    return team_id

        # Default to dev team
        return 'dev' if 'dev' in self.teams else None

    def _create_project(self, request: Dict, team_id: str) -> Project:
        """Create a new project from request"""
        project_id = f"proj-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        project = Project(
            id=project_id,
            name=request.get('title', project_id),
            description=request.get('description', ''),
            team=team_id,
            status=ProjectStatus.ACTIVE,
            current_stage='intake',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=request
        )

        # Create project directory
        project_path = self.root_path / 'projects' / 'active' / project_id
        project_path.mkdir(parents=True, exist_ok=True)

        # Save project config
        project_yaml = {
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'team': project.team,
                'status': project.status.value,
                'current_stage': project.current_stage,
                'created_at': project.created_at.isoformat(),
            }
        }

        with open(project_path / 'PROJECT.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(project_yaml, f, allow_unicode=True)

        logger.info(f"Created project: {project_id} for team: {team_id}")
        return project

    def start_workflow(self, project: Project):
        """Start the workflow for a project"""
        team_config = self.teams.get(project.team)
        if not team_config:
            logger.error(f"Team not found: {project.team}")
            return

        workflow_name = team_config.get('team', {}).get('default_workflow', 'new_project')
        workflow_path = self.root_path / 'teams' / project.team / 'workflows' / f'{workflow_name}.yaml'

        if not workflow_path.exists():
            logger.warning(f"Workflow not found: {workflow_path}, using default flow")
            self._run_default_workflow(project)
            return

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = yaml.safe_load(f)

        self._execute_workflow(project, workflow)

    def _run_default_workflow(self, project: Project):
        """Run default workflow when no workflow file exists"""
        stages = ['pm', 'tech_lead', 'frontend_dev', 'qa_tester', 'devops']

        for agent_id in stages:
            logger.info(f"Running agent: {agent_id} for project: {project.id}")
            result = self.agent_runner.run(agent_id, project.team, project.id)

            if not result.get('success'):
                logger.error(f"Agent {agent_id} failed: {result.get('error')}")
                if result.get('needs_input'):
                    self._request_user_input(project, agent_id, result)
                    break

    def _execute_workflow(self, project: Project, workflow: Dict):
        """Execute a workflow definition"""
        stages = workflow.get('workflow', {}).get('stages', [])

        for stage in stages:
            stage_name = stage.get('stage')
            agent_id = stage.get('agent')

            logger.info(f"Executing stage: {stage_name} with agent: {agent_id}")

            # Check conditions
            condition = stage.get('condition')
            if condition and not self._check_condition(project, condition):
                logger.info(f"Skipping stage {stage_name}: condition not met")
                continue

            # Run agent
            result = self.agent_runner.run(agent_id, project.team, project.id)

            # Handle result
            if result.get('success'):
                project.current_stage = stage.get('next', stage_name)
            else:
                if result.get('needs_input'):
                    self._request_user_input(project, agent_id, result)
                    break
                else:
                    on_error = stage.get('on_error', 'stop')
                    if on_error == 'ask_user':
                        self._request_user_input(project, agent_id, result)
                    break

        # Update project status
        self._update_project(project)

    def _check_condition(self, project: Project, condition: str) -> bool:
        """Check if a condition is met"""
        # Simple condition checking - can be expanded
        project_path = self.root_path / 'projects' / 'active' / project.id

        if condition == 'has_frontend':
            return (project_path / 'ARCHITECTURE.md').exists()
        elif condition == 'has_backend':
            return (project_path / 'ARCHITECTURE.md').exists()

        return True

    def _request_user_input(self, project: Project, agent_id: str, result: Dict):
        """Request input from user"""
        logger.warning(f"User input required for project {project.id}")

        # Save pending state
        pending_file = self.root_path / 'projects' / 'active' / project.id / '.pending_input'
        with open(pending_file, 'w') as f:
            json.dump({
                'agent': agent_id,
                'question': result.get('question', 'Input required'),
                'options': result.get('options', []),
                'timestamp': datetime.now().isoformat()
            }, f)

    def _update_project(self, project: Project):
        """Update project status"""
        project.updated_at = datetime.now()
        project_path = self.root_path / 'projects' / 'active' / project.id / 'PROJECT.yaml'

        with open(project_path, 'r', encoding='utf-8') as f:
            project_yaml = yaml.safe_load(f)

        project_yaml['project']['status'] = project.status.value
        project_yaml['project']['current_stage'] = project.current_stage
        project_yaml['project']['updated_at'] = project.updated_at.isoformat()

        with open(project_path, 'w', encoding='utf-8') as f:
            yaml.dump(project_yaml, f, allow_unicode=True)

    def get_status(self) -> Dict:
        """Get current system status"""
        projects_path = self.root_path / 'projects'

        status = {
            'teams': list(self.teams.keys()),
            'projects': {
                'inbox': len(list((projects_path / 'inbox').glob('*.yaml'))),
                'active': len(list((projects_path / 'active').iterdir())),
                'review': len(list((projects_path / 'review').iterdir())),
                'completed': len(list((projects_path / 'completed').iterdir())),
            },
            'queue': self.task_queue.get_stats(),
        }

        return status


def main():
    """Main entry point"""
    orchestrator = Orchestrator()

    # Check for new requests
    orchestrator.watch_inbox()

    # Print status
    status = orchestrator.get_status()
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    main()
