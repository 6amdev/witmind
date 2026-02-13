#!/usr/bin/env python3
"""
Workflow Engine - Advanced multi-agent orchestration

Features:
1. Parallel execution - Run multiple agents at once
2. Conditional execution - Skip stages based on conditions
3. Approval gates - Ask user before proceeding
4. Error recovery - Retry, rollback, or continue on error
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from .intelligent_agent import IntelligentAgent
from .agent_coordinator import AgentCoordinator

logger = logging.getLogger('workflow_engine')


class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStage:
    """Represents a stage in the workflow"""
    id: str
    agent: str
    task: Dict
    status: StageStatus = StageStatus.PENDING

    # Dependencies
    wait_for: List[str] = field(default_factory=list)

    # Conditional execution
    condition: Optional[Callable] = None

    # Approval
    requires_approval: bool = False
    approval_message: Optional[str] = None

    # Error handling
    on_error: str = "stop"  # 'stop', 'skip', 'retry', 'ask_user'
    max_retries: int = 0
    retry_count: int = 0

    # Parallel execution
    can_run_parallel: bool = False
    parallel_group: Optional[str] = None

    # Results
    result: Optional[Dict] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class WorkflowEngine:
    """
    Advanced workflow engine for multi-agent orchestration.

    Key features:
    - Parallel execution
    - Approval gates
    - Conditional stages
    - Error recovery
    """

    def __init__(self, project_root: Path, max_parallel: int = 3):
        self.project_root = project_root
        self.max_parallel = max_parallel
        self.agents: Dict[str, IntelligentAgent] = {}
        self.stages: List[WorkflowStage] = []

        # Execution state
        self.current_stage_idx = 0
        self.completed_stages: List[str] = []
        self.failed_stages: List[str] = []

        logger.info(f"Workflow Engine initialized (max_parallel={max_parallel})")

    def register_agent(self, agent_id: str, agent: IntelligentAgent):
        """Register an agent"""
        self.agents[agent_id] = agent
        logger.info(f"Registered agent: {agent_id}")

    def add_stage(self, stage: WorkflowStage):
        """Add a stage to the workflow"""
        self.stages.append(stage)
        logger.info(f"Added stage: {stage.id} (agent: {stage.agent})")

    def execute(self, on_approval_needed: Optional[Callable] = None) -> Dict:
        """
        Execute the entire workflow.

        Args:
            on_approval_needed: Callback when approval is needed
                               Should return True (approve) or False (deny)

        Returns:
            {
                'success': True/False,
                'completed_stages': [...],
                'failed_stages': [...],
                'results': {...}
            }
        """
        logger.info("="*70)
        logger.info(f"Starting workflow with {len(self.stages)} stages")
        logger.info("="*70)

        results = {}

        while self.current_stage_idx < len(self.stages):
            # Find stages that can run now
            ready_stages = self._get_ready_stages()

            if not ready_stages:
                # No stages ready - check if we're blocked
                pending = [s for s in self.stages if s.status == StageStatus.PENDING]
                if pending:
                    logger.error("Workflow blocked - no stages can run")
                    break
                else:
                    # All done
                    break

            # Check for parallel execution
            parallel_groups = self._group_parallel_stages(ready_stages)

            for group_name, group_stages in parallel_groups.items():
                if len(group_stages) > 1:
                    # Execute in parallel
                    logger.info(f"\n🔀 Executing {len(group_stages)} stages in parallel: {group_name}")
                    group_results = self._execute_parallel(group_stages, on_approval_needed)
                    results.update(group_results)
                else:
                    # Execute single stage
                    stage = group_stages[0]
                    result = self._execute_stage(stage, on_approval_needed)
                    if result:
                        results[stage.id] = result

            self.current_stage_idx += 1

        # Summary
        logger.info("\n" + "="*70)
        logger.info("WORKFLOW COMPLETE")
        logger.info("="*70)
        logger.info(f"Completed: {len(self.completed_stages)}")
        logger.info(f"Failed: {len(self.failed_stages)}")

        return {
            'success': len(self.failed_stages) == 0,
            'completed_stages': self.completed_stages,
            'failed_stages': self.failed_stages,
            'results': results
        }

    def _get_ready_stages(self) -> List[WorkflowStage]:
        """Get stages that are ready to run"""
        ready = []

        for stage in self.stages:
            if stage.status != StageStatus.PENDING:
                continue

            # Check dependencies
            if stage.wait_for:
                deps_met = all(dep in self.completed_stages for dep in stage.wait_for)
                if not deps_met:
                    continue

            # Check condition
            if stage.condition and not stage.condition(self.project_root):
                stage.status = StageStatus.SKIPPED
                logger.info(f"⏭️  Skipped {stage.id}: condition not met")
                continue

            ready.append(stage)

        return ready

    def _group_parallel_stages(self, stages: List[WorkflowStage]) -> Dict[str, List[WorkflowStage]]:
        """Group stages by parallel execution capability"""
        groups = {}

        for stage in stages:
            if stage.can_run_parallel and stage.parallel_group:
                group_name = stage.parallel_group
            else:
                group_name = f"sequential_{stage.id}"

            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(stage)

        return groups

    def _execute_parallel(
        self,
        stages: List[WorkflowStage],
        on_approval_needed: Optional[Callable]
    ) -> Dict:
        """Execute multiple stages in parallel"""
        results = {}

        with ThreadPoolExecutor(max_workers=min(len(stages), self.max_parallel)) as executor:
            # Submit all stages
            future_to_stage = {
                executor.submit(self._execute_stage, stage, on_approval_needed): stage
                for stage in stages
            }

            # Collect results
            for future in as_completed(future_to_stage):
                stage = future_to_stage[future]
                try:
                    result = future.result()
                    if result:
                        results[stage.id] = result
                except Exception as e:
                    logger.error(f"Parallel execution error for {stage.id}: {e}")
                    stage.status = StageStatus.FAILED
                    stage.error = str(e)
                    self.failed_stages.append(stage.id)

        return results

    def _execute_stage(
        self,
        stage: WorkflowStage,
        on_approval_needed: Optional[Callable]
    ) -> Optional[Dict]:
        """Execute a single stage"""
        logger.info(f"\n{'='*70}")
        logger.info(f"Stage: {stage.id} (agent: {stage.agent})")
        logger.info(f"{'='*70}")

        stage.status = StageStatus.RUNNING
        stage.started_at = datetime.utcnow().isoformat()

        # Check for approval requirement
        if stage.requires_approval:
            stage.status = StageStatus.WAITING_APPROVAL

            message = stage.approval_message or f"Approve execution of {stage.id}?"
            logger.info(f"🔐 Approval required: {message}")

            if on_approval_needed:
                approved = on_approval_needed(stage, message)
                if not approved:
                    logger.warning(f"❌ Stage {stage.id} not approved - skipping")
                    stage.status = StageStatus.SKIPPED
                    return None
            else:
                # No approval handler - auto approve
                logger.warning("No approval handler - auto approving")

            stage.status = StageStatus.RUNNING

        # Get agent
        agent = self.agents.get(stage.agent)
        if not agent:
            error = f"Agent {stage.agent} not found"
            logger.error(error)
            stage.status = StageStatus.FAILED
            stage.error = error
            self.failed_stages.append(stage.id)
            return None

        # Execute with retry
        for attempt in range(stage.max_retries + 1):
            if attempt > 0:
                logger.info(f"🔄 Retry attempt {attempt}/{stage.max_retries}")

            try:
                result = agent.execute_task(stage.task)

                if result.get('success'):
                    stage.status = StageStatus.COMPLETED
                    stage.completed_at = datetime.utcnow().isoformat()
                    stage.result = result
                    self.completed_stages.append(stage.id)

                    logger.info(f"✅ {stage.id} completed")
                    return result

                else:
                    # Task failed
                    error = result.get('error', 'Unknown error')

                    if result.get('needs_input'):
                        logger.warning(f"⏸️  {stage.id} needs user input")
                        # Could handle this with callback
                        stage.status = StageStatus.FAILED
                        stage.error = "Needs user input"
                        self.failed_stages.append(stage.id)
                        return None

                    # Handle error based on strategy
                    if stage.on_error == 'retry' and attempt < stage.max_retries:
                        logger.warning(f"⚠️  {stage.id} failed: {error} - retrying...")
                        continue
                    elif stage.on_error == 'skip':
                        logger.warning(f"⏭️  {stage.id} failed: {error} - skipping")
                        stage.status = StageStatus.SKIPPED
                        return None
                    else:
                        # Stop workflow
                        stage.status = StageStatus.FAILED
                        stage.error = error
                        self.failed_stages.append(stage.id)
                        logger.error(f"❌ {stage.id} failed: {error}")
                        return None

            except Exception as e:
                logger.error(f"Exception in {stage.id}: {e}")
                if attempt < stage.max_retries:
                    continue
                else:
                    stage.status = StageStatus.FAILED
                    stage.error = str(e)
                    self.failed_stages.append(stage.id)
                    return None

        return None


# Helper functions for creating stages

def create_stage(
    id: str,
    agent: str,
    task: Dict,
    **kwargs
) -> WorkflowStage:
    """Helper to create a workflow stage"""
    return WorkflowStage(
        id=id,
        agent=agent,
        task=task,
        **kwargs
    )


def create_parallel_stages(
    group_name: str,
    stages_config: List[Dict]
) -> List[WorkflowStage]:
    """Create multiple stages that can run in parallel"""
    stages = []

    for config in stages_config:
        stage = create_stage(
            id=config['id'],
            agent=config['agent'],
            task=config['task'],
            can_run_parallel=True,
            parallel_group=group_name,
            **config.get('options', {})
        )
        stages.append(stage)

    return stages


# Example workflows

def create_simple_workflow() -> List[WorkflowStage]:
    """PM → Tech Lead workflow"""
    return [
        create_stage(
            id='pm_analysis',
            agent='pm',
            task={
                'type': 'analyze_requirements',
                'inputs': ['REQUEST.md'],
                'expected_outputs': ['SPEC.md']
            }
        ),
        create_stage(
            id='tech_design',
            agent='tech_lead',
            task={
                'type': 'design_architecture',
                'inputs': ['SPEC.md'],
                'expected_outputs': ['ARCHITECTURE.md']
            },
            wait_for=['pm_analysis'],
            requires_approval=True,
            approval_message="Approve architecture design stage?"
        )
    ]


def create_parallel_workflow() -> List[WorkflowStage]:
    """Workflow with parallel execution"""
    stages = []

    # Stage 1: PM (sequential)
    stages.append(create_stage(
        id='pm_analysis',
        agent='pm',
        task={
            'type': 'analyze_requirements',
            'inputs': ['REQUEST.md'],
            'expected_outputs': ['SPEC.md', 'TASKS.md']
        }
    ))

    # Stage 2: Tech Lead (sequential)
    stages.append(create_stage(
        id='tech_design',
        agent='tech_lead',
        task={
            'type': 'design_architecture',
            'inputs': ['SPEC.md'],
            'expected_outputs': ['ARCHITECTURE.md']
        },
        wait_for=['pm_analysis']
    ))

    # Stage 3: Parallel development
    parallel_stages = create_parallel_stages(
        group_name='development',
        stages_config=[
            {
                'id': 'frontend_dev',
                'agent': 'frontend_dev',
                'task': {
                    'type': 'implement_frontend',
                    'inputs': ['ARCHITECTURE.md', 'TASKS.md'],
                    'expected_outputs': ['src/frontend/']
                },
                'options': {'wait_for': ['tech_design']}
            },
            {
                'id': 'backend_dev',
                'agent': 'backend_dev',
                'task': {
                    'type': 'implement_backend',
                    'inputs': ['ARCHITECTURE.md', 'TASKS.md'],
                    'expected_outputs': ['src/backend/']
                },
                'options': {'wait_for': ['tech_design']}
            }
        ]
    )
    stages.extend(parallel_stages)

    # Stage 4: QA (wait for both frontend and backend)
    stages.append(create_stage(
        id='qa_testing',
        agent='qa_tester',
        task={
            'type': 'test_application',
            'inputs': ['src/'],
            'expected_outputs': ['TEST_REPORT.md']
        },
        wait_for=['frontend_dev', 'backend_dev']
    ))

    return stages
