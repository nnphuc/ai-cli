"""AI CLI - A powerful AI-powered command line interface tool."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.config import Config
from .core.client import AIClient

__all__ = ["Config", "AIClient"] 