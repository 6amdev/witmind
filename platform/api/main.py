#!/usr/bin/env python3
"""
6AMDev Platform API - Simplified Version
Triggers PM agent to create tasks for Mission Control
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import redis
import yaml
import httpx

# Import task runner and git helper
from .task_runner import TaskRunner, task_queue, start_task_queue
from .git_helper import GitHelper, setup_project_git

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger('platform_api')

# Redis connection for Mission Control
REDIS_URL = os.getenv('MISSION_CONTROL_REDIS', 'redis://localhost:6381')
_redis_client = None

def get_redis():
    """Get Redis client"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info(f"Connected to Redis: {REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            _redis_client = None
    return _redis_client

def publish_event(event_type: str, data: dict):
    """Publish event to Mission Control via Redis"""
    r = get_redis()
    if r:
        try:
            event = {
                'type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                **data
            }
            r.publish('mission_control', json.dumps(event))
            logger.debug(f"Published: {event_type}")
        except Exception as e:
            logger.warning(f"Failed to publish: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown"""
    logger.info("Platform API starting...")
    # Start task queue processor
    await start_task_queue()
    logger.info("Task queue processor started")
    yield
    # Stop task queue
    task_queue.stop()
    logger.info("Platform API shutting down")


app = FastAPI(
    title="6AMDev Platform API",
    description="API for Mission Control integration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Execution modes
class ExecutionMode:
    FULL_AUTO = "full_auto"       # PM creates tasks → auto dispatch → auto complete
    REVIEW_FIRST = "review_first" # PM creates tasks → user reviews → manual dispatch
    MANUAL = "manual"             # User creates tasks manually


# Request models
class StartProjectRequest(BaseModel):
    project_id: str
    name: str
    description: str
    team_id: str = "dev"
    execution_mode: str = "review_first"  # full_auto, review_first, manual
    mission_control_url: str = "http://192.168.80.203:4000"
    git_clone_url: Optional[str] = None  # Git URL for version control


class RunTaskRequest(BaseModel):
    task_id: str
    agent_id: Optional[str] = None  # If not specified, uses task's assigned_to


class RunTasksRequest(BaseModel):
    task_ids: List[str]
    agent_id: Optional[str] = None  # Apply same agent to all tasks


# PM Agent prompt template
PM_AGENT_PROMPT = '''You are a Project Manager AI agent. Your job is to analyze project requirements and create tasks.

# Project Details
- Project ID: {project_id}
- Name: {name}
- Description:
{description}

# Your Task
1. Analyze the project description carefully
2. Break it down into specific, actionable tasks
3. Create 3-8 tasks covering the main work items

# CRITICAL: You MUST create tasks using curl commands

For EACH task, execute a curl command like this:

```bash
curl -X POST "{api_url}/api/tasks" -H "Content-Type: application/json" -d '{{"project_id": "{project_id}", "title": "YOUR_TASK_TITLE", "description": "What needs to be done", "priority": "medium", "status": "planned"}}'
```

Example tasks to create (adapt based on project):
- Setup project structure
- Implement core features
- Create UI components
- Write tests
- Documentation

After creating ALL tasks, report completion:

```bash
curl -X POST "{api_url}/api/agent/activity" -H "Content-Type: application/json" -d '{{"agent_id": "pm", "project_id": "{project_id}", "type": "agent_completed", "message": "Created tasks for project planning"}}'
```

Now analyze this project and create appropriate tasks. Execute the curl commands!
'''


async def auto_dispatch_tasks(project_id: str, api_url: str):
    """
    Auto-dispatch all tasks for a project to appropriate dev agents.
    Used in FULL_AUTO mode after PM creates tasks.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch all tasks for this project
            response = await client.get(f"{api_url}/api/projects/{project_id}/tasks")
            if response.status_code != 200:
                logger.error(f"Failed to fetch tasks: {response.status_code}")
                return

            tasks = response.json()
            logger.info(f"Found {len(tasks)} tasks to dispatch")
            print(f"[PLATFORM] FULL_AUTO: Found {len(tasks)} tasks to dispatch", flush=True)

            # Filter tasks that are in 'planned' status
            planned_tasks = [t for t in tasks if t.get('status') == 'planned']
            logger.info(f"Dispatching {len(planned_tasks)} planned tasks")

            # Add all tasks to the queue
            for task in planned_tasks:
                task_id = task.get('id')
                # Determine agent based on task type or use fullstack_dev as default
                agent_id = task.get('assigned_to') or 'fullstack_dev'

                logger.info(f"Queuing task {task_id} for agent {agent_id}")
                print(f"[PLATFORM] FULL_AUTO: Queuing task {task_id} for {agent_id}", flush=True)

                await task_queue.add_task(task_id, agent_id)

            logger.info(f"All {len(planned_tasks)} tasks queued for execution")
            print(f"[PLATFORM] FULL_AUTO: All tasks queued!", flush=True)

    except Exception as e:
        logger.error(f"Error in auto_dispatch_tasks: {e}")
        print(f"[PLATFORM] FULL_AUTO ERROR: {e}", flush=True)


async def run_pm_agent(
    project_id: str,
    name: str,
    description: str,
    team_id: str,
    api_url: str,
    execution_mode: str = "review_first",
    git_clone_url: str = None
):
    """Run PM agent using Claude Code CLI"""
    logger.info(f"Starting PM agent for project: {project_id}")
    logger.info(f"Execution mode: {execution_mode}")
    if git_clone_url:
        logger.info(f"Git integration enabled")

    # Report agent started
    publish_event('agent:status', {
        'agentId': 'pm',
        'name': 'Project Manager',
        'status': 'working',
        'projectId': project_id
    })

    # Build prompt
    prompt = PM_AGENT_PROMPT.format(
        project_id=project_id,
        name=name,
        description=description,
        api_url=api_url
    )

    try:
        # Create project workspace
        root_path = Path(os.environ.get('WITMIND_ROOT', '/home/wit/6amdev/platform'))
        project_path = root_path / 'projects' / 'active' / project_id
        project_path.mkdir(parents=True, exist_ok=True)

        # Initialize git if clone URL provided
        git_helper = None
        if git_clone_url:
            logger.info(f"Setting up Git for project {project_id}")
            git_helper = await setup_project_git(project_path, git_clone_url, initial_commit=False)

        # Save project info
        project_yaml = {
            'project': {
                'id': project_id,
                'name': name,
                'description': description,
                'team': team_id,
                'status': 'planning',
                'created_at': datetime.now().isoformat(),
                'git_clone_url': git_clone_url,
            }
        }
        with open(project_path / 'PROJECT.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(project_yaml, f, allow_unicode=True)

        # Run Claude Code
        logger.info(f"Running Claude Code for project {project_id}")
        process = await asyncio.create_subprocess_exec(
            'claude', '-p', prompt,
            '--allowedTools', 'Bash,Read,Write',
            '--output-format', 'text',
            cwd=str(project_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=300  # 5 minute timeout
        )

        output = stdout.decode() if stdout else ''
        error = stderr.decode() if stderr else ''

        logger.info(f"Claude output length: {len(output)}")
        if error:
            logger.warning(f"Claude stderr: {error[:500]}")

        if process.returncode == 0:
            logger.info(f"PM agent completed for project: {project_id}")
            print(f"[PLATFORM] PM agent completed for project: {project_id}", flush=True)

            # Determine next status based on execution mode
            if execution_mode == ExecutionMode.FULL_AUTO:
                next_status = "in_progress"
            else:
                next_status = "review"

            # Update project status
            update_url = f"{api_url}/api/projects/{project_id}"
            logger.info(f"Updating project status to {next_status} at: {update_url}")
            print(f"[PLATFORM] Calling PATCH {update_url}", flush=True)

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.patch(
                        update_url,
                        json={"status": next_status}
                    )
                    if response.status_code == 200:
                        logger.info(f"SUCCESS: Updated project {project_id} status to {next_status}")
                        print(f"[PLATFORM] SUCCESS: Project status updated to {next_status}", flush=True)
                    else:
                        logger.error(f"FAILED: Status update returned {response.status_code}: {response.text}")
                        print(f"[PLATFORM] FAILED: {response.status_code} - {response.text}", flush=True)
            except httpx.TimeoutException as e:
                logger.error(f"TIMEOUT: Failed to update project status: {e}")
                print(f"[PLATFORM] TIMEOUT: {e}", flush=True)
            except httpx.ConnectError as e:
                logger.error(f"CONNECT ERROR: Failed to update project status: {e}")
                print(f"[PLATFORM] CONNECT ERROR: {e}", flush=True)
            except Exception as e:
                logger.error(f"ERROR: Failed to update project status: {type(e).__name__}: {e}")
                print(f"[PLATFORM] ERROR: {type(e).__name__}: {e}", flush=True)

            # Commit PM agent work to Git
            if git_helper:
                logger.info(f"Committing PM agent work for project {project_id}")
                await git_helper.commit_and_push(
                    message=f"PM agent: Project planning complete\n\nProject: {name}",
                    agent_id="pm"
                )

            # If FULL_AUTO mode, dispatch all tasks to dev agents
            if execution_mode == ExecutionMode.FULL_AUTO:
                logger.info(f"FULL_AUTO mode: Auto-dispatching tasks for project {project_id}")
                print(f"[PLATFORM] FULL_AUTO: Fetching tasks to dispatch...", flush=True)
                await auto_dispatch_tasks(project_id, api_url)

            publish_event('agent:status', {
                'agentId': 'pm',
                'status': 'standby'
            })
            publish_event('agent:complete', {
                'agentId': 'pm',
                'projectId': project_id,
                'success': True
            })
        else:
            logger.error(f"PM agent failed with code {process.returncode}")
            publish_event('agent:status', {
                'agentId': 'pm',
                'status': 'error',
                'error': error[:500] if error else 'Unknown error'
            })

    except asyncio.TimeoutError:
        logger.error(f"PM agent timed out for project: {project_id}")
        publish_event('agent:status', {
            'agentId': 'pm',
            'status': 'error',
            'error': 'Agent timed out'
        })
    except Exception as e:
        logger.error(f"PM agent error: {e}")
        publish_event('agent:status', {
            'agentId': 'pm',
            'status': 'error',
            'error': str(e)
        })


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "ok", "service": "platform-api"}


@app.get("/status")
async def get_status():
    """Get platform status"""
    return {
        "status": "running",
        "redis": get_redis() is not None,
        "claude_cli": os.path.exists("/usr/bin/claude") or os.path.exists("/usr/local/bin/claude")
    }


@app.post("/start")
async def start_project(request: StartProjectRequest, background_tasks: BackgroundTasks):
    """
    Start a project - triggers PM agent to analyze and create tasks.
    Called by Mission Control when user clicks "Start Project".

    Execution modes:
    - full_auto: PM creates tasks → auto dispatch to dev agents → auto complete
    - review_first: PM creates tasks → user reviews → manual dispatch
    - manual: User creates tasks manually
    """
    logger.info(f"Starting project: {request.project_id} - {request.name}")
    logger.info(f"Execution mode: {request.execution_mode}")
    if request.git_clone_url:
        logger.info(f"Git integration enabled for project")

    # Run PM agent in background
    background_tasks.add_task(
        run_pm_agent,
        project_id=request.project_id,
        name=request.name,
        description=request.description,
        team_id=request.team_id,
        api_url=request.mission_control_url,
        execution_mode=request.execution_mode,
        git_clone_url=request.git_clone_url
    )

    return {
        "status": "started",
        "project_id": request.project_id,
        "execution_mode": request.execution_mode,
        "git_enabled": request.git_clone_url is not None,
        "message": f"PM agent is analyzing the project (mode: {request.execution_mode})"
    }


@app.post("/run-task")
async def run_task_endpoint(request: RunTaskRequest, background_tasks: BackgroundTasks):
    """
    Run a single task with an AI agent.
    The task will be executed in the background.
    """
    logger.info(f"Running task: {request.task_id} with agent: {request.agent_id}")

    # Add to queue for background processing
    await task_queue.add_task(request.task_id, request.agent_id)

    return {
        "status": "queued",
        "task_id": request.task_id,
        "agent_id": request.agent_id,
        "message": "Task queued for execution"
    }


@app.post("/run-tasks")
async def run_tasks_endpoint(request: RunTasksRequest, background_tasks: BackgroundTasks):
    """
    Run multiple tasks with AI agents.
    Tasks will be executed in the background.
    """
    logger.info(f"Running {len(request.task_ids)} tasks")

    # Add all tasks to queue
    for task_id in request.task_ids:
        await task_queue.add_task(task_id, request.agent_id)

    return {
        "status": "queued",
        "task_count": len(request.task_ids),
        "task_ids": request.task_ids,
        "message": f"{len(request.task_ids)} tasks queued for execution"
    }


@app.get("/queue-status")
async def get_queue_status():
    """Get current task queue status"""
    return {
        "queue_size": task_queue.queue.qsize(),
        "is_running": task_queue.is_running
    }


@app.get("/project-files/{project_id}")
async def get_project_files(project_id: str):
    """
    List all files in a project's output directory.
    """
    root_path = Path(os.environ.get('WITMIND_ROOT', '/home/wit/6amdev/platform'))
    project_path = root_path / 'projects' / 'active' / project_id

    if not project_path.exists():
        return {"files": [], "total_size": 0, "output_dir": str(project_path)}

    files = []
    total_size = 0

    for file_path in project_path.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(project_path)
            file_size = file_path.stat().st_size
            files.append({
                "path": str(relative_path),
                "name": file_path.name,
                "size": file_size,
                "extension": file_path.suffix,
            })
            total_size += file_size

    return {
        "files": sorted(files, key=lambda x: x["path"]),
        "total_size": total_size,
        "file_count": len(files),
        "output_dir": str(project_path)
    }


@app.get("/project-download/{project_id}")
async def download_project(project_id: str):
    """
    Download all project files as a ZIP archive.
    """
    import io
    import zipfile
    from fastapi.responses import StreamingResponse

    root_path = Path(os.environ.get('WITMIND_ROOT', '/home/wit/6amdev/platform'))
    project_path = root_path / 'projects' / 'active' / project_id

    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project directory not found")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(project_path)
                zip_file.write(file_path, relative_path)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={project_id}.zip"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4005)
