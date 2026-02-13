#!/usr/bin/env python3
"""
Test Intelligent Agent - Demo with PM Agent

This demonstrates:
1. How IntelligentAgent works with agentic loop
2. How agent thinks, acts, and evaluates
3. How agent creates deliverables (SPEC.md)
"""

import sys
import logging
from pathlib import Path

# Add platform to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'platform'))

from core.intelligent_agent import create_intelligent_agent
from core.llm_client import create_llm_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger('test')


def test_pm_agent():
    """
    Test PM agent analyzing a project request.

    Input: Simple project description
    Expected Output: SPEC.md file with requirements
    """
    logger.info("=" * 60)
    logger.info("Testing Intelligent Agent - PM Agent")
    logger.info("=" * 60)

    # 1. Create test project directory
    test_dir = Path(__file__).parent / 'test_projects' / 'todo_app'
    test_dir.mkdir(parents=True, exist_ok=True)

    # 2. Create input request
    request_content = """
# Project Request

## Title
Todo App with React

## Description
I need a simple todo list application with the following features:
- Create new todos
- Mark todos as completed
- Delete todos
- Filter todos (all/active/completed)
- Search todos by text

## Tech Preferences
- Frontend: React
- Should be mobile responsive
- Simple and clean UI

## Timeline
Need it in 2 weeks
"""

    (test_dir / 'REQUEST.md').write_text(request_content)
    logger.info(f"Created test request: {test_dir / 'REQUEST.md'}")

    # 3. Create LLM client
    llm = create_llm_client(provider='claude')
    logger.info("LLM client created (Claude Sonnet)")

    # 4. Load PM agent config
    platform_root = Path(__file__).parent.parent / 'platform'
    pm_config = platform_root / 'teams' / 'dev' / 'agents' / 'pm.yaml'

    # 5. Create intelligent agent
    agent = create_intelligent_agent(
        agent_id='pm',
        team_id='dev',
        config_path=pm_config,
        llm_client=llm,
        project_root=test_dir
    )
    logger.info("PM Agent initialized")

    # 6. Define task
    task = {
        'type': 'analyze_requirements',
        'description': 'Analyze project request and create specification',
        'inputs': ['REQUEST.md'],
        'expected_outputs': ['SPEC.md', 'TASKS.md']
    }

    # 7. Execute task
    logger.info("Starting agent execution...")
    logger.info("-" * 60)

    result = agent.execute_task(task)

    # 8. Display results
    logger.info("-" * 60)
    logger.info("EXECUTION COMPLETE")
    logger.info("=" * 60)

    if result['success']:
        logger.info("✅ Task completed successfully!")
        logger.info(f"Iterations: {result.get('iterations', 'N/A')}")
        logger.info(f"Deliverables: {', '.join(result['deliverables'])}")

        # Show created files
        for deliverable in result['deliverables']:
            file_path = test_dir / deliverable
            if file_path.exists():
                logger.info(f"\n📄 {deliverable}:")
                logger.info("-" * 40)
                content = file_path.read_text()
                # Show first 500 chars
                logger.info(content[:500] + "..." if len(content) > 500 else content)

    else:
        logger.error("❌ Task failed")
        if result.get('needs_input'):
            logger.info(f"🤔 Agent needs input: {result['question']}")
        elif result.get('error'):
            logger.error(f"Error: {result['error']}")

    # 9. Show memory
    logger.info("\n" + "=" * 60)
    logger.info("AGENT MEMORY")
    logger.info("=" * 60)

    memory = result.get('memory', {})
    logger.info(f"Actions taken: {len(memory.get('actions', []))}")
    logger.info(f"Thoughts: {len(memory.get('thoughts', []))}")

    # Show all thoughts
    for i, thought in enumerate(memory.get('thoughts', []), 1):
        logger.info(f"\n💭 Thought {i}:")
        content = thought.get('content', thought)
        logger.info(content[:300] + "..." if len(content) > 300 else content)

    return result


def test_simple_thinking():
    """
    Simpler test - just test the thinking process.
    """
    logger.info("\n" + "=" * 60)
    logger.info("Testing Agent Thinking Process")
    logger.info("=" * 60)

    # Create LLM client
    llm = create_llm_client(provider='claude')

    # Create a minimal agent config
    minimal_config = {
        'agent': {
            'id': 'test_agent',
            'name': 'Test Agent',
            'description': 'A test agent for demonstration'
        },
        'system_prompt': '''
You are a helpful AI assistant that analyzes project requests.
Your job is to think carefully and create clear specifications.
        ''',
        'limits': {
            'max_iterations': 3,
            'max_tokens': 4000
        }
    }

    # Create agent
    from core.intelligent_agent import IntelligentAgent
    test_dir = Path(__file__).parent / 'test_projects' / 'simple_test'
    test_dir.mkdir(parents=True, exist_ok=True)

    agent = IntelligentAgent(
        agent_id='test_agent',
        config=minimal_config,
        llm_client=llm,
        tools={},
        project_root=test_dir
    )

    # Test thinking
    context = {
        'task': {
            'description': 'Create a hello world app',
            'type': 'web_app'
        },
        'available_tools': ['read_file', 'write_file'],
        'iteration': 0
    }

    thought = agent._think(context, 0)

    logger.info("\n💭 Agent's Thought:")
    logger.info("-" * 60)
    logger.info(thought)

    return thought


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test Intelligent Agent')
    parser.add_argument(
        '--mode',
        choices=['simple', 'full'],
        default='simple',
        help='Test mode: simple (thinking only) or full (complete task)'
    )

    args = parser.parse_args()

    try:
        if args.mode == 'simple':
            test_simple_thinking()
        else:
            test_pm_agent()

        logger.info("\n✅ Test completed successfully!")

    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        sys.exit(1)
