"""AI client implementations for different providers."""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic
import openai
from pydantic import BaseModel

from .config import config

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Chat message model."""
    role: str
    content: str


class ChatResponse(BaseModel):
    """Chat response model."""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class AIClient(ABC):
    """Abstract base class for AI clients."""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.cache_enabled = config.enable_cache
        self.cache_dir = config.get_cache_path()
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate a chat completion."""
        pass
    
    def _get_cache_key(self, messages: List[Message], model: str, **kwargs) -> str:
        """Generate a cache key for the request."""
        data = {
            "messages": [msg.dict() for msg in messages],
            "model": model,
            **kwargs
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the cache file path."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _load_from_cache(self, cache_key: str) -> Optional[ChatResponse]:
        """Load response from cache."""
        if not self.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                return ChatResponse(**data)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, response: ChatResponse) -> None:
        """Save response to cache."""
        if not self.cache_enabled:
            return
        
        try:
            cache_path = self._get_cache_path(cache_key)
            with open(cache_path, 'w') as f:
                json.dump(response.dict(), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")


class OpenAIClient(AIClient):
    """OpenAI API client."""
    
    def __init__(self, api_key: str, org_id: Optional[str] = None):
        super().__init__(api_key)
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            organization=org_id
        )
    
    async def chat_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate a chat completion using OpenAI."""
        cache_key = self._get_cache_key(messages, model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        
        # Try to load from cache
        cached_response = self._load_from_cache(cache_key)
        if cached_response:
            logger.info("Using cached response")
            return cached_response
        
        # Convert messages to OpenAI format
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        # Prepare parameters
        params = {
            "model": model,
            "messages": openai_messages,
            "temperature": temperature,
            **kwargs
        }
        if max_tokens:
            params["max_tokens"] = max_tokens
        
        try:
            response = await self.client.chat.completions.create(**params)
            
            chat_response = ChatResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage=response.usage.dict() if response.usage else None
            )
            
            # Save to cache
            self._save_to_cache(cache_key, chat_response)
            
            return chat_response
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicClient(AIClient):
    """Anthropic API client."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def chat_completion(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Generate a chat completion using Anthropic."""
        cache_key = self._get_cache_key(messages, model, temperature=temperature, max_tokens=max_tokens, **kwargs)
        
        # Try to load from cache
        cached_response = self._load_from_cache(cache_key)
        if cached_response:
            logger.info("Using cached response")
            return cached_response
        
        # Convert messages to Anthropic format
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            elif msg.role == "user":
                user_messages.append(msg.content)
            elif msg.role == "assistant":
                # For Anthropic, we need to handle assistant messages differently
                # This is a simplified approach
                pass
        
        # Combine user messages
        user_content = "\n\n".join(user_messages)
        
        # Prepare parameters
        params = {
            "model": model,
            "max_tokens": max_tokens or 4000,
            "temperature": temperature,
            **kwargs
        }
        
        if system_message:
            params["system"] = system_message
        
        try:
            response = await self.client.messages.create(
                messages=[{"role": "user", "content": user_content}],
                **params
            )
            
            chat_response = ChatResponse(
                content=response.content[0].text,
                model=response.model,
                usage=response.usage.dict() if response.usage else None
            )
            
            # Save to cache
            self._save_to_cache(cache_key, chat_response)
            
            return chat_response
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


def get_client(provider: str = None) -> AIClient:
    """Get the appropriate AI client based on provider."""
    provider = provider or config.default_provider
    
    if provider == "openai":
        if not config.openai_api_key:
            raise ValueError("OpenAI API key is required")
        return OpenAIClient(config.openai_api_key, config.openai_org_id)
    elif provider == "anthropic":
        if not config.anthropic_api_key:
            raise ValueError("Anthropic API key is required")
        return AnthropicClient(config.anthropic_api_key)
    else:
        raise ValueError(f"Unsupported provider: {provider}") 