"""
LLM Router - Support multiple LLM providers
Supports: Claude Code, OpenRouter, Ollama
"""

import os
import json
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import requests


class LLMProvider(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> Dict[str, Any]:
        """Generate response from LLM"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass


class ClaudeCodeProvider(LLMProvider):
    """Claude Code CLI provider (default)"""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model
        self.claude_path = self._find_claude()

    def _find_claude(self) -> str:
        """Find claude CLI path"""
        # Check common locations
        paths = [
            "/usr/local/bin/claude",
            "/usr/bin/claude",
            os.path.expanduser("~/.local/bin/claude"),
            "claude"  # In PATH
        ]
        for path in paths:
            if os.path.exists(path) or self._command_exists(path):
                return path
        return "claude"

    def _command_exists(self, cmd: str) -> bool:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
            return True
        except:
            return False

    def is_available(self) -> bool:
        return self._command_exists(self.claude_path)

    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> Dict[str, Any]:
        """Run claude CLI with prompt"""
        try:
            cmd = [
                self.claude_path,
                "-p", prompt,
                "--model", self.model,
                "--output-format", "json"
            ]

            if system_prompt:
                cmd.extend(["--system", system_prompt])

            # Add allowed tools if specified
            allowed_tools = kwargs.get("allowed_tools", [])
            if allowed_tools:
                cmd.extend(["--allowedTools", ",".join(allowed_tools)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 300),
                cwd=kwargs.get("cwd")
            )

            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    return {
                        "success": True,
                        "response": output.get("result", result.stdout),
                        "provider": "claude_code"
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "response": result.stdout,
                        "provider": "claude_code"
                    }
            else:
                return {
                    "success": False,
                    "error": result.stderr or "Claude CLI failed",
                    "provider": "claude_code"
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Agent timed out",
                "provider": "claude_code"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "claude_code"
            }


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider"""

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: str = "anthropic/claude-3.5-sonnet"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> Dict[str, Any]:
        """Generate using OpenRouter API"""
        if not self.api_key:
            return {
                "success": False,
                "error": "OPENROUTER_API_KEY not set",
                "provider": "openrouter"
            }

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://6amdev.com",
                    "X-Title": "6AMDev Platform"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": kwargs.get("max_tokens", 4096),
                    "temperature": kwargs.get("temperature", 0.7)
                },
                timeout=kwargs.get("timeout", 120)
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "response": content,
                    "provider": "openrouter",
                    "model": self.model,
                    "usage": data.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"OpenRouter API error: {response.status_code} - {response.text}",
                    "provider": "openrouter"
                }

        except requests.Timeout:
            return {
                "success": False,
                "error": "OpenRouter request timed out",
                "provider": "openrouter"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "openrouter"
            }


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""

    def __init__(self,
                 host: str = "http://localhost:11434",
                 model: str = "llama3.1:70b"):
        self.host = host
        self.model = model

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except:
            pass
        return []

    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> Dict[str, Any]:
        """Generate using Ollama API"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 4096)
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=kwargs.get("timeout", 300)
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "provider": "ollama",
                    "model": self.model,
                    "eval_count": data.get("eval_count", 0),
                    "eval_duration": data.get("eval_duration", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"Ollama error: {response.status_code} - {response.text}",
                    "provider": "ollama"
                }

        except requests.Timeout:
            return {
                "success": False,
                "error": "Ollama request timed out",
                "provider": "ollama"
            }
        except requests.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to Ollama at {self.host}",
                "provider": "ollama"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "ollama"
            }


class LLMRouter:
    """
    Routes requests to appropriate LLM provider

    Usage:
        router = LLMRouter(provider="ollama", model="llama3.1:70b")
        result = router.generate("Write hello world in Python")
    """

    PROVIDERS = {
        "claude_code": ClaudeCodeProvider,
        "openrouter": OpenRouterProvider,
        "ollama": OllamaProvider
    }

    # Model recommendations per provider
    RECOMMENDED_MODELS = {
        "claude_code": [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-3-5-haiku-20241022"
        ],
        "openrouter": [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "openai/gpt-4-turbo",
            "meta-llama/llama-3.1-405b-instruct",
            "google/gemini-pro-1.5"
        ],
        "ollama": [
            "llama3.1:70b",
            "llama3.1:8b",
            "codellama:34b",
            "deepseek-coder:33b",
            "mixtral:8x7b",
            "qwen2:72b"
        ]
    }

    def __init__(self,
                 provider: str = "claude_code",
                 model: Optional[str] = None,
                 config: Optional[Dict] = None):
        """
        Initialize LLM Router

        Args:
            provider: "claude_code", "openrouter", or "ollama"
            model: Model name (uses default if not specified)
            config: Additional provider config (api_key, host, etc.)
        """
        self.provider_name = provider
        self.config = config or {}

        # Set default model if not specified
        if model:
            self.config["model"] = model
        elif provider in self.RECOMMENDED_MODELS:
            self.config["model"] = self.RECOMMENDED_MODELS[provider][0]

        # Initialize provider
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}. Use: {list(self.PROVIDERS.keys())}")

        self.provider = self.PROVIDERS[provider](**self.config)

    def is_available(self) -> bool:
        """Check if current provider is available"""
        return self.provider.is_available()

    def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> Dict[str, Any]:
        """Generate response from LLM"""
        return self.provider.generate(prompt, system_prompt, **kwargs)

    def get_status(self) -> Dict[str, Any]:
        """Get provider status"""
        return {
            "provider": self.provider_name,
            "model": self.config.get("model"),
            "available": self.is_available()
        }

    @classmethod
    def from_config_file(cls, config_path: str = "~/.6amdev/llm_config.yaml") -> "LLMRouter":
        """Load router from config file"""
        import yaml

        path = Path(config_path).expanduser()
        if path.exists():
            with open(path) as f:
                config = yaml.safe_load(f)

            return cls(
                provider=config.get("provider", "claude_code"),
                model=config.get("model"),
                config=config.get("config", {})
            )

        # Return default
        return cls()

    @classmethod
    def auto_select(cls) -> "LLMRouter":
        """
        Auto-select best available provider
        Priority: Claude Code > OpenRouter > Ollama
        """
        # Try Claude Code first
        claude = ClaudeCodeProvider()
        if claude.is_available():
            return cls(provider="claude_code")

        # Try OpenRouter
        openrouter = OpenRouterProvider()
        if openrouter.is_available():
            return cls(provider="openrouter")

        # Try Ollama
        ollama = OllamaProvider()
        if ollama.is_available():
            return cls(provider="ollama")

        # Default to Claude Code (will fail gracefully)
        return cls(provider="claude_code")


# Convenience functions
def get_router(provider: str = None, model: str = None) -> LLMRouter:
    """Get LLM router instance"""
    if provider:
        return LLMRouter(provider=provider, model=model)
    return LLMRouter.auto_select()


def generate(prompt: str,
             provider: str = None,
             model: str = None,
             system_prompt: str = "",
             **kwargs) -> Dict[str, Any]:
    """Quick generate function"""
    router = get_router(provider, model)
    return router.generate(prompt, system_prompt, **kwargs)


# Example usage
if __name__ == "__main__":
    # Test each provider
    print("Testing LLM Router...")

    # Check available providers
    providers = ["claude_code", "openrouter", "ollama"]
    for p in providers:
        try:
            router = LLMRouter(provider=p)
            status = router.get_status()
            print(f"\n{p}: {'✅ Available' if status['available'] else '❌ Not available'}")
            if status['available']:
                print(f"   Model: {status['model']}")
        except Exception as e:
            print(f"\n{p}: ❌ Error - {e}")

    # Auto-select and test
    print("\n--- Auto-select test ---")
    router = LLMRouter.auto_select()
    print(f"Selected: {router.provider_name}")

    if router.is_available():
        result = router.generate("Say 'Hello from LLM Router' in one line")
        if result["success"]:
            print(f"Response: {result['response'][:100]}...")
        else:
            print(f"Error: {result['error']}")

# Task Complexity Enum
class TaskComplexity(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
