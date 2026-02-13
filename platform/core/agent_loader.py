#!/usr/bin/env python3
"""
Agent Loader - Load agents from YAML configs

Bridges existing YAML agent definitions with IntelligentAgent system.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from core.intelligent_agent import IntelligentAgent, create_intelligent_agent
from core.llm_client import create_llm_client
from core.agent_tools import create_tool_registry

# Load environment variables from ~/.env
env_file = Path.home() / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()


class AgentLoader:
    """Load and instantiate agents from YAML configs"""

    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self.agents_cache: Dict[str, IntelligentAgent] = {}

    def load_agent_config(self, agent_id: str, team: str = 'dev') -> Dict:
        """Load agent YAML config"""
        config_path = self.agents_dir / team / 'agents' / f'{agent_id}.yaml'

        if not config_path.exists():
            raise FileNotFoundError(f"Agent config not found: {config_path}")

        with open(config_path) as f:
            return yaml.safe_load(f)

    def create_agent(
        self,
        agent_id: str,
        team: str,
        project_root: Path,
        llm_provider: Optional[str] = None
    ) -> IntelligentAgent:
        """Create IntelligentAgent from YAML config"""

        config = self.load_agent_config(agent_id, team)
        agent_config = config['agent']
        llm_config = config.get('llm', {})

        # Determine LLM (use OpenRouter by default)
        if not llm_provider:
            llm_provider = 'openrouter'

        # Map model names
        model_map = {
            'opus': 'anthropic/claude-opus-4',
            'sonnet': 'anthropic/claude-3.5-sonnet',
            'haiku': 'anthropic/claude-3.5-haiku',
        }

        llm_model = llm_config.get('primary', {}).get('model', 'sonnet')
        if llm_model in model_map:
            llm_model = model_map[llm_model]

        # Create LLM & tools
        llm = create_llm_client(llm_provider, model=llm_model)
        tools = create_tool_registry(project_root)

        # Build config for IntelligentAgent
        intelligent_config = {
            'description': agent_config['description'],
            'role': agent_config['role'],
            'capabilities': config.get('capabilities', []),
            'max_iterations': config.get('limits', {}).get('max_iterations', 10),
            'timeout_seconds': config.get('limits', {}).get('timeout_minutes', 30) * 60,
        }

        # Create agent
        agent = create_intelligent_agent(
            agent_id=agent_id,
            team=team,
            config=intelligent_config,
            llm_client=llm,
            project_root=project_root,
            tools=tools
        )

        return agent

    def load_team(self, team: str, project_root: Path) -> Dict[str, IntelligentAgent]:
        """Load all agents from a team"""
        agents_dir = self.agents_dir / team / 'agents'
        agents = {}

        for config_file in agents_dir.glob('*.yaml'):
            agent_id = config_file.stem
            try:
                agent = self.create_agent(agent_id, team, project_root)
                agents[agent_id] = agent
            except Exception as e:
                print(f"⚠️  Failed to load {agent_id}: {e}")

        return agents


def load_all_agents(agents_dir: Path, project_root: Path) -> Dict[str, IntelligentAgent]:
    """Load ALL 21 agents from all teams"""
    loader = AgentLoader(agents_dir)
    all_agents = {}

    for team in ['dev', 'marketing', 'creative']:
        team_agents = loader.load_team(team, project_root)
        all_agents.update(team_agents)

    return all_agents


if __name__ == '__main__':
    # Test loading
    agents_dir = Path(__file__).parent.parent / 'teams'
    project_root = Path('/tmp/test-project')
    project_root.mkdir(exist_ok=True)

    all_agents = load_all_agents(agents_dir, project_root)
    print(f"✅ Loaded {len(all_agents)} agents:")
    for agent_id in all_agents:
        print(f"  - {agent_id}")
