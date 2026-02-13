#!/usr/bin/env python3
"""
Fix hardcoded paths to use portable witmind-data directory
Makes the codebase portable for others to use
"""

import os
import re
from pathlib import Path

def fix_file(filepath: Path, replacements: list):
    """Apply replacements to a file"""
    if not filepath.exists():
        print(f"  [!] Skipping {filepath} (not found)")
        return False

    content = filepath.read_text(encoding='utf-8')
    original = content

    for old, new in replacements:
        content = content.replace(old, new)

    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print(f"  [+] Fixed {filepath}")
        return True
    else:
        print(f"  [-] No changes needed in {filepath}")
        return False

def main():
    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)

    print("[*] Fixing hardcoded paths in witmind codebase...\n")

    fixes = [
        # orchestrator.py
        (
            repo_root / "platform/core/orchestrator.py",
            [
                (
                    "Path(os.environ.get('WITMIND_ROOT', '/home/wit/6amdev'))",
                    "Path(os.environ.get('WITMIND_ROOT', str(Path.home() / 'witmind-data')))"
                )
            ]
        ),
        # execution_engine.py
        (
            repo_root / "platform/core/execution_engine.py",
            [
                (
                    "os.environ.get('WITMIND_ROOT', '/home/wit/6amdev')",
                    "os.environ.get('WITMIND_ROOT', str(Path.home() / 'witmind-data'))"
                )
            ]
        ),
        # task_queue.py
        (
            repo_root / "platform/core/task_queue.py",
            [
                (
                    "os.environ.get('WITMIND_ROOT', '/home/wit/6amdev') + '/logs/queue'",
                    "os.path.join(os.environ.get('WITMIND_ROOT', str(Path.home() / 'witmind-data')), 'logs/queue')"
                )
            ]
        ),
        # approval_gate.py
        (
            repo_root / "platform/core/approval_gate.py",
            [
                (
                    "os.environ.get('WITMIND_ROOT', '/home/wit/6amdev')",
                    "os.environ.get('WITMIND_ROOT', str(Path.home() / 'witmind-data'))"
                )
            ]
        ),
        # projects.py
        (
            repo_root / "mission-control/backend/app/routes/projects.py",
            [
                (
                    'PLATFORM_PROJECTS_DIR = os.getenv("PLATFORM_PROJECTS_DIR", "/home/wit/6amdev/platform/projects/active")',
                    'PLATFORM_PROJECTS_DIR = os.getenv("PLATFORM_PROJECTS_DIR", str(Path.home() / "witmind-data" / "projects" / "active"))'
                )
            ]
        ),
        # config.py
        (
            repo_root / "platform/core/config.py",
            [
                (
                    'default_factory=lambda: Path(os.getenv("LOG_PATH", "/var/log/6amdev"))',
                    'default_factory=lambda: Path(os.getenv("LOG_PATH", str(Path.home() / "witmind-data" / "logs")))'
                )
            ]
        ),
    ]

    fixed_count = 0
    for filepath, replacements in fixes:
        if fix_file(filepath, replacements):
            fixed_count += 1

    print(f"\n[+] Fixed {fixed_count} files!")
    print("\n[*] Next steps:")
    print("  1. Copy .env.example to ~/.env")
    print("  2. Set WITMIND_ROOT in ~/.env if you want custom location")
    print("  3. Run: mkdir -p ~/witmind-data/{projects/active,logs/queue,cache}")
    print("  4. For server: export WITMIND_ROOT=/home/wit/witmind-data")

if __name__ == '__main__':
    main()
