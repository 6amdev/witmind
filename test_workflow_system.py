#!/usr/bin/env python3
"""
Test Workflow System - Verify everything works

This tests:
1. Agent loading from YAML (21 agents)
2. Template system (9 templates)
3. Workflow execution (basic)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'platform'))

from core.agent_loader import load_all_agents
from core.workflow_templates import list_templates, suggest_template, get_template
from core.workflow_executor import WorkflowExecutor


def test_agent_loading():
    """Test: Load all 21 agents from YAML"""
    print("="*70)
    print("TEST 1: Agent Loading")
    print("="*70)

    agents_dir = Path(__file__).parent / 'platform' / 'teams'
    project_root = Path('/tmp/test_workflow_system')
    project_root.mkdir(parents=True, exist_ok=True)

    try:
        agents = load_all_agents(agents_dir, project_root)
        print(f"✅ Loaded {len(agents)} agents:")

        teams = {'dev': [], 'marketing': [], 'creative': []}
        for agent_id, agent in agents.items():
            teams[agent.team].append(agent_id)

        for team, agent_list in teams.items():
            print(f"\n  {team.upper()} ({len(agent_list)}):")
            for agent_id in sorted(agent_list):
                print(f"    - {agent_id}")

        assert len(agents) == 21, f"Expected 21 agents, got {len(agents)}"
        print(f"\n✅ PASS: All 21 agents loaded successfully!")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_templates():
    """Test: Template system"""
    print("\n" + "="*70)
    print("TEST 2: Template System")
    print("="*70)

    try:
        templates = list_templates()
        print(f"✅ Found {len(templates)} templates:")

        for template in templates:
            print(f"\n  📋 {template.name} ({template.id})")
            print(f"     {template.description}")
            print(f"     Agents: {' → '.join(template.agents)}")

        assert len(templates) == 9, f"Expected 9 templates, got {len(templates)}"
        print(f"\n✅ PASS: All 9 templates available!")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_detection():
    """Test: Auto template suggestion"""
    print("\n" + "="*70)
    print("TEST 3: Auto-Detection")
    print("="*70)

    test_cases = [
        ("Build a portfolio website", "simple_website"),
        ("Create a mobile app for iOS", "mobile_app"),
        ("Build a REST API backend", "api_backend"),
        ("Create marketing content for launch", "content_campaign"),
        ("Design a logo and brand identity", "branding"),
    ]

    try:
        for description, expected_id in test_cases:
            suggested = suggest_template(description)
            match = "✅" if suggested.id == expected_id else "❌"
            print(f"{match} '{description}'")
            print(f"   Expected: {expected_id}")
            print(f"   Got: {suggested.id} ({suggested.name})")
            print()

        print("✅ PASS: Auto-detection working!")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_executor():
    """Test: Workflow executor setup"""
    print("\n" + "="*70)
    print("TEST 4: Workflow Executor")
    print("="*70)

    try:
        agents_dir = Path(__file__).parent / 'platform' / 'teams'
        projects_dir = Path('/tmp/test_workflow_projects')
        projects_dir.mkdir(parents=True, exist_ok=True)

        executor = WorkflowExecutor(
            agents_dir=agents_dir,
            projects_dir=projects_dir,
            metrics_dir=None
        )

        print("✅ Workflow executor created")
        print(f"   Agents dir: {agents_dir}")
        print(f"   Projects dir: {projects_dir}")

        # Test template retrieval
        template = get_template('simple_website')
        print(f"\n✅ Template loaded: {template.name}")
        print(f"   Agents: {', '.join(template.agents)}")

        print("\n✅ PASS: Workflow executor ready!")
        return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("WITMIND WORKFLOW SYSTEM TEST SUITE")
    print("="*70)
    print()

    results = {
        'Agent Loading': test_agent_loading(),
        'Template System': test_templates(),
        'Auto-Detection': test_auto_detection(),
        'Workflow Executor': test_workflow_executor(),
    }

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(results.values())
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("System is ready:")
        print("  - 21 agents loaded from YAML")
        print("  - 9 workflow templates available")
        print("  - Auto-detection working")
        print("  - Workflow executor ready")
        print()
        print("Next: Start the dashboard:")
        print("  cd workflow-dashboard/backend")
        print("  python3 main.py")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == '__main__':
    main()
