#!/usr/bin/env python3
"""
Test Workflow Engine - Advanced orchestration

Demonstrates:
1. Sequential workflow
2. Parallel execution
3. Approval gates
4. Error handling
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'platform'))

from core.intelligent_agent import create_intelligent_agent
from core.llm_client import create_llm_client
from core.workflow_engine import (
    WorkflowEngine,
    create_simple_workflow,
    create_parallel_workflow,
    create_stage
)

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger('test')


def approval_handler(stage, message):
    """
    Simple approval handler - auto-approves everything.
    In real usage, this would ask the user.
    """
    logger.info(f"🔐 APPROVAL REQUEST: {message}")
    logger.info(f"   Stage: {stage.id}")
    logger.info(f"   Agent: {stage.agent}")
    logger.info(f"   Auto-approving for test...")
    return True  # Auto-approve


def test_simple_workflow():
    """Test simple sequential workflow with approval"""
    logger.info("="*70)
    logger.info("Test: Simple Workflow (PM → Tech Lead)")
    logger.info("="*70)

    # Setup
    test_dir = Path(__file__).parent / 'test_projects' / 'workflow_test'
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create request
    (test_dir / 'REQUEST.md').write_text("""
# Calculator App

Build a simple calculator web app.

Features:
- Basic operations (+, -, *, /)
- Clear button
- History of calculations

Tech: React + TailwindCSS
""")

    # Create LLM & agents
    llm = create_llm_client('openrouter', model='anthropic/claude-3.5-sonnet')

    platform_root = Path(__file__).parent.parent / 'platform'

    pm_agent = create_intelligent_agent(
        'pm', 'dev',
        platform_root / 'teams' / 'dev' / 'agents' / 'pm.yaml',
        llm, test_dir
    )

    tech_lead_agent = create_intelligent_agent(
        'tech_lead', 'dev',
        platform_root / 'teams' / 'dev' / 'agents' / 'tech_lead.yaml',
        llm, test_dir
    )

    # Create workflow engine
    engine = WorkflowEngine(test_dir)
    engine.register_agent('pm', pm_agent)
    engine.register_agent('tech_lead', tech_lead_agent)

    # Add stages
    for stage in create_simple_workflow():
        engine.add_stage(stage)

    # Execute
    logger.info("\nStarting workflow execution...")
    result = engine.execute(on_approval_needed=approval_handler)

    # Results
    logger.info("\n" + "="*70)
    logger.info("RESULTS")
    logger.info("="*70)
    logger.info(f"Success: {result['success']}")
    logger.info(f"Completed: {result['completed_stages']}")
    logger.info(f"Failed: {result['failed_stages']}")

    # Show files
    logger.info("\n📄 Created files:")
    for f in test_dir.glob('*.md'):
        if f.name != 'REQUEST.md':
            logger.info(f"  - {f.name}")

    return result


def test_parallel_workflow():
    """Test workflow with parallel execution"""
    logger.info("\n" + "="*70)
    logger.info("Test: Parallel Workflow (Frontend + Backend in parallel)")
    logger.info("="*70)

    test_dir = Path(__file__).parent / 'test_projects' / 'parallel_test'
    test_dir.mkdir(parents=True, exist_ok=True)

    logger.info("⚠️  Note: This test needs frontend_dev and backend_dev agents")
    logger.info("    Skipping for now (not all agents implemented)")

    return {'success': True, 'skipped': True}


def test_approval_gate():
    """Test approval gate functionality"""
    logger.info("\n" + "="*70)
    logger.info("Test: Approval Gate")
    logger.info("="*70)

    test_dir = Path(__file__).parent / 'test_projects' / 'approval_test'
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create engine
    engine = WorkflowEngine(test_dir)

    # Add stage that requires approval
    stage = create_stage(
        id='test_stage',
        agent='pm',
        task={'type': 'test', 'expected_outputs': []},
        requires_approval=True,
        approval_message="Do you want to proceed with test stage?"
    )
    engine.add_stage(stage)

    # Test with auto-approve
    logger.info("Testing with auto-approve...")
    result = {'approved': approval_handler(stage, stage.approval_message)}

    logger.info(f"Result: {result}")
    return result


def test_error_handling():
    """Test error handling strategies"""
    logger.info("\n" + "="*70)
    logger.info("Test: Error Handling")
    logger.info("="*70)

    logger.info("Error handling strategies:")
    logger.info("  - stop: Stop workflow on error (default)")
    logger.info("  - skip: Skip failed stage and continue")
    logger.info("  - retry: Retry failed stage N times")

    # Example
    stage_with_retry = create_stage(
        id='risky_stage',
        agent='pm',
        task={'type': 'risky_task'},
        on_error='retry',
        max_retries=3
    )

    logger.info(f"\nExample stage: {stage_with_retry.id}")
    logger.info(f"  on_error: {stage_with_retry.on_error}")
    logger.info(f"  max_retries: {stage_with_retry.max_retries}")

    return {'success': True}


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--test',
        choices=['simple', 'parallel', 'approval', 'error', 'all'],
        default='simple',
        help='Which test to run'
    )

    args = parser.parse_args()

    try:
        if args.test == 'simple':
            test_simple_workflow()
        elif args.test == 'parallel':
            test_parallel_workflow()
        elif args.test == 'approval':
            test_approval_gate()
        elif args.test == 'error':
            test_error_handling()
        elif args.test == 'all':
            test_simple_workflow()
            test_parallel_workflow()
            test_approval_gate()
            test_error_handling()

        logger.info("\n✅ Tests completed!")

    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        sys.exit(1)
