#!/usr/bin/env python3
"""
LLM Router - Support multiple LLM providers
Providers: Claude (Anthropic), OpenRouter, Ollama
"""

import os
import json
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, AsyncGenerator
from enum import Enum

import httpx

logger = logging.getLogger('llm_router')


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
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"


class BaseLLMClient(ABC):
    """Base class for LLM clients"""

    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion"""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream completion"""
        pass


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude API client"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = config.base_url or "https://api.anthropic.com"

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.config.model,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "messages": messages,
        }

        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["content"][0]["text"],
                model=data["model"],
                provider="claude",
                usage={
                    "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                    "output_tokens": data.get("usage", {}).get("output_tokens", 0),
                },
                finish_reason=data.get("stop_reason", "stop")
            )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.config.model,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "messages": messages,
            "stream": True,
        }

        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data.get("type") == "content_block_delta":
                            yield data["delta"].get("text", "")


class OpenRouterClient(BaseLLMClient):
    """OpenRouter API client"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = config.base_url or "https://openrouter.ai/api/v1"

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://6amdev.com",
            "X-Title": "6AMDev Platform",
        }

        # Prepend system message if provided
        all_messages = messages.copy()
        if system:
            all_messages.insert(0, {"role": "system", "content": system})

        payload = {
            "model": self.config.model,
            "messages": all_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data.get("model", self.config.model),
                provider="openrouter",
                usage=data.get("usage", {}),
                finish_reason=data["choices"][0].get("finish_reason", "stop")
            )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://6amdev.com",
            "X-Title": "6AMDev Platform",
        }

        all_messages = messages.copy()
        if system:
            all_messages.insert(0, {"role": "system", "content": system})

        payload = {
            "model": self.config.model,
            "messages": all_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and not line.endswith("[DONE]"):
                        try:
                            data = json.loads(line[6:])
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue


class OllamaClient(BaseLLMClient):
    """Ollama local LLM client"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.base_url = config.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        # Prepend system message if provided
        all_messages = messages.copy()
        if system:
            all_messages.insert(0, {"role": "system", "content": system})

        payload = {
            "model": self.config.model,
            "messages": all_messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            }
        }

        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                content=data["message"]["content"],
                model=data.get("model", self.config.model),
                provider="ollama",
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                },
                finish_reason="stop"
            )

    async def stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        all_messages = messages.copy()
        if system:
            all_messages.insert(0, {"role": "system", "content": system})

        payload = {
            "model": self.config.model,
            "messages": all_messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            }
        }

        async with httpx.AsyncClient(timeout=600.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data:
                                yield data["message"].get("content", "")
                        except json.JSONDecodeError:
                            continue


class LLMRouter:
    """Router for multiple LLM providers"""

    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.default_configs: Dict[str, LLMConfig] = {}

    def register_config(self, name: str, config: LLMConfig):
        """Register a named LLM configuration"""
        self.default_configs[name] = config
        self.clients[name] = self._create_client(config)

    def _create_client(self, config: LLMConfig) -> BaseLLMClient:
        """Create client based on provider"""
        if config.provider == LLMProvider.CLAUDE:
            return ClaudeClient(config)
        elif config.provider == LLMProvider.OPENROUTER:
            return OpenRouterClient(config)
        elif config.provider == LLMProvider.OLLAMA:
            return OllamaClient(config)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    def get_client(self, name: str) -> BaseLLMClient:
        """Get client by name"""
        if name not in self.clients:
            raise ValueError(f"Unknown LLM config: {name}")
        return self.clients[name]

    async def complete(
        self,
        config_name: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using named config"""
        client = self.get_client(config_name)
        return await client.complete(messages, system, **kwargs)

    async def stream(
        self,
        config_name: str,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream completion using named config"""
        client = self.get_client(config_name)
        async for chunk in client.stream(messages, system, **kwargs):
            yield chunk


# Default router instance with common configurations
def create_default_router() -> LLMRouter:
    """Create router with default configurations"""
    router = LLMRouter()

    # Claude configurations
    if os.getenv("ANTHROPIC_API_KEY"):
        router.register_config("claude-opus", LLMConfig(
            provider=LLMProvider.CLAUDE,
            model="claude-opus-4-5-20251101"
        ))
        router.register_config("claude-sonnet", LLMConfig(
            provider=LLMProvider.CLAUDE,
            model="claude-sonnet-4-20250514"
        ))

    # OpenRouter configurations
    if os.getenv("OPENROUTER_API_KEY"):
        router.register_config("openrouter-gpt4", LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model="openai/gpt-4-turbo"
        ))
        router.register_config("openrouter-claude", LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model="anthropic/claude-3-opus"
        ))
        router.register_config("openrouter-llama", LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model="meta-llama/llama-3-70b-instruct"
        ))

    # Ollama configurations (local)
    router.register_config("ollama-codellama", LLMConfig(
        provider=LLMProvider.OLLAMA,
        model="codellama:34b"
    ))
    router.register_config("ollama-mistral", LLMConfig(
        provider=LLMProvider.OLLAMA,
        model="mistral:7b"
    ))
    router.register_config("ollama-llama3", LLMConfig(
        provider=LLMProvider.OLLAMA,
        model="llama3:8b"
    ))

    return router


# Global router instance
llm_router = create_default_router()


# Agent to LLM mapping
AGENT_LLM_MAPPING = {
    "pm": "claude-opus",
    "tech_lead": "claude-opus",
    "frontend_dev": "claude-sonnet",
    "backend_dev": "claude-sonnet",
    "fullstack_dev": "claude-sonnet",
    "qa_tester": "ollama-mistral",  # Use local for cost saving
    "devops": "claude-sonnet",
}


def get_llm_for_agent(agent_id: str) -> str:
    """Get LLM config name for agent"""
    return AGENT_LLM_MAPPING.get(agent_id, "claude-sonnet")
