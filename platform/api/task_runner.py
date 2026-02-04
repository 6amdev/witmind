#!/usr/bin/env python3
"""
Task Runner - Execute tasks with AI Agents
Supports multiple LLM providers: Claude, OpenRouter, Ollama
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

import httpx

from .git_helper import GitHelper

logger = logging.getLogger('task_runner')


class LLMProvider(Enum):
    CLAUDE = "claude"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


@dataclass
class LLMConfig:
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


# Default LLM configurations per agent type
AGENT_LLM_CONFIG: Dict[str, LLMConfig] = {
    "pm": LLMConfig(LLMProvider.CLAUDE, "claude-opus-4-5-20251101"),
    "tech_lead": LLMConfig(LLMProvider.CLAUDE, "claude-opus-4-5-20251101"),
    "frontend_dev": LLMConfig(LLMProvider.CLAUDE, "claude-sonnet-4-20250514"),
    "backend_dev": LLMConfig(LLMProvider.CLAUDE, "claude-sonnet-4-20250514"),
    "fullstack_dev": LLMConfig(LLMProvider.CLAUDE, "claude-sonnet-4-20250514"),
    "qa_tester": LLMConfig(LLMProvider.CLAUDE, "claude-sonnet-4-20250514"),
    "devops": LLMConfig(LLMProvider.CLAUDE, "claude-sonnet-4-20250514"),
}


# Agent prompts templates
AGENT_PROMPTS = {
    "pm": '''You are a Project Manager AI agent.
Your job is to break down project requirements into specific tasks.

# Task Details
- Task ID: {task_id}
- Title: {title}
- Description: {description}
- Project: {project_name}

# Instructions
1. Analyze the task requirements
2. Create a detailed plan
3. If this task needs to be broken into subtasks, create them
4. Report your findings and recommendations
''',

    "tech_lead": '''You are a Technical Lead AI agent.
Your job is to design architecture and make technical decisions.

# Task Details
- Task ID: {task_id}
- Title: {title}
- Description: {description}
- Project: {project_name}

# Instructions
1. Analyze the technical requirements
2. Design the architecture or solution
3. Document your decisions with reasoning
4. Create implementation guidelines for developers
''',

    "frontend_dev": '''You are a Frontend Developer AI agent.
Your job is to implement frontend features using React/TypeScript.

# Task Details
- Task ID: {task_id}
- Title: {title}
- Description: {description}
- Project: {project_name}

# Working Directory
{working_dir}

# Instructions
1. Read existing code to understand the codebase
2. Implement the required feature
3. Write clean, typed TypeScript code
4. Follow existing patterns and conventions
5. Test your implementation

Use the available tools: Read, Write, Edit, Bash
''',

    "backend_dev": '''You are a Backend Developer AI agent.
Your job is to implement backend features using Python/FastAPI.

# Task Details
- Task ID: {task_id}
- Title: {title}
- Description: {description}
- Project: {project_name}

# Working Directory
{working_dir}

# Instructions
1. Read existing code to understand the codebase
2. Implement the required feature
3. Write clean, typed Python code
4. Follow existing patterns and conventions
5. Write tests for your implementation

Use the available tools: Read, Write, Edit, Bash
''',

    "fullstack_dev": '''You are a Fullstack Developer AI agent.
Your job is to implement features across frontend and backend.

# Task Details
- Task ID: {task_id}
- Title: {title}
- Description: {description}
- Project: {project_name}

# Working Directory
{working_dir}

# Instructions
1. Read existing code to understand both frontend and backend
2. Implement the required feature end-to-end
3. Ensure frontend and backend work together
4. Write clean, typed code
5. Test your implementation

Use the available tools: Read, Write, Edit, Bash
''',

    "qa_tester": '''You are a QA Tester AI agent.
Your job is to test features and find bugs.

# Task Details
- Task ID: {task_id}
- Title: {title}
- Description: {description}
- Project: {project_name}

# Working Directory
{working_dir}

# Instructions
1. Understand what needs to be tested
2. Write test cases
3. Run tests
4. Report any bugs or issues found
5. Verify the feature works as expected

Use the available tools: Read, Write, Edit, Bash
''',

    "devops": '''You are a DevOps AI agent.
Your job is to handle deployment and infrastructure.

# Task Details
- Task ID: {task_id}
- Title: {title}
- Description: {description}
- Project: {project_name}

# Working Directory
{working_dir}

# Instructions
1. Understand deployment requirements
2. Configure infrastructure as needed
3. Deploy the application
4. Verify deployment success
5. Report deployment status

Use the available tools: Read, Write, Edit, Bash
''',
}


@dataclass
class TaskResult:
    success: bool
    output: str
    error: Optional[str] = None
    duration_ms: int = 0
    files_changed: list = None

    def __post_init__(self):
        if self.files_changed is None:
            self.files_changed = []


class TaskRunner:
    """Runs tasks with AI agents"""

    def __init__(
        self,
        mission_control_url: str = "http://192.168.80.203:4000",
        working_dir: str = "/home/wit/6amdev/platform/projects/active"
    ):
        self.mission_control_url = mission_control_url
        self.working_dir = Path(working_dir)
        self.event_callback = None
        # Current task context
        self.current_task_id: Optional[str] = None
        self.current_project_id: Optional[str] = None
        self.current_agent_id: Optional[str] = None

    def set_event_callback(self, callback):
        """Set callback for real-time events"""
        self.event_callback = callback

    async def emit_event(self, event_type: str, data: dict, project_id: str = None):
        """Emit event to Mission Control for Socket.io broadcast"""
        # Use current project_id if not explicitly provided
        project_id = project_id or self.current_project_id

        # Add task/agent context to data if not present
        if self.current_task_id and "taskId" not in data:
            data["taskId"] = self.current_task_id
        if self.current_agent_id and "agentId" not in data:
            data["agentId"] = self.current_agent_id

        # Log locally
        logger.info(f"Event: {event_type} - {json.dumps(data, default=str)}")

        # Call local callback if set
        if self.event_callback:
            await self.event_callback(event_type, data)

        # Forward to Mission Control for Socket.io broadcast
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                payload = {
                    "event_type": event_type,
                    "data": data,
                }
                if project_id:
                    payload["project_id"] = project_id

                await client.post(
                    f"{self.mission_control_url}/api/events",
                    json=payload
                )
        except Exception as e:
            logger.warning(f"Failed to forward event to Mission Control: {e}")

    async def get_task(self, task_id: str) -> Optional[dict]:
        """Fetch task details from Mission Control"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.mission_control_url}/api/tasks/{task_id}")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch task {task_id}: {e}")
        return None

    async def get_project(self, project_id: str) -> Optional[dict]:
        """Fetch project details from Mission Control"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.mission_control_url}/api/projects/{project_id}")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch project {project_id}: {e}")
        return None

    async def update_task_status(self, task_id: str, status: str):
        """Update task status in Mission Control"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.patch(
                    f"{self.mission_control_url}/api/tasks/{task_id}/move",
                    json={"status": status}
                )
                logger.info(f"Updated task {task_id} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")

    async def add_activity(self, task_id: str, activity_type: str, message: str, agent_id: str = None):
        """Add activity log to task"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get task to find project_id
                task = await self.get_task(task_id)
                if not task:
                    return

                await client.post(
                    f"{self.mission_control_url}/api/activities",
                    json={
                        "task_id": task_id,
                        "project_id": task.get("project_id"),
                        "type": activity_type,
                        "message": message,
                        "agent_id": agent_id,
                    }
                )
        except Exception as e:
            logger.error(f"Failed to add activity: {e}")

    async def deploy_project(self, project_id: str) -> Optional[str]:
        """
        Deploy project using docker-compose if available.
        Returns the preview URL if successful.
        """
        project_dir = self.working_dir / project_id
        compose_file = project_dir / "docker-compose.yml"

        if not compose_file.exists():
            # Try frontend subdirectory
            compose_file = project_dir / "frontend" / "docker-compose.yml"
            if not compose_file.exists():
                logger.info(f"No docker-compose.yml found for project {project_id}")
                return None

        # Assign a port based on project_id hash (5000-5999 range)
        port = 5000 + (hash(project_id) % 1000)

        try:
            # Create a modified docker-compose for this project
            compose_dir = compose_file.parent

            # Run docker compose with project-specific name
            process = await asyncio.create_subprocess_exec(
                'docker', 'compose', '-p', f'preview-{project_id[:8]}',
                '-f', str(compose_file),
                'up', '-d', '--build',
                cwd=str(compose_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'PREVIEW_PORT': str(port)}
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300  # 5 minute timeout for build
            )

            if process.returncode == 0:
                preview_url = f"http://192.168.80.203:{port}"
                logger.info(f"Project {project_id} deployed at {preview_url}")
                return preview_url
            else:
                logger.error(f"Deploy failed: {stderr.decode()[:500]}")
                return None

        except asyncio.TimeoutError:
            logger.error(f"Deploy timed out for project {project_id}")
            return None
        except Exception as e:
            logger.error(f"Deploy error: {e}")
            return None

    async def check_project_completion(self, project_id: str):
        """Check if all tasks are done and mark project as completed"""
        if not project_id:
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get all tasks for the project
                response = await client.get(
                    f"{self.mission_control_url}/api/projects/{project_id}/tasks"
                )
                if response.status_code != 200:
                    logger.error(f"Failed to fetch tasks for project {project_id}")
                    return

                tasks = response.json()
                if not tasks:
                    return

                # Check if all tasks are done
                all_done = all(t.get("status") == "done" for t in tasks)

                if all_done:
                    logger.info(f"All tasks done for project {project_id}, marking as completed")

                    # Try to deploy the project
                    preview_url = await self.deploy_project(project_id)

                    # Mark project as completed with preview URL
                    complete_data = {
                        "output_dir": str(self.working_dir / project_id)
                    }
                    if preview_url:
                        complete_data["preview_url"] = preview_url

                    complete_response = await client.post(
                        f"{self.mission_control_url}/api/projects/{project_id}/complete",
                        json=complete_data
                    )

                    if complete_response.status_code == 200:
                        logger.info(f"Project {project_id} marked as completed")
                        await self.emit_event("project:complete", {
                            "projectId": project_id,
                            "tasksCompleted": len(tasks),
                            "previewUrl": preview_url
                        }, project_id)
                    else:
                        logger.error(f"Failed to complete project: {complete_response.status_code}")

        except Exception as e:
            logger.error(f"Error checking project completion: {e}")

    def build_prompt(self, task: dict, project: dict, agent_id: str) -> str:
        """Build prompt for agent"""
        template = AGENT_PROMPTS.get(agent_id, AGENT_PROMPTS["fullstack_dev"])

        # Get working directory for project
        project_dir = self.working_dir / task.get("project_id", "default")
        project_dir.mkdir(parents=True, exist_ok=True)

        return template.format(
            task_id=task.get("id"),
            title=task.get("title", ""),
            description=task.get("description", ""),
            project_name=project.get("name", ""),
            working_dir=str(project_dir),
        )

    async def run_with_claude_cli(
        self,
        prompt: str,
        working_dir: Path,
        timeout: int = 600
    ) -> TaskResult:
        """Run task using Claude Code CLI"""
        start_time = datetime.now()

        try:
            # Emit starting event
            await self.emit_event("agent:action", {
                "message": "Starting Claude Code execution...",
                "type": "start"
            })

            process = await asyncio.create_subprocess_exec(
                'claude', '-p', prompt,
                '--allowedTools', 'Bash,Read,Write,Edit',
                '--output-format', 'text',
                cwd=str(working_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            output = stdout.decode() if stdout else ''
            error = stderr.decode() if stderr else ''

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            if process.returncode == 0:
                await self.emit_event("agent:action", {
                    "message": "Claude Code execution completed",
                    "type": "complete"
                })
                return TaskResult(
                    success=True,
                    output=output,
                    duration_ms=duration_ms
                )
            else:
                return TaskResult(
                    success=False,
                    output=output,
                    error=error[:500] if error else "Unknown error",
                    duration_ms=duration_ms
                )

        except asyncio.TimeoutError:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return TaskResult(
                success=False,
                output="",
                error="Execution timed out",
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return TaskResult(
                success=False,
                output="",
                error=str(e),
                duration_ms=duration_ms
            )

    async def run_task(self, task_id: str, agent_id: str = None) -> TaskResult:
        """
        Run a task with the specified agent.

        Args:
            task_id: The task ID to run
            agent_id: Optional agent ID (uses task's assigned_to if not specified)

        Returns:
            TaskResult with success status and output
        """
        logger.info(f"Running task {task_id} with agent {agent_id}")

        # Fetch task details
        task = await self.get_task(task_id)
        if not task:
            return TaskResult(success=False, output="", error="Task not found")

        # Use assigned agent or specified agent
        agent_id = agent_id or task.get("assigned_to", "fullstack_dev")

        # Fetch project details
        project = await self.get_project(task.get("project_id"))
        if not project:
            return TaskResult(success=False, output="", error="Project not found")

        # Store task context for events
        self.current_task_id = task_id
        self.current_project_id = task.get("project_id")
        self.current_agent_id = agent_id

        # Update task status to working
        await self.update_task_status(task_id, "working")

        # Emit agent started event
        await self.emit_event("agent:status", {
            "agentId": agent_id,
            "status": "working",
            "taskId": task_id
        })

        await self.add_activity(
            task_id,
            "agent_started",
            f"Agent {agent_id} started working on task",
            agent_id
        )

        # Build prompt
        prompt = self.build_prompt(task, project, agent_id)

        # Get working directory
        project_dir = self.working_dir / task.get("project_id", "default")
        project_dir.mkdir(parents=True, exist_ok=True)

        # Run with Claude CLI
        result = await self.run_with_claude_cli(prompt, project_dir)

        # Update task status based on result
        if result.success:
            await self.update_task_status(task_id, "done")
            await self.add_activity(
                task_id,
                "agent_completed",
                f"Agent {agent_id} completed task successfully",
                agent_id
            )

            # Commit changes to Git if enabled
            git_clone_url = project.get("git_clone_url")
            if git_clone_url:
                try:
                    git_helper = GitHelper(project_dir, git_clone_url)
                    task_title = task.get("title", "Task")
                    await git_helper.commit_and_push(
                        message=f"Task completed: {task_title}",
                        agent_id=agent_id,
                        task_id=task_id
                    )
                    logger.info(f"Committed task {task_id} changes to Git")
                except Exception as e:
                    logger.warning(f"Failed to commit to Git: {e}")

            # Check if all tasks are done and auto-complete project
            await self.check_project_completion(task.get("project_id"))
        else:
            # Reset task back to planned for retry
            await self.update_task_status(task_id, "planned")
            await self.add_activity(
                task_id,
                "agent_error",
                f"Agent {agent_id} failed: {result.error}. Task reset to planned.",
                agent_id
            )
            logger.warning(f"Task {task_id} failed, reset to planned for retry")

        # Emit agent completed event
        await self.emit_event("agent:status", {
            "agentId": agent_id,
            "status": "standby"
        })

        await self.emit_event("agent:complete", {
            "agentId": agent_id,
            "taskId": task_id,
            "success": result.success,
            "duration_ms": result.duration_ms
        })

        # Clear task context
        self.current_task_id = None
        self.current_project_id = None
        self.current_agent_id = None

        return result


# Task queue for background processing
class TaskQueue:
    """Simple in-memory task queue"""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.runner = TaskRunner()
        self.is_running = False

    async def add_task(self, task_id: str, agent_id: str = None):
        """Add task to queue"""
        await self.queue.put({"task_id": task_id, "agent_id": agent_id})
        logger.info(f"Task {task_id} added to queue")

    async def process_queue(self):
        """Process tasks from queue - runs tasks sequentially"""
        self.is_running = True
        logger.info("Task queue processor started")

        while self.is_running:
            try:
                # Wait for task with timeout
                try:
                    item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                task_id = item["task_id"]
                agent_id = item.get("agent_id")

                logger.info(f"Processing task {task_id}")

                try:
                    # Run task and wait for completion before processing next
                    result = await self.runner.run_task(task_id, agent_id)
                    logger.info(f"Task {task_id} completed: success={result.success}")
                except Exception as task_error:
                    # If task execution crashes, reset the task to planned
                    logger.error(f"Task {task_id} crashed: {task_error}")
                    try:
                        await self.runner.update_task_status(task_id, "planned")
                        logger.info(f"Task {task_id} reset to planned after crash")
                    except:
                        pass

                self.queue.task_done()

            except Exception as e:
                logger.error(f"Error in queue processor: {e}")

    def stop(self):
        """Stop queue processor"""
        self.is_running = False


# Global task queue instance
task_queue = TaskQueue()


async def start_task_queue():
    """Start the task queue processor"""
    asyncio.create_task(task_queue.process_queue())


async def run_task(task_id: str, agent_id: str = None) -> TaskResult:
    """
    Run a task immediately (not queued).
    For queued execution, use task_queue.add_task()
    """
    runner = TaskRunner()
    return await runner.run_task(task_id, agent_id)
