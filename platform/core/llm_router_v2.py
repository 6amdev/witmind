"""
LLM Router v2 - Agent-level LLM Configuration
Each agent can use different LLM provider/model
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM configuration for an agent"""
    provider: str = "claude_code"
    model: str = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 300

    @classmethod
    def from_dict(cls, data: Dict) -> "LLMConfig":
        return cls(
            provider=data.get("provider", "claude_code"),
            model=data.get("model"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096),
            timeout=data.get("timeout", 300)
        )


# Default LLM settings per agent role
AGENT_LLM_DEFAULTS = {
    # === High Quality (Use best models) ===
    "business_analyst": {
        "provider": "claude_code",
        "model": "claude-opus-4-20250514",  # Best for analysis
        "temperature": 0.5,
        "reason": "BA needs deep understanding and quality analysis"
    },
    "uxui_designer": {
        "provider": "claude_code",
        "model": "claude-opus-4-20250514",
        "temperature": 0.7,
        "reason": "UX needs creativity and detailed design"
    },
    "tech_lead": {
        "provider": "claude_code",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.5,
        "reason": "Architecture needs accuracy"
    },
    "security_auditor": {
        "provider": "claude_code",
        "model": "claude-opus-4-20250514",
        "temperature": 0.3,
        "reason": "Security needs thorough analysis"
    },

    # === Standard Quality ===
    "pm": {
        "provider": "claude_code",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.5
    },
    "backend_dev": {
        "provider": "claude_code",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.5
    },
    "frontend_dev": {
        "provider": "claude_code",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.5
    },
    "fullstack_dev": {
        "provider": "claude_code",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.5
    },
    "devops": {
        "provider": "claude_code",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.3
    },

    # === Can use cheaper/local models ===
    "qa_tester": {
        "provider": "ollama",  # Can run locally
        "model": "llama3.1:70b",
        "temperature": 0.3,
        "reason": "Testing is more mechanical, can use local"
    },

    # === Default fallback ===
    "_default": {
        "provider": "claude_code",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.5
    }
}


class AgentLLMRouter:
    """
    Routes each agent to its configured LLM

    Agent LLM can be configured in:
    1. Agent YAML file (agent.llm section)
    2. Platform config (config/agent_llm.yaml)
    3. Default settings (AGENT_LLM_DEFAULTS)

    Priority: Agent YAML > Platform Config > Defaults
    """

    def __init__(self, platform_path: str = None):
        self.platform_path = Path(platform_path or os.environ.get(
            "PLATFORM_PATH",
            os.path.expanduser("~/workspace/6amdev-platform")
        ))
        self.config_path = self.platform_path / "config" / "agent_llm.yaml"
        self._config_cache = None

    def load_platform_config(self) -> Dict:
        """Load platform-level agent LLM config"""
        if self._config_cache is not None:
            return self._config_cache

        if self.config_path.exists():
            with open(self.config_path) as f:
                self._config_cache = yaml.safe_load(f) or {}
        else:
            self._config_cache = {}

        return self._config_cache

    def get_agent_llm_config(self, agent_id: str, agent_yaml: Dict = None) -> LLMConfig:
        """
        Get LLM config for specific agent

        Args:
            agent_id: Agent identifier (e.g., "backend_dev")
            agent_yaml: Optional agent YAML config (if already loaded)

        Returns:
            LLMConfig for the agent
        """
        # 1. Check agent YAML first (highest priority)
        if agent_yaml:
            agent_llm = agent_yaml.get("agent", {}).get("llm", {})
            if agent_llm:
                return LLMConfig.from_dict(agent_llm)

        # 2. Check platform config
        platform_config = self.load_platform_config()
        if agent_id in platform_config.get("agents", {}):
            return LLMConfig.from_dict(platform_config["agents"][agent_id])

        # 3. Use defaults
        default = AGENT_LLM_DEFAULTS.get(agent_id, AGENT_LLM_DEFAULTS["_default"])
        return LLMConfig.from_dict(default)

    def get_provider(self, agent_id: str, agent_yaml: Dict = None):
        """Get LLM provider instance for agent"""
        from llm_router import LLMRouter

        config = self.get_agent_llm_config(agent_id, agent_yaml)
        return LLMRouter(
            provider=config.provider,
            model=config.model,
            config={
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "timeout": config.timeout
            }
        )


def create_agent_llm_config_template() -> str:
    """Generate template for agent LLM configuration"""
    template = """# Agent LLM Configuration
# Configure which LLM provider/model each agent uses
# Priority: Agent YAML > This Config > Defaults

# Global defaults (applied to all agents unless overridden)
defaults:
  provider: claude_code
  model: claude-sonnet-4-20250514
  temperature: 0.5
  max_tokens: 4096
  timeout: 300

# Per-agent configuration
agents:
  # === Critical Roles (Use best models) ===
  business_analyst:
    provider: claude_code
    model: claude-opus-4-20250514  # Best for deep analysis
    temperature: 0.5
    reason: "BA needs thorough business understanding"

  uxui_designer:
    provider: claude_code
    model: claude-opus-4-20250514
    temperature: 0.7  # More creative
    reason: "UX needs creativity and detail"

  security_auditor:
    provider: claude_code
    model: claude-opus-4-20250514
    temperature: 0.3  # More deterministic
    reason: "Security needs thorough analysis"

  # === Standard Roles ===
  pm:
    provider: claude_code
    model: claude-sonnet-4-20250514

  tech_lead:
    provider: claude_code
    model: claude-sonnet-4-20250514

  backend_dev:
    provider: claude_code
    model: claude-sonnet-4-20250514

  frontend_dev:
    provider: claude_code
    model: claude-sonnet-4-20250514

  fullstack_dev:
    provider: claude_code
    model: claude-sonnet-4-20250514

  devops:
    provider: claude_code
    model: claude-sonnet-4-20250514

  # === Can Use Cheaper/Local Models ===
  qa_tester:
    provider: ollama  # Run locally, free
    model: llama3.1:70b
    temperature: 0.3
    reason: "Testing is mechanical, can use local"

  # === OpenRouter Examples ===
  # content_writer:
  #   provider: openrouter
  #   model: anthropic/claude-3.5-sonnet
  #
  # data_analyst:
  #   provider: openrouter
  #   model: openai/gpt-4-turbo

# Provider configurations
providers:
  claude_code:
    # Uses Claude Code CLI (default)
    available_models:
      - claude-opus-4-20250514      # Most powerful
      - claude-sonnet-4-20250514    # Balanced (recommended)
      - claude-3-5-haiku-20241022   # Fast, cheap

  openrouter:
    api_key: ${OPENROUTER_API_KEY}
    available_models:
      - anthropic/claude-3.5-sonnet
      - anthropic/claude-3-opus
      - openai/gpt-4-turbo
      - meta-llama/llama-3.1-405b-instruct
      - google/gemini-pro-1.5

  ollama:
    host: http://localhost:11434
    available_models:
      - llama3.1:70b      # Best quality
      - llama3.1:8b       # Fast
      - codellama:34b     # Code specialized
      - deepseek-coder:33b
"""
    return template


# Example of agent YAML with LLM config
AGENT_YAML_EXAMPLE = """
# Example: agents/business_analyst.yaml
agent:
  id: business_analyst
  role: "Business Analyst"
  team: dev

  # LLM Configuration for this agent
  llm:
    provider: claude_code
    model: claude-opus-4-20250514
    temperature: 0.5
    max_tokens: 8192  # More tokens for analysis
    timeout: 600      # Longer timeout

  capabilities:
    - business_requirement_analysis
    - stakeholder_interview
    - use_case_writing

  outputs:
    - docs/BRD.md
    - docs/USER_STORIES.md
"""


if __name__ == "__main__":
    # Generate config template
    print("Agent LLM Config Template:")
    print("=" * 50)
    print(create_agent_llm_config_template())

    print("\n" + "=" * 50)
    print("Agent YAML Example:")
    print("=" * 50)
    print(AGENT_YAML_EXAMPLE)

    # Test router
    print("\n" + "=" * 50)
    print("Testing Agent LLM Router:")
    print("=" * 50)

    router = AgentLLMRouter()
    for agent_id in ["business_analyst", "backend_dev", "qa_tester", "unknown_agent"]:
        config = router.get_agent_llm_config(agent_id)
        print(f"\n{agent_id}:")
        print(f"  Provider: {config.provider}")
        print(f"  Model: {config.model}")
        print(f"  Temperature: {config.temperature}")
