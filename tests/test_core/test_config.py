"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_cli.core.config import Config


class TestConfig:
    """Test configuration management."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.default_provider == "openai"
        assert config.default_model == "gpt-4"
        assert config.default_temperature == 0.7
        assert config.default_max_tokens == 4000
        assert config.enable_syntax_highlighting is True
        assert config.enable_markdown_rendering is True
        assert config.enable_cache is True
    
    def test_config_from_env(self):
        """Test configuration from environment variables."""
        env_vars = {
            "OPENAI_API_KEY": "test_openai_key",
            "ANTHROPIC_API_KEY": "test_anthropic_key",
            "DEFAULT_PROVIDER": "anthropic",
            "DEFAULT_MODEL": "claude-3-sonnet",
            "DEFAULT_TEMPERATURE": "0.5",
            "DEFAULT_MAX_TOKENS": "2000",
        }
        
        with patch.dict(os.environ, env_vars):
            config = Config.from_env()
            
            assert config.openai_api_key == "test_openai_key"
            assert config.anthropic_api_key == "test_anthropic_key"
            assert config.default_provider == "anthropic"
            assert config.default_model == "claude-3-sonnet"
            assert config.default_temperature == 0.5
            assert config.default_max_tokens == 2000
    
    def test_validate_api_keys_openai(self):
        """Test API key validation for OpenAI."""
        config = Config(default_provider="openai", openai_api_key="test_key")
        config.validate_api_keys()  # Should not raise
    
    def test_validate_api_keys_anthropic(self):
        """Test API key validation for Anthropic."""
        config = Config(default_provider="anthropic", anthropic_api_key="test_key")
        config.validate_api_keys()  # Should not raise
    
    def test_validate_api_keys_missing_openai(self):
        """Test API key validation with missing OpenAI key."""
        config = Config(default_provider="openai", openai_api_key=None)
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            config.validate_api_keys()
    
    def test_validate_api_keys_missing_anthropic(self):
        """Test API key validation with missing Anthropic key."""
        config = Config(default_provider="anthropic", anthropic_api_key=None)
        with pytest.raises(ValueError, match="Anthropic API key is required"):
            config.validate_api_keys()
    
    def test_get_cache_path(self):
        """Test cache path generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(cache_dir=temp_dir)
            cache_path = config.get_cache_path()
            
            assert isinstance(cache_path, Path)
            assert cache_path == Path(temp_dir)
            assert cache_path.exists()
    
    def test_get_cache_path_relative(self):
        """Test cache path generation with relative path."""
        config = Config(cache_dir="test_cache")
        cache_path = config.get_cache_path()
        
        assert isinstance(cache_path, Path)
        assert cache_path.name == "test_cache"
        assert cache_path.is_absolute() 