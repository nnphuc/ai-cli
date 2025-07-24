"""Utility functions for AI CLI."""

import logging
import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text

from .config import config

console = Console()


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """Setup logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=format_string,
        handlers=[]
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(format_string))
    logging.getLogger().addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(format_string))
        logging.getLogger().addHandler(file_handler)


def get_cache_dir() -> Path:
    """Get the cache directory path."""
    return config.get_cache_path()


def clear_cache() -> None:
    """Clear the cache directory."""
    cache_dir = get_cache_dir()
    if cache_dir.exists():
        for cache_file in cache_dir.glob("*.json"):
            cache_file.unlink()
        console.print("[green]Cache cleared successfully[/green]")


def detect_language(text: str) -> str:
    """Detect the programming language from code text."""
    # Simple language detection based on common patterns
    text_lower = text.lower().strip()
    
    if text_lower.startswith(("def ", "import ", "from ", "class ", "if __name__")):
        return "python"
    elif text_lower.startswith(("function ", "const ", "let ", "var ", "console.log")):
        return "javascript"
    elif text_lower.startswith(("public class", "private ", "public ", "import java")):
        return "java"
    elif text_lower.startswith(("package ", "import ", "func ")):
        return "go"
    elif text_lower.startswith(("fn ", "let ", "use ", "pub ")):
        return "rust"
    elif text_lower.startswith(("<?php", "function ", "$")):
        return "php"
    elif text_lower.startswith(("def ", "module ", "require ")):
        return "ruby"
    elif text_lower.startswith(("using ", "namespace ", "public class")):
        return "csharp"
    elif text_lower.startswith(("#include", "int main", "void ")):
        return "c"
    elif text_lower.startswith(("#include", "int main", "void ")):
        return "cpp"
    elif text_lower.startswith(("html", "<!doctype", "<html")):
        return "html"
    elif text_lower.startswith(("sql", "select ", "insert ", "update ")):
        return "sql"
    elif text_lower.startswith(("dockerfile", "from ", "run ")):
        return "dockerfile"
    elif text_lower.startswith(("yaml", "---", "- ")):
        return "yaml"
    elif text_lower.startswith(("{", "}", '"')) and ("name" in text_lower or "age" in text_lower or "city" in text_lower):
        return "json"
    elif "{" in text_lower and "}" in text_lower and ("font-family" in text_lower or "margin" in text_lower or "padding" in text_lower):
        return "css"
    else:
        return "text"


def format_code_output(content: str, language: Optional[str] = None) -> None:
    """Format and display code output with syntax highlighting."""
    if not content:
        return
    
    # Detect language if not provided
    if not language:
        language = detect_language(content)
    
    # Check if content looks like code
    if language in ["python", "javascript", "java", "go", "rust", "php", "ruby", "csharp", "c", "cpp", "html", "css", "sql", "dockerfile", "yaml", "json"]:
        # Format as syntax-highlighted code
        syntax = Syntax(content, language, theme="monokai", line_numbers=True)
        console.print(syntax)
    else:
        # Format as markdown if enabled
        if config.enable_markdown_rendering:
            try:
                markdown = Markdown(content)
                console.print(markdown)
            except Exception:
                # Fallback to plain text
                console.print(content)
        else:
            console.print(content)


def format_chat_message(role: str, content: str, show_role: bool = True) -> None:
    """Format and display a chat message."""
    if show_role:
        role_text = Text(f"[{role.upper()}]", style="bold blue")
        console.print(role_text)
    
    format_code_output(content)


def get_terminal_size() -> tuple[int, int]:
    """Get terminal size (width, height)."""
    try:
        return os.get_terminal_size()
    except OSError:
        return (80, 24)  # Default fallback


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    path.mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return Path(filename).suffix.lower()


def is_binary_file(file_path: Path) -> bool:
    """Check if file is binary."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except Exception:
        return False 