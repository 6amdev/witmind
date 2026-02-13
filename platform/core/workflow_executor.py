#!/usr/bin/env python3
"""
Workflow Executor - Execute workflows with real intelligent agents

Combines:
- Agent definitions (YAML)
- Workflow templates (smart agent selection)
- Intelligent agents (agentic execution)
- Workflow engine (orchestration)
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from core.agent_loader import load_all_agents
from core.workflow_templates import get_template, suggest_template, WorkflowTemplate
from core.workflow_engine import WorkflowEngine, WorkflowStage
from core.monitoring import MetricsCollector, track_execution

logger = logging.getLogger('workflow_executor')


class WorkflowExecutor:
    """Execute workflows using templates and real agents"""

    def __init__(
        self,
        agents_dir: Path,
        projects_dir: Path,
        metrics_dir: Optional[Path] = None
    ):
        self.agents_dir = agents_dir
        self.projects_dir = projects_dir
        self.metrics_collector = MetricsCollector(metrics_dir) if metrics_dir else None

        # Cache for loaded agents (per project)
        self.agents_cache: Dict[str, Dict] = {}

    def execute_from_template(
        self,
        template_id: str,
        project_name: str,
        project_description: str,
        auto_approve: bool = False
    ) -> Dict:
        """
        Execute a workflow using a template.

        Args:
            template_id: Template ID (e.g., 'fullstack_app')
            project_name: Project name
            project_description: What to build
            auto_approve: Skip approval gates

        Returns:
            Execution result with deliverables
        """
        # Get template
        template = get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Create project directory
        project_root = self.projects_dir / project_name
        project_root.mkdir(parents=True, exist_ok=True)

        # Write initial request
        request_file = project_root / 'REQUEST.md'
        request_file.write_text(f"""# Project: {project_name}

## Description
{project_description}

## Template
{template.name}

## Created
{datetime.now().isoformat()}
""")

        logger.info(f"🚀 Starting workflow: {template.name}")
        logger.info(f"   Project: {project_name}")
        logger.info(f"   Agents: {', '.join(template.agents)}")

        # Load agents
        agents = self._load_agents_for_project(project_root, template)

        # Create workflow stages from template
        stages = self._template_to_stages(template)

        # Create workflow engine
        engine = WorkflowEngine(project_root, stages)

        # Register agents
        for agent_id, agent in agents.items():
            engine.register_agent(agent_id, agent)

        # Execute workflow
        def approval_callback(stage_id: str) -> bool:
            if auto_approve:
                logger.info(f"✅ Auto-approved: {stage_id}")
                return True
            else:
                # TODO: Implement UI approval
                response = input(f"Approve stage '{stage_id}'? (y/n): ")
                return response.lower() == 'y'

        result = engine.execute(
            on_approval_needed=approval_callback if not auto_approve else None
        )

        # Log metrics
        if self.metrics_collector:
            # TODO: Collect metrics from workflow execution
            pass

        logger.info(f"✅ Workflow completed!")
        logger.info(f"   Success: {result['success']}")
        logger.info(f"   Stages: {result['completed_stages']}/{result['total_stages']}")

        return result

    def execute_auto(
        self,
        project_name: str,
        project_description: str,
        auto_approve: bool = True
    ) -> Dict:
        """
        Auto-detect best template and execute.

        This is the "magic" mode - just describe what you want!
        """
        # Suggest template
        template = suggest_template(project_description)

        logger.info(f"🤖 Auto-selected template: {template.name}")

        return self.execute_from_template(
            template.id,
            project_name,
            project_description,
            auto_approve
        )

    def _load_agents_for_project(
        self,
        project_root: Path,
        template: WorkflowTemplate
    ) -> Dict:
        """Load only agents needed for this template"""

        # Check cache
        cache_key = str(project_root)
        if cache_key in self.agents_cache:
            return self.agents_cache[cache_key]

        # Load all agents (TODO: optimize to load only needed ones)
        all_agents = load_all_agents(self.agents_dir, project_root)

        # Filter to template agents
        agents = {
            agent_id: all_agents[agent_id]
            for agent_id in template.agents
            if agent_id in all_agents
        }

        self.agents_cache[cache_key] = agents
        return agents

    def _template_to_stages(self, template: WorkflowTemplate) -> List[WorkflowStage]:
        """Convert template to workflow stages"""
        stages = []

        # Simple sequential stages
        for i, agent_id in enumerate(template.agents):
            stage = WorkflowStage(
                stage_id=f"stage_{i}_{agent_id}",
                agent_id=agent_id,
                task={
                    'type': 'execute',
                    'description': f'Execute {agent_id} task'
                },
                dependencies=[f"stage_{i-1}_{template.agents[i-1]}"] if i > 0 else []
            )
            stages.append(stage)

        # TODO: Handle parallel stages from template.parallel_stages

        return stages


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    executor = WorkflowExecutor(
        agents_dir=Path(__file__).parent.parent / 'teams',
        projects_dir=Path(__file__).parent.parent.parent / 'test_projects',
        metrics_dir=Path(__file__).parent.parent.parent / 'metrics'
    )

    # Execute with template
    result = executor.execute_from_template(
        template_id='simple_website',
        project_name='my_portfolio',
        project_description='Create a personal portfolio website with dark theme',
        auto_approve=True
    )

    print(f"\n✅ Result: {result}")
