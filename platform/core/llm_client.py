#!/usr/bin/env python3
"""
LLM Client - Unified interface for different LLM providers

Supports:
- Anthropic Claude (via API)
- OpenRouter
- Ollama (local)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

logger = logging.getLogger('llm_client')


class BaseLLMClient(ABC):
    """Base class for LLM clients"""

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> str:
        """Send chat messages and get response"""
        pass


class ClaudeLLMClient(BaseLLMClient):
    """
    Claude API client using Anthropic SDK.

    This is the primary LLM for intelligent agents.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-sonnet-4-20250514"  # Latest Sonnet
            logger.info("Claude LLM client initialized")
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> str:
        """
        Send messages to Claude and get response.

        Args:
            messages: List of {'role': 'user'|'assistant', 'content': '...'}
            system: System prompt
            max_tokens: Max response tokens
            temperature: Randomness (0-1)

        Returns:
            Response text
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system if system else anthropic.NOT_GIVEN,
                messages=messages
            )

            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text

            return ""

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise


class OllamaLLMClient(BaseLLMClient):
    """
    Ollama client for local LLMs.

    Good for:
    - Testing without API costs
    - Simple tasks
    - Boilerplate code generation
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        self.base_url = base_url
        self.model = model

        try:
            import httpx
            self.client = httpx.Client(base_url=base_url, timeout=120.0)
            logger.info(f"Ollama LLM client initialized: {model}")
        except ImportError:
            raise ImportError("httpx package not installed. Run: pip install httpx")

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> str:
        """Send messages to Ollama and get response"""
        try:
            # Build prompt from messages
            prompt = ""
            if system:
                prompt += f"System: {system}\n\n"

            for msg in messages:
                role = msg['role'].capitalize()
                content = msg['content']
                prompt += f"{role}: {content}\n"

            prompt += "Assistant: "

            # Call Ollama API
            response = self.client.post(
                "/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                logger.error(f"Ollama error: {response.text}")
                return ""

        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise


class OpenRouterLLMClient(BaseLLMClient):
    """
    OpenRouter client - Unified API for multiple LLM providers.

    Benefits:
    - One API key for Claude, GPT-4, Llama, and more
    - Some models are FREE
    - Pay-as-you-go pricing
    - Easy to switch models

    Get API key: https://openrouter.ai/keys
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "anthropic/claude-3.5-sonnet",
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found")

        self.model = model
        self.base_url = base_url

        try:
            import httpx
            self.client = httpx.Client(
                base_url=base_url,
                timeout=120.0,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "Witmind AI Platform"
                }
            )
            logger.info(f"OpenRouter LLM client initialized: {model}")
        except ImportError:
            raise ImportError("httpx package not installed. Run: pip install httpx")

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7,
    ) -> str:
        """Send messages to OpenRouter and get response"""
        try:
            # Build messages list
            api_messages = []

            # Add system message if provided
            if system:
                api_messages.append({
                    "role": "system",
                    "content": system
                })

            # Add conversation messages
            api_messages.extend(messages)

            # Call OpenRouter API
            response = self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": api_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                return ""
            else:
                logger.error(f"OpenRouter error: {response.status_code} - {response.text}")
                return f"[Error: {response.status_code}]"

        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            raise


class LLMClientFactory:
    """Factory for creating LLM clients"""

    @staticmethod
    def create(provider: str = "claude", **kwargs) -> BaseLLMClient:
        """
        Create LLM client by provider name.

        Args:
            provider: 'claude', 'ollama', 'openrouter'
            **kwargs: Provider-specific arguments

        Returns:
            LLM client instance
        """
        if provider == "claude":
            return ClaudeLLMClient(**kwargs)
        elif provider == "ollama":
            return OllamaLLMClient(**kwargs)
        elif provider == "openrouter":
            return OpenRouterLLMClient(**kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")


# Convenience function
def create_llm_client(provider: str = "claude", **kwargs) -> BaseLLMClient:
    """Create an LLM client"""
    return LLMClientFactory.create(provider, **kwargs)
