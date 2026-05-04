"""Unified Model Dispatcher Service.

This module provides a unified interface for interacting with different LLM providers:
- Ollama (local models)
- OpenAI API (and compatible APIs like Azure, custom endpoints)
- Anthropic (future support)
- vLLM (future support)

The dispatcher abstracts away provider-specific details and provides a consistent API.
"""
import json
import asyncio
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime

import httpx
from loguru import logger

from app.core.config import settings


@dataclass
class ModelInfo:
    """Model information."""
    id: str
    name: str
    provider: str
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    context_window: int = 4096


@dataclass
class ChatMessage:
    """Chat message format."""
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class ChatCompletion:
    """Chat completion response."""
    content: str
    model: str
    usage: dict
    finish_reason: str
    tool_calls: Optional[list[dict]] = None


@dataclass
class StreamChunk:
    """Streaming response chunk."""
    content: str
    delta: str
    tool_call: Optional[dict] = None
    finish_reason: Optional[str] = None
    usage: Optional[dict] = None


class BaseModelProvider(ABC):
    """Abstract base class for model providers."""
    
    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> ChatCompletion:
        """Send a chat completion request."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Send a streaming chat completion request."""
        pass
    
    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """List available models."""
        pass


class OllamaProvider(BaseModelProvider):
    """Ollama local model provider."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> ChatCompletion:
        """Send a chat completion request to Ollama."""
        payload = {
            "model": model,
            "messages": [self._format_message(m) for m in messages],
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }
        
        if tools:
            payload["tools"] = tools
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return ChatCompletion(
                content=data["message"]["content"],
                model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0},  # Ollama doesn't always provide this
                finish_reason=data.get("done_reason", "stop"),
                tool_calls=data["message"].get("tool_calls"),
            )
        except httpx.HTTPError as e:
            logger.error(f"Ollama chat error: {e}")
            raise
    
    async def stream(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Send a streaming chat completion request to Ollama."""
        payload = {
            "model": model,
            "messages": [self._format_message(m) for m in messages],
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": True,
        }
        
        if tools:
            payload["tools"] = tools
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                accumulated_content = ""
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        delta = data.get("message", {}).get("content", "")
                        accumulated_content += delta
                        
                        tool_call = None
                        if data.get("message", {}).get("tool_calls"):
                            tool_call = data["message"]["tool_calls"][0]
                        
                        yield StreamChunk(
                            content=accumulated_content,
                            delta=delta,
                            tool_call=tool_call,
                            finish_reason=data.get("done_reason") if data.get("done") else None,
                        )
                        
                        if data.get("done"):
                            yield StreamChunk(
                                content=accumulated_content,
                                delta="",
                                finish_reason=data.get("done_reason", "stop"),
                                usage=data.get("eval_count", 0),
                            )
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except httpx.HTTPError as e:
            logger.error(f"Ollama stream error: {e}")
            raise
    
    async def list_models(self) -> list[ModelInfo]:
        """List available Ollama models."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model in data.get("models", []):
                models.append(ModelInfo(
                    id=model["name"],
                    name=model["name"],
                    provider="ollama",
                    supports_streaming=True,
                    supports_function_calling=False,  # Most Ollama models don't support this yet
                ))
            return models
        except httpx.HTTPError as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def _format_message(self, message: ChatMessage) -> dict:
        """Format a chat message for Ollama."""
        result = {
            "role": message.role,
            "content": message.content,
        }
        if message.name:
            result["name"] = message.name
        if message.tool_call_id:
            result["tool_call_id"] = message.tool_call_id
        return result
    
    async def health_check(self) -> dict:
        """Check Ollama health and connectivity."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return {"status": "online", "error": None}
            return {"status": "offline", "error": f"HTTP {response.status_code}"}
        except httpx.ConnectError:
            return {"status": "offline", "error": "Connection refused"}
        except httpx.TimeoutException:
            return {"status": "offline", "error": "Connection timeout"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class OpenAIProvider(BaseModelProvider):
    """OpenAI API compatible provider."""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_API_BASE
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> ChatCompletion:
        """Send a chat completion request to OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [self._format_message(m) for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            choice = data["choices"][0]
            return ChatCompletion(
                content=choice["message"]["content"] or "",
                model=model,
                usage=data.get("usage", {}),
                finish_reason=choice.get("finish_reason", "stop"),
                tool_calls=choice["message"].get("tool_calls"),
            )
        except httpx.HTTPError as e:
            logger.error(f"OpenAI chat error: {e}")
            raise
    
    async def stream(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Send a streaming chat completion request to OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [self._format_message(m) for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                accumulated_content = ""
                
                async for line in response.aiter_lines():
                    if not line.strip() or not line.startswith("data: "):
                        continue
                    
                    if line.strip() == "data: [DONE]":
                        break
                    
                    try:
                        data = json.loads(line[6:])
                        delta = data["choices"][0]["delta"]
                        
                        content = delta.get("content", "")
                        accumulated_content += content
                        
                        tool_call = None
                        if delta.get("tool_calls"):
                            tool_call = delta["tool_calls"][0]
                        
                        yield StreamChunk(
                            content=accumulated_content,
                            delta=content,
                            tool_call=tool_call,
                            finish_reason=data["choices"][0].get("finish_reason"),
                        )
                    except json.JSONDecodeError:
                        continue
                        
        except httpx.HTTPError as e:
            logger.error(f"OpenAI stream error: {e}")
            raise
    
    async def list_models(self) -> list[ModelInfo]:
        """List available OpenAI models."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # Common OpenAI models with their capabilities
        common_models = [
            ModelInfo("gpt-4-turbo-preview", "GPT-4 Turbo", "openai", True, True, True, 128000),
            ModelInfo("gpt-4", "GPT-4", "openai", True, True, True, 8192),
            ModelInfo("gpt-3.5-turbo", "GPT-3.5 Turbo", "openai", True, True, False, 16385),
        ]
        
        return common_models
    
    def _format_message(self, message: ChatMessage) -> dict:
        """Format a chat message for OpenAI."""
        result = {
            "role": message.role,
            "content": message.content,
        }
        if message.name:
            result["name"] = message.name
        if message.tool_call_id:
            result["tool_call_id"] = message.tool_call_id
        if message.tool_calls:
            result["tool_calls"] = message.tool_calls
        return result
    
    async def health_check(self) -> dict:
        """Check OpenAI API health."""
        if not self.api_key:
            return {"status": "offline", "error": "API key not configured"}
        try:
            response = await self.client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5.0
            )
            if response.status_code == 200:
                return {"status": "online", "error": None}
            return {"status": "offline", "error": f"HTTP {response.status_code}"}
        except httpx.ConnectError:
            return {"status": "offline", "error": "Connection refused"}
        except httpx.TimeoutException:
            return {"status": "offline", "error": "Connection timeout"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class ModelDispatcher:
    """Unified model dispatcher for all LLM providers."""
    
    def __init__(self):
        self.providers: dict[str, BaseModelProvider] = {
            "ollama": OllamaProvider(),
            "openai": OpenAIProvider(),
        }
    
    def get_provider(self, provider: str) -> BaseModelProvider:
        """Get a model provider by name."""
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        return self.providers[provider]
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        provider: str = "ollama",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> ChatCompletion:
        """Send a chat completion request."""
        provider_instance = self.get_provider(provider)
        return await provider_instance.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs
        )
    
    async def stream(
        self,
        messages: list[ChatMessage],
        model: str,
        provider: str = "ollama",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Send a streaming chat completion request."""
        provider_instance = self.get_provider(provider)
        async for chunk in provider_instance.stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs
        ):
            yield chunk
    
    async def list_all_models(self) -> dict[str, list[ModelInfo]]:
        """List all available models from all providers."""
        result = {}
        for name, provider in self.providers.items():
            try:
                result[name] = await provider.list_models()
            except Exception as e:
                logger.warning(f"Failed to list models from {name}: {e}")
                result[name] = []
        return result
    
    async def health_check_all(self) -> dict[str, dict]:
        """Check health of all providers."""
        result = {}
        for name, provider in self.providers.items():
            try:
                result[name] = await provider.health_check()
            except Exception as e:
                result[name] = {"status": "offline", "error": str(e)}
        return result
    
    async def get_provider_status(self, provider: str) -> dict:
        """Get status of a specific provider."""
        if provider not in self.providers:
            return {"status": "unknown", "error": f"Unknown provider: {provider}"}
        try:
            return await self.providers[provider].health_check()
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    async def close(self):
        """Close all provider connections."""
        for provider in self.providers.values():
            await provider.close()


# Global dispatcher instance
_dispatcher: Optional[ModelDispatcher] = None


def get_model_dispatcher() -> ModelDispatcher:
    """Get the global model dispatcher instance."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = ModelDispatcher()
    return _dispatcher
