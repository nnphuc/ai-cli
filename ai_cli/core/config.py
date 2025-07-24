"""Configuration management for AI CLI."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()


class Config(BaseModel):
    """Configuration settings for AI CLI."""
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_org_id: Optional[str] = Field(default=None, description="OpenAI organization ID")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Default Settings
    default_provider: str = Field(default="openai", description="Default AI provider")
    default_model: str = Field(default="gpt-4", description="Default AI model")
    default_temperature: float = Field(default=0.7, description="Default temperature")
    default_max_tokens: int = Field(default=4000, description="Default max tokens")
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # UI Settings
    enable_syntax_highlighting: bool = Field(default=True, description="Enable syntax highlighting")
    enable_markdown_rendering: bool = Field(default=True, description="Enable markdown rendering")
    theme: str = Field(default="default", description="UI theme")
    
    # Cache Settings
    enable_cache: bool = Field(default=True, description="Enable caching")
    cache_dir: str = Field(default=".cache", description="Cache directory")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_org_id=os.getenv("OPENAI_ORG_ID"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            default_provider=os.getenv("DEFAULT_PROVIDER", "openai"),
            default_model=os.getenv("DEFAULT_MODEL", "gpt-4"),
            default_temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
            default_max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "4000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE"),
            enable_syntax_highlighting=os.getenv("ENABLE_SYNTAX_HIGHLIGHTING", "true").lower() == "true",
            enable_markdown_rendering=os.getenv("ENABLE_MARKDOWN_RENDERING", "true").lower() == "true",
            theme=os.getenv("THEME", "default"),
            enable_cache=os.getenv("ENABLE_CACHE", "true").lower() == "true",
            cache_dir=os.getenv("CACHE_DIR", ".cache"),
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
        )
    
    def validate_api_keys(self) -> None:
        """Validate that required API keys are present."""
        if self.default_provider == "openai" and not self.openai_api_key:
            raise ValueError("OpenAI API key is required when using OpenAI as default provider")
        elif self.default_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("Anthropic API key is required when using Anthropic as default provider")
    
    def get_cache_path(self) -> Path:
        """Get the cache directory path."""
        cache_path = Path(self.cache_dir)
        if not cache_path.is_absolute():
            cache_path = Path.cwd() / cache_path
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path


# Global configuration instance
config = Config.from_env() 