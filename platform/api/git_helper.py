#!/usr/bin/env python3
"""
Git Helper - Handles Git operations for project workspaces
Integrates with Gitea for version control of agent work
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger('git_helper')


class GitHelper:
    """Helper class for Git operations in project workspaces"""

    def __init__(self, working_dir: Path, clone_url: Optional[str] = None):
        """
        Initialize GitHelper

        Args:
            working_dir: Project working directory
            clone_url: Git clone URL (with token embedded for auth)
        """
        self.working_dir = working_dir
        self.clone_url = clone_url

    async def _run_git(self, *args, cwd: Path = None) -> tuple[bool, str]:
        """Run a git command and return success status and output"""
        cwd = cwd or self.working_dir

        try:
            process = await asyncio.create_subprocess_exec(
                'git', *args,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60
            )

            output = stdout.decode() if stdout else ''
            error = stderr.decode() if stderr else ''

            if process.returncode == 0:
                return True, output
            else:
                logger.warning(f"Git command failed: git {' '.join(args)}")
                logger.warning(f"Error: {error}")
                return False, error

        except asyncio.TimeoutError:
            logger.error(f"Git command timed out: git {' '.join(args)}")
            return False, "Command timed out"
        except Exception as e:
            logger.error(f"Git command error: {e}")
            return False, str(e)

    async def init_or_clone(self) -> bool:
        """
        Initialize git repo or clone from remote.
        Returns True if successful.
        """
        git_dir = self.working_dir / '.git'

        if git_dir.exists():
            logger.info(f"Git repo already exists at {self.working_dir}")
            return True

        self.working_dir.mkdir(parents=True, exist_ok=True)

        if self.clone_url:
            # Clone from remote
            logger.info(f"Cloning repo to {self.working_dir}")
            # Clone to a temp directory first, then move contents
            success, output = await self._run_git(
                'clone', self.clone_url, '.',
                cwd=self.working_dir
            )
            if success:
                logger.info("Repository cloned successfully")
                return True
            else:
                # If clone fails (e.g., already has files), try init + add remote
                logger.warning(f"Clone failed, trying init instead: {output}")
                return await self._init_with_remote()
        else:
            # Just initialize
            success, _ = await self._run_git('init')
            if success:
                logger.info(f"Initialized git repo at {self.working_dir}")
            return success

    async def _init_with_remote(self) -> bool:
        """Initialize repo and add remote"""
        success, _ = await self._run_git('init')
        if not success:
            return False

        if self.clone_url:
            # Add remote
            await self._run_git('remote', 'add', 'origin', self.clone_url)

            # Try to fetch and set upstream
            await self._run_git('fetch', 'origin')

        return True

    async def configure_user(self, name: str = "6AMDev Agent", email: str = "agent@6amdev.ai"):
        """Configure git user for commits"""
        await self._run_git('config', 'user.name', name)
        await self._run_git('config', 'user.email', email)

    async def commit_changes(
        self,
        message: str,
        agent_id: str = None,
        task_id: str = None
    ) -> bool:
        """
        Stage all changes and commit.

        Args:
            message: Commit message
            agent_id: Optional agent ID for commit message
            task_id: Optional task ID for commit message

        Returns:
            True if commit was made, False otherwise
        """
        # Configure user
        await self.configure_user()

        # Check if there are changes
        success, status = await self._run_git('status', '--porcelain')
        if not success or not status.strip():
            logger.info("No changes to commit")
            return False

        # Stage all changes
        success, _ = await self._run_git('add', '-A')
        if not success:
            return False

        # Build commit message
        commit_lines = [message]
        if agent_id:
            commit_lines.append(f"Agent: {agent_id}")
        if task_id:
            commit_lines.append(f"Task: {task_id}")
        commit_lines.append(f"Timestamp: {datetime.utcnow().isoformat()}")

        full_message = '\n'.join(commit_lines)

        # Commit
        success, output = await self._run_git('commit', '-m', full_message)
        if success:
            logger.info(f"Committed changes: {message}")
            return True
        else:
            # Check if "nothing to commit" message
            if "nothing to commit" in output.lower():
                logger.info("Nothing to commit")
                return False
            logger.error(f"Commit failed: {output}")
            return False

    async def push(self, branch: str = "main") -> bool:
        """
        Push changes to remote.

        Args:
            branch: Branch to push

        Returns:
            True if push was successful
        """
        if not self.clone_url:
            logger.info("No remote URL configured, skipping push")
            return False

        # Push to origin
        success, output = await self._run_git('push', '-u', 'origin', branch)
        if success:
            logger.info(f"Pushed to origin/{branch}")
            return True
        else:
            # Try to set upstream and push
            logger.warning(f"Push failed, trying to set upstream: {output}")
            success, output = await self._run_git('push', '--set-upstream', 'origin', branch)
            if success:
                logger.info(f"Pushed to origin/{branch} (set upstream)")
                return True
            logger.error(f"Push failed: {output}")
            return False

    async def commit_and_push(
        self,
        message: str,
        agent_id: str = None,
        task_id: str = None,
        branch: str = "main"
    ) -> bool:
        """
        Commit all changes and push to remote.

        Args:
            message: Commit message
            agent_id: Optional agent ID
            task_id: Optional task ID
            branch: Branch to push

        Returns:
            True if commit and push were successful
        """
        committed = await self.commit_changes(message, agent_id, task_id)
        if committed:
            return await self.push(branch)
        return False

    async def get_status(self) -> dict:
        """Get current git status"""
        git_dir = self.working_dir / '.git'

        if not git_dir.exists():
            return {"initialized": False}

        result = {"initialized": True}

        # Get branch
        success, output = await self._run_git('branch', '--show-current')
        if success:
            result["branch"] = output.strip()

        # Get status
        success, output = await self._run_git('status', '--porcelain')
        if success:
            changes = [line for line in output.strip().split('\n') if line]
            result["changes_count"] = len(changes)
            result["has_changes"] = len(changes) > 0

        # Get remote
        success, output = await self._run_git('remote', '-v')
        if success and output.strip():
            result["has_remote"] = True

        return result


async def setup_project_git(
    project_dir: Path,
    clone_url: Optional[str] = None,
    initial_commit: bool = True
) -> GitHelper:
    """
    Setup git for a project directory.

    Args:
        project_dir: Project working directory
        clone_url: Optional git clone URL
        initial_commit: Whether to make an initial commit

    Returns:
        GitHelper instance
    """
    helper = GitHelper(project_dir, clone_url)

    # Initialize or clone
    success = await helper.init_or_clone()
    if not success:
        logger.error(f"Failed to initialize git at {project_dir}")
        return helper

    # Make initial commit if requested and there are files
    if initial_commit:
        await helper.commit_changes(
            "Initial project setup",
            agent_id="system"
        )
        if clone_url:
            await helper.push()

    return helper
