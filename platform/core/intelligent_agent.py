#!/usr/bin/env python3
"""
Intelligent Agent Core - Agent with real agentic capabilities

This implements the "agentic loop":
1. Think - Agent analyzes the situation
2. Act - Agent decides and executes actions (use tools, write files, etc.)
3. Evaluate - Agent checks if task is complete
4. Repeat - Continue until task is done or max iterations

Key concepts:
- Agent has memory (remembers what it did)
- Agent has tools (can do actions)
- Agent has context (knows current situation)
- Agent can make decisions (autonomy)
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger('intelligent_agent')


class AgentState(Enum):
    """Agent execution states"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_INPUT = "waiting_input"


@dataclass
class AgentAction:
    """Represents an action taken by the agent"""
    type: str  # 'tool_use', 'file_write', 'decision', 'question'
    description: str
    params: Dict[str, Any]
    timestamp: str = None
    result: Optional[Dict] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class AgentMemory:
    """Agent's memory of what it has done"""
    actions: List[AgentAction]
    thoughts: List[str]
    context: Dict[str, Any]
    deliverables: List[str]

    def add_action(self, action: AgentAction):
        """Record an action"""
        self.actions.append(action)

    def add_thought(self, thought: str):
        """Record a thought process"""
        self.thoughts.append({
            'content': thought,
            'timestamp': datetime.utcnow().isoformat()
        })

    def get_summary(self) -> str:
        """Get a summary of what agent has done"""
        return f"""
Agent Memory Summary:
- Actions taken: {len(self.actions)}
- Thoughts recorded: {len(self.thoughts)}
- Deliverables created: {len(self.deliverables)}
- Last action: {self.actions[-1].description if self.actions else 'None'}
"""


class IntelligentAgent:
    """
    An agent with real intelligence and autonomy.

    This is the core that makes agents "smart":
    - Can think (analyze situation)
    - Can act (use tools, write files)
    - Can evaluate (check if done)
    - Can learn (remember what worked)
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict,
        llm_client: Any,  # LLM client (Claude, OpenRouter, etc.)
        tools: Any,  # Dict[str, Callable] or ToolRegistry
        project_root: Path,
    ):
        self.agent_id = agent_id
        self.config = config
        self.llm = llm_client

        # Support both dict of callables and ToolRegistry
        if hasattr(tools, 'execute_tool'):
            # It's a ToolRegistry
            self.tool_registry = tools
            self.tools = {name: lambda **params: tools.execute_tool(name, **params)
                         for name in tools.get_all_tools().keys()}
        else:
            # It's a dict of callables
            self.tool_registry = None
            self.tools = tools

        self.project_root = project_root

        # Agent state
        self.state = AgentState.IDLE
        self.memory = AgentMemory(
            actions=[],
            thoughts=[],
            context={},
            deliverables=[]
        )

        # Limits
        self.max_iterations = config.get('limits', {}).get('max_iterations', 10)
        self.max_tokens = config.get('limits', {}).get('max_tokens', 8000)

        # System prompt from config
        self.system_prompt = config.get('system_prompt', '')

        logger.info(f"Initialized intelligent agent: {agent_id}")

    def execute_task(self, task: Dict) -> Dict:
        """
        Main entry point - execute a task using agentic loop.

        Args:
            task: {
                'type': 'analyze_requirements',
                'description': 'Create specification for Todo App',
                'inputs': ['request.yaml'],
                'expected_outputs': ['SPEC.md', 'TASKS.md']
            }

        Returns:
            {
                'success': True/False,
                'output': {...},
                'deliverables': ['SPEC.md'],
                'needs_input': False,
                'error': None
            }
        """
        logger.info(f"Agent {self.agent_id} starting task: {task.get('type')}")

        # Build initial context
        context = self._build_context(task)

        # Agentic loop
        for iteration in range(self.max_iterations):
            logger.info(f"Iteration {iteration + 1}/{self.max_iterations}")

            try:
                # 1. THINK - Agent analyzes current situation
                self.state = AgentState.THINKING
                thought = self._think(context, iteration)
                self.memory.add_thought(thought)

                # 2. ACT - Agent decides and executes action
                self.state = AgentState.ACTING
                action = self._act(thought, context)

                if action is None:
                    # Agent decided no action needed
                    continue

                # Execute the action
                action_result = self._execute_action(action)
                action.result = action_result
                self.memory.add_action(action)

                # Update context with result
                context['last_action'] = asdict(action)

                # 3. EVALUATE - Check if task is complete
                self.state = AgentState.EVALUATING
                evaluation = self._evaluate(task, context)

                if evaluation['is_complete']:
                    logger.info(f"Task completed in {iteration + 1} iterations")
                    self.state = AgentState.COMPLETED
                    return {
                        'success': True,
                        'output': evaluation['output'],
                        'deliverables': self.memory.deliverables,
                        'iterations': iteration + 1,
                        'memory': self._export_memory()
                    }

                if evaluation.get('needs_user_input'):
                    self.state = AgentState.WAITING_INPUT
                    return {
                        'success': False,
                        'needs_input': True,
                        'question': evaluation['question'],
                        'options': evaluation.get('options', []),
                        'memory': self._export_memory()
                    }

                # 4. REPEAT - Update context for next iteration
                if evaluation.get('next_thought'):
                    context['previous_evaluation'] = evaluation

            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                self.state = AgentState.FAILED
                return {
                    'success': False,
                    'error': str(e),
                    'memory': self._export_memory()
                }

        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        return {
            'success': False,
            'error': 'Max iterations reached',
            'partial_output': context,
            'memory': self._export_memory()
        }

    def _build_context(self, task: Dict) -> Dict:
        """Build initial context for the agent"""
        context = {
            'task': task,
            'agent': {
                'id': self.agent_id,
                'role': self.config.get('agent', {}).get('role'),
                'capabilities': self.config.get('capabilities', [])
            },
            'project': {
                'root': str(self.project_root),
            },
            'iteration': 0,
            'available_tools': list(self.tools.keys()),
        }

        # Load input files if specified
        if task.get('inputs'):
            context['inputs'] = {}
            for input_file in task['inputs']:
                file_path = self.project_root / input_file
                if file_path.exists():
                    context['inputs'][input_file] = file_path.read_text()

        return context

    def _think(self, context: Dict, iteration: int) -> str:
        """
        Agent thinks about current situation.
        Returns a thought/plan as string.
        """
        # Build the thinking prompt
        thinking_prompt = f"""
You are {self.config.get('agent', {}).get('name')}.
Your role: {self.config.get('agent', {}).get('description')}

Current task: {context['task'].get('description')}

Iteration: {iteration + 1}

What you've done so far:
{self.memory.get_summary()}

Available tools: {', '.join(context['available_tools'])}

Think about:
1. What is the current situation?
2. What needs to be done next?
3. What action should you take?
4. Are there any blockers or questions?

Provide your thought process:
"""

        # Call LLM for thinking
        response = self._call_llm(thinking_prompt, max_tokens=1000)

        logger.info(f"Agent thought: {response[:200]}...")
        return response

    def _act(self, thought: str, context: Dict) -> Optional[AgentAction]:
        """
        Agent decides what action to take based on thought.
        Returns an AgentAction or None.
        """
        task = context.get('task', {})
        expected_outputs = task.get('expected_outputs', [])

        # Build action decision prompt
        action_prompt = f"""
Based on your thought process above, decide your next action.

Task: {task.get('description', 'No description')}
Expected outputs: {', '.join(expected_outputs) if expected_outputs else 'None specified'}

IMPORTANT: Choose ONE action to take right now.

Available actions:

1. CREATE_FILE - Create a file with content
   When to use: When you need to create {', '.join(expected_outputs)}
   Format:
   ```
   CREATE_FILE: filename.md
   ---CONTENT---
   [Your file content here - be detailed and complete]
   ---END---
   ```

2. ASK_USER - Ask user for clarification
   When to use: When requirements are unclear or ambiguous
   Format: ASK_USER: What is your question?

3. COMPLETE - Declare task complete
   When to use: When all expected outputs have been created
   Format: COMPLETE: Brief summary of what was accomplished

Your decision (choose ONE):
"""

        response = self._call_llm(action_prompt, max_tokens=4000)

        # Parse the decision
        return self._parse_action(response)

    def _parse_action(self, decision: str) -> Optional[AgentAction]:
        """Parse agent's decision into an AgentAction"""
        decision = decision.strip()

        # Handle CREATE_FILE with ---CONTENT--- markers
        if 'CREATE_FILE:' in decision:
            lines = decision.split('\n')
            filename = None
            content_lines = []
            in_content = False

            for line in lines:
                if line.startswith('CREATE_FILE:'):
                    filename = line[12:].strip()
                elif '---CONTENT---' in line:
                    in_content = True
                elif '---END---' in line:
                    break
                elif in_content:
                    content_lines.append(line)

            if filename:
                content = '\n'.join(content_lines).strip()
                return AgentAction(
                    type='create_file',
                    description=f"Create file: {filename}",
                    params={'filename': filename, 'content': content}
                )

        # Handle ASK_USER
        if decision.startswith('ASK_USER:'):
            question = decision[9:].strip()
            return AgentAction(
                type='ask_user',
                description="Ask user for input",
                params={'question': question}
            )

        # Handle COMPLETE
        if decision.startswith('COMPLETE:'):
            summary = decision[9:].strip()
            return AgentAction(
                type='complete',
                description="Task complete",
                params={'summary': summary}
            )

        # If nothing matched, return None
        logger.warning(f"Could not parse action from: {decision[:100]}...")
        return None

    def _execute_action(self, action: AgentAction) -> Dict:
        """Execute an action and return result"""
        if action.type == 'tool_use':
            tool_name = action.params['tool']
            if tool_name in self.tools:
                tool_fn = self.tools[tool_name]
                result = tool_fn(**action.params)
                return {'success': True, 'result': result}
            else:
                return {'success': False, 'error': f'Tool {tool_name} not found'}

        elif action.type == 'create_file':
            filename = action.params['filename']
            content = action.params['content']
            file_path = self.project_root / filename

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

            self.memory.deliverables.append(filename)
            logger.info(f"Created file: {filename}")

            return {'success': True, 'file': filename}

        elif action.type == 'ask_user':
            # Will be handled in evaluate
            return {'success': True, 'needs_input': True}

        elif action.type == 'complete':
            return {'success': True, 'complete': True}

        return {'success': False, 'error': 'Unknown action type'}

    def _evaluate(self, task: Dict, context: Dict) -> Dict:
        """
        Evaluate if task is complete.
        Returns evaluation result.
        """
        last_action = context.get('last_action', {})

        # Check if agent declared completion
        if last_action.get('type') == 'complete':
            return {
                'is_complete': True,
                'output': last_action.get('result', {}).get('summary', '')
            }

        # Check if agent needs user input
        if last_action.get('type') == 'ask_user':
            return {
                'is_complete': False,
                'needs_user_input': True,
                'question': last_action['params']['question']
            }

        # Check if expected outputs are created
        expected = task.get('expected_outputs', [])
        if expected:
            all_created = all(
                (self.project_root / f).exists()
                for f in expected
            )
            if all_created:
                return {
                    'is_complete': True,
                    'output': f"Created all deliverables: {', '.join(expected)}"
                }

        # Not complete yet
        return {
            'is_complete': False,
            'next_thought': 'Continue working on task'
        }

    def _call_llm(self, prompt: str, max_tokens: int = None) -> str:
        """
        Call LLM with system prompt + user prompt.
        """
        if max_tokens is None:
            max_tokens = self.max_tokens

        messages = [{'role': 'user', 'content': prompt}]

        try:
            response = self.llm.chat(
                messages=messages,
                system=self.system_prompt,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return f"[Error: {str(e)}]"

    def _export_memory(self) -> Dict:
        """Export agent memory for persistence"""
        return {
            'actions': [asdict(a) for a in self.memory.actions],
            'thoughts': self.memory.thoughts,
            'deliverables': self.memory.deliverables,
            'context': self.memory.context
        }


def create_intelligent_agent(
    agent_id: str,
    team_id: str,
    config_path: Path,
    llm_client: Any,
    project_root: Path,
    tool_registry: Any = None
) -> IntelligentAgent:
    """
    Factory function to create an intelligent agent.

    Args:
        agent_id: Agent identifier (e.g., 'pm', 'frontend_dev')
        team_id: Team identifier (e.g., 'dev')
        config_path: Path to agent config file
        llm_client: LLM client instance
        project_root: Project root directory
        tool_registry: ToolRegistry instance (optional, will create default if not provided)

    Returns:
        IntelligentAgent instance
    """
    # Load agent config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Load system prompt if specified
    if config.get('prompt_file'):
        prompt_path = config_path.parent.parent / config['prompt_file']
        if prompt_path.exists():
            config['system_prompt'] = prompt_path.read_text()

    # Create or use provided tool registry
    if tool_registry is None:
        try:
            from .agent_tools import create_tool_registry
            tool_registry = create_tool_registry(project_root)
        except ImportError:
            # Fallback to simple dict
            tool_registry = {
                'read_file': lambda path: {'success': True, 'content': Path(project_root / path).read_text()},
                'write_file': lambda path, content: {'success': True} if Path(project_root / path).write_text(content) or True else {},
                'list_files': lambda: {'success': True, 'files': [str(p) for p in project_root.iterdir()]},
            }

    return IntelligentAgent(
        agent_id=agent_id,
        config=config,
        llm_client=llm_client,
        tools=tool_registry,
        project_root=project_root
    )
