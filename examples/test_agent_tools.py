#!/usr/bin/env python3
"""
Test Agent Tools - Real capabilities for agents

Demonstrates all tools:
- Read/Write/Edit files
- Bash commands
- Glob/Grep (search)
- Git operations
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'platform'))

from core.agent_tools import create_tool_registry

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger('test')


def test_file_operations():
    """Test Read/Write/Edit tools"""
    logger.info("="*70)
    logger.info("Test: File Operations")
    logger.info("="*70)

    test_dir = Path(__file__).parent / 'test_projects' / 'tools_test'
    test_dir.mkdir(parents=True, exist_ok=True)

    registry = create_tool_registry(test_dir)

    # 1. Write file
    logger.info("\n1. Testing write_file...")
    result = registry.execute_tool(
        'write_file',
        path='hello.txt',
        content='Hello, World!\nThis is a test file.'
    )
    logger.info(f"   Result: {result}")

    # 2. Read file
    logger.info("\n2. Testing read_file...")
    result = registry.execute_tool('read_file', path='hello.txt')
    logger.info(f"   Success: {result['success']}")
    logger.info(f"   Content: {result.get('content', '')[:50]}...")

    # 3. Edit file
    logger.info("\n3. Testing edit_file...")
    result = registry.execute_tool(
        'edit_file',
        path='hello.txt',
        old_text='World',
        new_text='Agent Tools'
    )
    logger.info(f"   Result: {result}")

    # 4. Read again to verify
    result = registry.execute_tool('read_file', path='hello.txt')
    logger.info(f"   New content: {result.get('content', '')}")

    return True


def test_search_tools():
    """Test Glob and Grep"""
    logger.info("\n" + "="*70)
    logger.info("Test: Search Tools (Glob & Grep)")
    logger.info("="*70)

    test_dir = Path(__file__).parent / 'test_projects' / 'tools_test'
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create some test files
    (test_dir / 'file1.py').write_text('def hello():\n    print("Hello")')
    (test_dir / 'file2.py').write_text('def world():\n    print("World")')
    (test_dir / 'README.md').write_text('# Test Project\nThis is a test.')

    registry = create_tool_registry(test_dir)

    # 1. Glob - find Python files
    logger.info("\n1. Testing glob (find *.py)...")
    result = registry.execute_tool('glob', pattern='*.py')
    logger.info(f"   Found {result['count']} files:")
    for f in result['matches']:
        logger.info(f"     - {f}")

    # 2. Glob - find all files
    logger.info("\n2. Testing glob (find all files)...")
    result = registry.execute_tool('glob', pattern='*')
    logger.info(f"   Found {result['count']} files")

    # 3. Grep - search for text
    logger.info("\n3. Testing grep (search for 'print')...")
    result = registry.execute_tool('grep', pattern='print')
    logger.info(f"   Found {result['total']} matches:")
    for match in result['matches'][:5]:
        logger.info(f"     {match['file']}:{match['line']} - {match['text'][:50]}")

    return True


def test_bash_tool():
    """Test Bash command execution"""
    logger.info("\n" + "="*70)
    logger.info("Test: Bash Tool")
    logger.info("="*70)

    test_dir = Path(__file__).parent / 'test_projects' / 'tools_test'
    test_dir.mkdir(parents=True, exist_ok=True)

    registry = create_tool_registry(test_dir)

    # 1. List files
    logger.info("\n1. Testing bash: ls...")
    result = registry.execute_tool('bash', command='ls -la')
    logger.info(f"   Success: {result['success']}")
    logger.info(f"   Output:\n{result.get('stdout', '')[:200]}")

    # 2. Echo
    logger.info("\n2. Testing bash: echo...")
    result = registry.execute_tool('bash', command='echo "Hello from bash!"')
    logger.info(f"   Output: {result.get('stdout', '').strip()}")

    # 3. Blocked command (for safety)
    logger.info("\n3. Testing bash: blocked command (rm)...")
    result = registry.execute_tool('bash', command='rm -rf /')
    logger.info(f"   Blocked: {not result['success']}")
    logger.info(f"   Error: {result.get('error', 'N/A')}")

    return True


def test_git_tool():
    """Test Git operations"""
    logger.info("\n" + "="*70)
    logger.info("Test: Git Tool")
    logger.info("="*70)

    test_dir = Path(__file__).parent / 'test_projects' / 'git_test'
    test_dir.mkdir(parents=True, exist_ok=True)

    # Initialize git repo
    import subprocess
    subprocess.run(['git', 'init'], cwd=test_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=test_dir)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=test_dir)

    registry = create_tool_registry(test_dir)

    # 1. Create a file
    (test_dir / 'test.txt').write_text('Test content')

    # 2. Git status
    logger.info("\n1. Testing git status...")
    result = registry.execute_tool('git', operation='status')
    logger.info(f"   Success: {result['success']}")
    logger.info(f"   Output:\n{result.get('output', '')[:200]}")

    # 3. Git add
    logger.info("\n2. Testing git add...")
    result = registry.execute_tool('git', operation='add', files=['test.txt'])
    logger.info(f"   Success: {result['success']}")

    # 4. Git commit
    logger.info("\n3. Testing git commit...")
    result = registry.execute_tool('git', operation='commit', message='Test commit')
    logger.info(f"   Success: {result['success']}")
    logger.info(f"   Output: {result.get('output', '')[:100]}")

    return True


def test_all_tools():
    """Run all tool tests"""
    logger.info("="*70)
    logger.info("AGENT TOOLS TEST SUITE")
    logger.info("="*70)

    results = {
        'file_operations': test_file_operations(),
        'search_tools': test_search_tools(),
        'bash_tool': test_bash_tool(),
        'git_tool': test_git_tool()
    }

    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}")

    all_passed = all(results.values())
    logger.info(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    return all_passed


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--test',
        choices=['file', 'search', 'bash', 'git', 'all'],
        default='all',
        help='Which test to run'
    )

    args = parser.parse_args()

    try:
        if args.test == 'file':
            test_file_operations()
        elif args.test == 'search':
            test_search_tools()
        elif args.test == 'bash':
            test_bash_tool()
        elif args.test == 'git':
            test_git_tool()
        else:
            test_all_tools()

        logger.info("\n✅ Tests completed!")

    except Exception as e:
        logger.error(f"\n❌ Tests failed: {e}", exc_info=True)
        sys.exit(1)
