#!/usr/bin/env python3
"""
Agent Coordinator - ควบคุมการทำงานของหลาย agents

Key concepts:
1. Agents communicate via FILES (not direct messages)
2. Sequential execution (PM → Tech Lead → Frontend Dev)
3. Each agent reads inputs, creates outputs
4. Next agent picks up where previous left off
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .intelligent_agent import IntelligentAgent

logger = logging.getLogger('agent_coordinator')


@dataclass
class AgentHandoff:
    """Represents passing work from one agent to another"""
    from_agent: str
    to_agent: str
    trigger: str  # 'completion', 'file_created', 'manual'
    files_to_pass: List[str]  # Files created by from_agent that to_agent needs
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class AgentCoordinator:
    """
    Coordinates multiple agents working together.

    Example workflow:
    1. PM Agent analyzes request → creates SPEC.md
    2. Coordinator hands off to Tech Lead
    3. Tech Lead reads SPEC.md → creates ARCHITECTURE.md
    4. Coordinator hands off to Frontend Dev
    5. Frontend Dev reads ARCHITECTURE.md → creates code
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.agents: Dict[str, IntelligentAgent] = {}
        self.handoffs: List[AgentHandoff] = []

        logger.info(f"Agent Coordinator initialized for: {project_root}")

    def register_agent(self, agent_id: str, agent: IntelligentAgent):
        """Register an agent with the coordinator"""
        self.agents[agent_id] = agent
        logger.info(f"Registered agent: {agent_id}")

    def execute_workflow(self, workflow: List[Dict]) -> Dict:
        """
        Execute a workflow with multiple agents.

        Args:
            workflow: [
                {
                    'agent': 'pm',
                    'task': {
                        'type': 'analyze_requirements',
                        'inputs': ['REQUEST.md'],
                        'expected_outputs': ['SPEC.md', 'TASKS.md']
                    }
                },
                {
                    'agent': 'tech_lead',
                    'task': {
                        'type': 'design_architecture',
                        'inputs': ['SPEC.md', 'TASKS.md'],
                        'expected_outputs': ['ARCHITECTURE.md']
                    },
                    'wait_for': ['pm']  # Wait for PM to finish
                }
            ]

        Returns:
            {
                'success': True/False,
                'completed_agents': [...],
                'deliverables': {...},
                'error': None
            }
        """
        logger.info(f"Starting workflow with {len(workflow)} stages")

        completed_agents = []
        all_deliverables = {}

        for stage_idx, stage in enumerate(workflow):
            agent_id = stage['agent']
            task = stage['task']
            wait_for = stage.get('wait_for', [])

            logger.info(f"\n{'='*60}")
            logger.info(f"Stage {stage_idx + 1}: {agent_id}")
            logger.info(f"{'='*60}")

            # Check if dependencies are met
            if wait_for:
                missing = [a for a in wait_for if a not in completed_agents]
                if missing:
                    error = f"Cannot run {agent_id}: waiting for {missing}"
                    logger.error(error)
                    return {
                        'success': False,
                        'error': error,
                        'completed_agents': completed_agents
                    }

            # Get agent
            agent = self.agents.get(agent_id)
            if not agent:
                error = f"Agent {agent_id} not registered"
                logger.error(error)
                return {
                    'success': False,
                    'error': error,
                    'completed_agents': completed_agents
                }

            # Verify inputs exist
            for input_file in task.get('inputs', []):
                input_path = self.project_root / input_file
                if not input_path.exists():
                    error = f"Input file missing: {input_file}"
                    logger.error(error)
                    return {
                        'success': False,
                        'error': error,
                        'completed_agents': completed_agents
                    }

            # Execute agent
            logger.info(f"Executing {agent_id}...")
            result = agent.execute_task(task)

            # Check result
            if not result.get('success'):
                logger.error(f"{agent_id} failed: {result.get('error')}")

                # Handle needs_input
                if result.get('needs_input'):
                    return {
                        'success': False,
                        'needs_input': True,
                        'question': result['question'],
                        'agent': agent_id,
                        'completed_agents': completed_agents
                    }

                return {
                    'success': False,
                    'error': result.get('error'),
                    'agent': agent_id,
                    'completed_agents': completed_agents
                }

            # Success - record deliverables
            deliverables = result.get('deliverables', [])
            all_deliverables[agent_id] = deliverables
            completed_agents.append(agent_id)

            logger.info(f"✅ {agent_id} completed")
            logger.info(f"   Deliverables: {', '.join(deliverables)}")

            # Record handoff to next agent
            if stage_idx < len(workflow) - 1:
                next_stage = workflow[stage_idx + 1]
                next_agent = next_stage['agent']

                handoff = AgentHandoff(
                    from_agent=agent_id,
                    to_agent=next_agent,
                    trigger='completion',
                    files_to_pass=deliverables
                )
                self.handoffs.append(handoff)

                logger.info(f"📤 Handing off to {next_agent}")
                logger.info(f"   Files: {', '.join(deliverables)}")

        # All agents completed successfully
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Workflow completed successfully!")
        logger.info(f"{'='*60}")
        logger.info(f"Completed agents: {', '.join(completed_agents)}")

        return {
            'success': True,
            'completed_agents': completed_agents,
            'deliverables': all_deliverables,
            'handoffs': [
                {
                    'from': h.from_agent,
                    'to': h.to_agent,
                    'files': h.files_to_pass
                }
                for h in self.handoffs
            ]
        }

    def get_agent_outputs(self, agent_id: str) -> List[str]:
        """Get list of files created by an agent"""
        outputs = []
        for file_path in self.project_root.iterdir():
            if file_path.is_file():
                # Simple heuristic - could be improved
                outputs.append(file_path.name)
        return outputs

    def verify_handoff(self, from_agent: str, to_agent: str) -> bool:
        """Verify that handoff was successful"""
        # Check if files created by from_agent exist
        for handoff in self.handoffs:
            if handoff.from_agent == from_agent and handoff.to_agent == to_agent:
                for file_name in handoff.files_to_pass:
                    file_path = self.project_root / file_name
                    if not file_path.exists():
                        logger.error(f"Handoff failed: {file_name} not found")
                        return False
                return True
        return False


def create_simple_workflow(
    pm_agent: IntelligentAgent,
    tech_lead_agent: IntelligentAgent,
    project_root: Path
) -> AgentCoordinator:
    """
    Create a simple 2-agent workflow: PM → Tech Lead

    This is the most basic multi-agent collaboration.
    """
    coordinator = AgentCoordinator(project_root)

    # Register agents
    coordinator.register_agent('pm', pm_agent)
    coordinator.register_agent('tech_lead', tech_lead_agent)

    return coordinator


# Example workflow definition
SIMPLE_WORKFLOW = [
    {
        'agent': 'pm',
        'task': {
            'type': 'analyze_requirements',
            'description': 'Analyze project request and create specification',
            'inputs': ['REQUEST.md'],
            'expected_outputs': ['SPEC.md']
        }
    },
    {
        'agent': 'tech_lead',
        'task': {
            'type': 'design_architecture',
            'description': 'Design system architecture based on spec',
            'inputs': ['SPEC.md'],
            'expected_outputs': ['ARCHITECTURE.md']
        },
        'wait_for': ['pm']
    }
]

FULL_DEV_WORKFLOW = [
    {
        'agent': 'pm',
        'task': {
            'type': 'analyze_requirements',
            'inputs': ['REQUEST.md'],
            'expected_outputs': ['SPEC.md', 'TASKS.md']
        }
    },
    {
        'agent': 'tech_lead',
        'task': {
            'type': 'design_architecture',
            'inputs': ['SPEC.md', 'TASKS.md'],
            'expected_outputs': ['ARCHITECTURE.md', 'TECH_STACK.md']
        },
        'wait_for': ['pm']
    },
    {
        'agent': 'frontend_dev',
        'task': {
            'type': 'implement_frontend',
            'inputs': ['ARCHITECTURE.md', 'TASKS.md'],
            'expected_outputs': ['src/frontend/']
        },
        'wait_for': ['tech_lead']
    },
    {
        'agent': 'qa_tester',
        'task': {
            'type': 'test_application',
            'inputs': ['src/'],
            'expected_outputs': ['TEST_REPORT.md']
        },
        'wait_for': ['frontend_dev']
    }
]
