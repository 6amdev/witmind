#!/usr/bin/env python3
"""
Test Agent Communication - PM → Tech Lead

This demonstrates:
1. PM Agent analyzes request → creates SPEC.md
2. Tech Lead Agent reads SPEC.md → creates ARCHITECTURE.md
3. Agents communicate via files (not talking directly)
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'platform'))

from core.intelligent_agent import create_intelligent_agent
from core.llm_client import create_llm_client
from core.agent_coordinator import AgentCoordinator, SIMPLE_WORKFLOW

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger('test')


def test_pm_to_tech_lead():
    """
    Test PM → Tech Lead workflow.

    Flow:
    1. User creates REQUEST.md
    2. PM Agent reads REQUEST.md → creates SPEC.md
    3. Coordinator hands off to Tech Lead
    4. Tech Lead reads SPEC.md → creates ARCHITECTURE.md
    """
    logger.info("="*70)
    logger.info("Testing Agent Communication: PM → Tech Lead")
    logger.info("="*70)

    # 1. Setup project directory
    test_dir = Path(__file__).parent / 'test_projects' / 'agent_comm_test'
    test_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Project dir: {test_dir}")

    # 2. Create user request
    request_content = """# Todo App Request

## What I want
A simple todo list web application.

## Features needed
- Add new todos
- Mark todos as complete/incomplete
- Delete todos
- Filter by status (all/active/completed)
- Search todos by text

## Tech preferences
- Use React for frontend
- Keep it simple and clean
- Mobile responsive

## Timeline
Need it done in 2 weeks.

## Notes
- No user authentication needed
- Data can be stored in browser (localStorage)
- Focus on user experience
"""

    (test_dir / 'REQUEST.md').write_text(request_content)
    logger.info("✅ REQUEST.md created")

    # 3. Create LLM client
    llm = create_llm_client('openrouter', model='anthropic/claude-3.5-sonnet')
    logger.info("🤖 LLM client ready (OpenRouter + Claude)")

    # 4. Load agent configs
    platform_root = Path(__file__).parent.parent / 'platform'
    pm_config = platform_root / 'teams' / 'dev' / 'agents' / 'pm.yaml'
    tech_lead_config = platform_root / 'teams' / 'dev' / 'agents' / 'tech_lead.yaml'

    # 5. Create agents
    pm_agent = create_intelligent_agent(
        agent_id='pm',
        team_id='dev',
        config_path=pm_config,
        llm_client=llm,
        project_root=test_dir
    )
    logger.info("✅ PM Agent created")

    tech_lead_agent = create_intelligent_agent(
        agent_id='tech_lead',
        team_id='dev',
        config_path=tech_lead_config,
        llm_client=llm,
        project_root=test_dir
    )
    logger.info("✅ Tech Lead Agent created")

    # 6. Create coordinator
    coordinator = AgentCoordinator(test_dir)
    coordinator.register_agent('pm', pm_agent)
    coordinator.register_agent('tech_lead', tech_lead_agent)
    logger.info("✅ Coordinator ready")

    # 7. Execute workflow
    logger.info("\n" + "="*70)
    logger.info("EXECUTING WORKFLOW: PM → Tech Lead")
    logger.info("="*70)

    result = coordinator.execute_workflow(SIMPLE_WORKFLOW)

    # 8. Show results
    logger.info("\n" + "="*70)
    logger.info("WORKFLOW RESULTS")
    logger.info("="*70)

    if result['success']:
        logger.info("✅ SUCCESS!")
        logger.info(f"Completed agents: {', '.join(result['completed_agents'])}")

        logger.info("\n📦 Deliverables by agent:")
        for agent_id, deliverables in result['deliverables'].items():
            logger.info(f"  {agent_id}: {', '.join(deliverables)}")

        logger.info("\n🔄 Handoffs:")
        for handoff in result['handoffs']:
            logger.info(f"  {handoff['from']} → {handoff['to']}")
            logger.info(f"     Files: {', '.join(handoff['files'])}")

        # Show created files
        logger.info("\n📄 Files created:")
        for file_path in sorted(test_dir.iterdir()):
            if file_path.is_file() and file_path.suffix == '.md':
                logger.info(f"\n  {file_path.name}:")
                logger.info("  " + "-"*60)
                content = file_path.read_text()
                # Show first 500 chars
                preview = content[:500]
                if len(content) > 500:
                    preview += "\n  ... (truncated)"
                logger.info("  " + preview.replace("\n", "\n  "))

    else:
        logger.error("❌ FAILED")
        if result.get('needs_input'):
            logger.info(f"🤔 Agent needs input: {result['question']}")
            logger.info(f"   From agent: {result['agent']}")
        else:
            logger.error(f"Error: {result.get('error')}")

    return result


def test_simple_handoff():
    """
    Simple test - just verify handoff mechanism works.
    """
    logger.info("\n" + "="*70)
    logger.info("Testing Simple Handoff Mechanism")
    logger.info("="*70)

    test_dir = Path(__file__).parent / 'test_projects' / 'handoff_test'
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create a fake file
    (test_dir / 'SPEC.md').write_text("# Spec\nSome specification content")

    coordinator = AgentCoordinator(test_dir)

    # Simulate handoff
    from core.agent_coordinator import AgentHandoff
    handoff = AgentHandoff(
        from_agent='pm',
        to_agent='tech_lead',
        trigger='completion',
        files_to_pass=['SPEC.md']
    )
    coordinator.handoffs.append(handoff)

    # Verify
    result = coordinator.verify_handoff('pm', 'tech_lead')
    logger.info(f"Handoff verification: {'✅ PASS' if result else '❌ FAIL'}")

    return result


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--mode',
        choices=['simple', 'full'],
        default='full',
        help='Test mode'
    )

    args = parser.parse_args()

    try:
        if args.mode == 'simple':
            test_simple_handoff()
        else:
            test_pm_to_tech_lead()

        logger.info("\n✅ Test completed!")

    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        sys.exit(1)
