#!/usr/bin/env python3
"""
6AMDev AI Platform - Agent Runner
Executes individual agents with their configurations

Integrated with Mission Control for real-time tracking.
"""

import os
import yaml
import json
import logging
import subprocess
import redis
from pathlib import Path
from typing import Dict, Optional, Callable
from datetime import datetime

from llm_router import LLMRouter, TaskComplexity

logger = logging.getLogger('agent_runner')

# Redis connection for Mission Control integration
# Port 6381 is exposed by Mission Control's Redis container
REDIS_URL = os.getenv('MISSION_CONTROL_REDIS', 'redis://192.168.80.203:6381')
_redis_client = None

def get_redis():
    """Get Redis client for publishing events to Mission Control"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info(f"Connected to Mission Control Redis: {REDIS_URL}")
        except Exception as e:
            logger.warning(f"Mission Control Redis not available: {e}")
            _redis_client = None
    return _redis_client

def publish_to_mission_control(event_type: str, data: dict):
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
            logger.debug(f"Published to Mission Control: {event_type}")
        except Exception as e:
            logger.warning(f"Failed to publish to Mission Control: {e}")


class AgentRunner:
    """
    Runs individual agents based on their configuration.
    Handles prompt loading, LLM routing, and result processing.
    """

    def __init__(self, root_path: Path, llm_router: LLMRouter):
        self.root_path = root_path
        self.llm_router = llm_router
        self.agents_cache: Dict[str, Dict] = {}

    def load_agent(self, agent_id: str, team_id: str) -> Optional[Dict]:
        """Load agent configuration"""
        cache_key = f"{team_id}/{agent_id}"

        if cache_key in self.agents_cache:
            return self.agents_cache[cache_key]

        agent_path = self.root_path / 'teams' / team_id / 'agents' / f'{agent_id}.yaml'

        if not agent_path.exists():
            logger.error(f"Agent not found: {agent_path}")
            return None

        with open(agent_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Load prompt file if specified
        prompt_file = config.get('prompt_file')
        if prompt_file:
            prompt_path = self.root_path / 'teams' / team_id / prompt_file
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    config['system_prompt'] = f.read()

        self.agents_cache[cache_key] = config
        return config

    def run(self, agent_id: str, team_id: str, project_id: str) -> Dict:
        """
        Run an agent for a specific project.
        Returns result dictionary with success status and output.
        """
        logger.info(f"Running agent: {agent_id} for project: {project_id}")

        # Load agent config
        agent_config = self.load_agent(agent_id, team_id)
        if not agent_config:
            return {
                'success': False,
                'error': f"Agent not found: {agent_id}"
            }

        # Get project context
        project_path = self.root_path / 'projects' / 'active' / project_id
        project_context = self._get_project_context(project_path)

        # Build prompt
        prompt = self._build_prompt(agent_config, project_context)

        # Determine LLM to use
        llm_config = agent_config.get('llm', {})
        primary = llm_config.get('primary', {})

        # Determine complexity based on agent role
        role = agent_config.get('agent', {}).get('role', 'developer')
        if role in ['manager', 'architect']:
            complexity = TaskComplexity.HIGH
        elif role in ['tester', 'reviewer']:
            complexity = TaskComplexity.MEDIUM
        else:
            complexity = TaskComplexity.MEDIUM

        # Route to LLM
        preferred = None
        if primary.get('provider') == 'claude_code':
            preferred = 'claude_code'
        elif primary.get('provider') == 'ollama':
            preferred = f"ollama/{primary.get('model', 'llama3.2')}"

        response = self.llm_router.route(
            prompt=prompt,
            task_type=agent_id,
            complexity=complexity,
            preferred_provider=preferred
        )

        if not response.success:
            return {
                'success': False,
                'error': response.error,
                'agent': agent_id
            }

        # Process response
        result = self._process_response(agent_config, response.content, project_path)

        # Log agent activity
        self._log_agent_activity(agent_id, project_id, result)

        return result

    def _get_project_context(self, project_path: Path) -> Dict:
        """Gather project context for the agent"""
        context = {
            'path': str(project_path),
            'files': [],
            'spec': None,
            'architecture': None,
            'tasks': None
        }

        # List files
        if project_path.exists():
            for f in project_path.rglob('*'):
                if f.is_file() and not f.name.startswith('.'):
                    context['files'].append(str(f.relative_to(project_path)))

        # Load key files
        spec_file = project_path / 'SPEC.md'
        if spec_file.exists():
            context['spec'] = spec_file.read_text(encoding='utf-8')

        arch_file = project_path / 'ARCHITECTURE.md'
        if arch_file.exists():
            context['architecture'] = arch_file.read_text(encoding='utf-8')

        tasks_file = project_path / 'TASKS.md'
        if tasks_file.exists():
            context['tasks'] = tasks_file.read_text(encoding='utf-8')

        return context

    def _build_prompt(self, agent_config: Dict, context: Dict) -> str:
        """Build the prompt for the agent"""
        agent_info = agent_config.get('agent', {})
        system_prompt = agent_config.get('system_prompt', '')

        prompt_parts = []

        # System prompt
        if system_prompt:
            prompt_parts.append(f"# System Instructions\n{system_prompt}")

        # Agent identity
        prompt_parts.append(f"""
# Your Role
You are {agent_info.get('name', 'an AI agent')}.
Role: {agent_info.get('role', 'assistant')}
Description: {agent_info.get('description', '')}

# Capabilities
{', '.join(agent_config.get('capabilities', []))}
""")

        # Project context
        if context.get('spec'):
            prompt_parts.append(f"# Project Specification\n{context['spec']}")

        if context.get('architecture'):
            prompt_parts.append(f"# Architecture\n{context['architecture']}")

        if context.get('tasks'):
            prompt_parts.append(f"# Tasks\n{context['tasks']}")

        # Current files
        if context.get('files'):
            prompt_parts.append(f"# Existing Files\n{json.dumps(context['files'], indent=2)}")

        # Behavior guidelines
        behavior = agent_config.get('behavior', {})
        if behavior:
            prompt_parts.append(f"""
# Behavior Guidelines
- Ask user when: {', '.join(behavior.get('ask_user_when', []))}
- Auto proceed when: {', '.join(behavior.get('auto_proceed_when', []))}
""")

        # Task instruction
        prompt_parts.append("""
# Task
Based on the project context above, perform your role's responsibilities.
Output your work in a structured format.
If you need to create files, specify the file path and content clearly.
If you need user input, clearly state the question and options.
""")

        return '\n\n'.join(prompt_parts)

    def _process_response(self, agent_config: Dict, response: str, project_path: Path) -> Dict:
        """Process the LLM response and extract actions"""
        result = {
            'success': True,
            'output': response,
            'files_created': [],
            'needs_input': False,
            'next_agent': None
        }

        # Check if user input is needed
        if 'NEED_INPUT:' in response or 'QUESTION:' in response:
            result['needs_input'] = True
            # Extract question
            for line in response.split('\n'):
                if line.startswith('QUESTION:'):
                    result['question'] = line.replace('QUESTION:', '').strip()
                    break

        # Check for file creation markers
        if '```' in response:
            # Extract file content (simplified)
            # In production, this would be more sophisticated
            pass

        # Determine next agent from workflow
        workflow = agent_config.get('workflow', {})
        notifies = workflow.get('notifies', [])
        if notifies:
            result['next_agent'] = notifies[0]

        return result

    def _log_agent_activity(self, agent_id: str, project_id: str, result: Dict):
        """Log agent activity"""
        log_dir = self.root_path / 'logs' / 'agents'
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{agent_id}.log"

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent': agent_id,
            'project': project_id,
            'success': result.get('success'),
            'needs_input': result.get('needs_input'),
            'next_agent': result.get('next_agent')
        }

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')

    def run_with_tools(self, agent_id: str, team_id: str, project_id: str, task_id: str = None) -> Dict:
        """
        Run agent with full tool access using Claude Code CLI.
        This allows agents to actually create/edit files.

        Publishes real-time events to Mission Control via Redis.
        """
        agent_config = self.load_agent(agent_id, team_id)
        if not agent_config:
            publish_to_mission_control('agent:error', {
                'agentId': agent_id,
                'error': 'Agent not found'
            })
            return {'success': False, 'error': 'Agent not found'}

        project_path = self.root_path / 'projects' / 'active' / project_id
        context = self._get_project_context(project_path)
        prompt = self._build_prompt(agent_config, context)

        # Get allowed tools
        allowed_tools = agent_config.get('allowed_tools', [])
        tools_arg = ','.join(allowed_tools) if allowed_tools else 'Read,Write,Edit,Bash'

        agent_name = agent_config.get('agent', {}).get('name', agent_id)

        # Publish: Agent starting
        publish_to_mission_control('agent:status', {
            'agentId': agent_id,
            'name': agent_name,
            'status': 'working',
            'currentTask': task_id,
            'projectId': project_id
        })

        try:
            # Run claude with tools using Popen for streaming
            process = subprocess.Popen(
                [
                    'claude', '-p', prompt,
                    '--allowedTools', tools_arg,
                    '--output-format', 'stream-json'
                ],
                cwd=str(project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            output_lines = []

            # Stream output to Mission Control
            for line in iter(process.stdout.readline, ''):
                if line:
                    output_lines.append(line)
                    # Parse and publish streaming output
                    try:
                        data = json.loads(line.strip())
                        if data.get('type') == 'assistant':
                            publish_to_mission_control('agent:output', {
                                'agentId': agent_id,
                                'taskId': task_id,
                                'content': data.get('content', ''),
                                'streaming': True
                            })
                        elif data.get('type') == 'tool_use':
                            publish_to_mission_control('agent:tool', {
                                'agentId': agent_id,
                                'taskId': task_id,
                                'tool': data.get('tool', 'unknown'),
                                'status': 'running'
                            })
                    except json.JSONDecodeError:
                        # Non-JSON output, still publish
                        publish_to_mission_control('agent:output', {
                            'agentId': agent_id,
                            'taskId': task_id,
                            'content': line.strip(),
                            'streaming': True
                        })

            process.wait(timeout=600)
            stderr = process.stderr.read()

            if process.returncode == 0:
                # Publish: Agent completed
                publish_to_mission_control('agent:status', {
                    'agentId': agent_id,
                    'status': 'standby',
                    'currentTask': None
                })
                publish_to_mission_control('agent:complete', {
                    'agentId': agent_id,
                    'taskId': task_id,
                    'projectId': project_id,
                    'success': True
                })
                return {
                    'success': True,
                    'output': ''.join(output_lines),
                    'agent': agent_id
                }
            else:
                # Publish: Agent error
                publish_to_mission_control('agent:status', {
                    'agentId': agent_id,
                    'status': 'error',
                    'error': stderr
                })
                return {
                    'success': False,
                    'error': stderr,
                    'agent': agent_id
                }

        except subprocess.TimeoutExpired:
            process.kill()
            publish_to_mission_control('agent:status', {
                'agentId': agent_id,
                'status': 'error',
                'error': 'Agent timed out'
            })
            return {
                'success': False,
                'error': 'Agent timed out',
                'agent': agent_id
            }
        except Exception as e:
            publish_to_mission_control('agent:status', {
                'agentId': agent_id,
                'status': 'error',
                'error': str(e)
            })
            return {
                'success': False,
                'error': str(e),
                'agent': agent_id
            }
