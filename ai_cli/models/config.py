"""Configuration models for AI CLI."""

from typing import Optional

from pydantic import BaseModel, Field


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