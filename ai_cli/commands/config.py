"""Configuration management command for AI CLI."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.config import config
from ..core.utils import clear_cache, setup_logging

app = typer.Typer(name="config", help="Manage configuration settings")

console = Console()


def show_current_config() -> None:
    """Display current configuration."""
    table = Table(title="[bold blue]Current Configuration[/bold blue]")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_column("Description", style="dim")
    
    # API Keys (masked)
    openai_key = config.openai_api_key
    anthropic_key = config.anthropic_api_key
    
    table.add_row(
        "OpenAI API Key",
        "***" + openai_key[-4:] if openai_key else "Not set",
        "OpenAI API key for GPT models"
    )
    table.add_row(
        "Anthropic API Key",
        "***" + anthropic_key[-4:] if anthropic_key else "Not set",
        "Anthropic API key for Claude models"
    )
    table.add_row("", "", "")  # Empty row for spacing
    
    # Default Settings
    table.add_row("Default Provider", config.default_provider, "Default AI provider")
    table.add_row("Default Model", config.default_model, "Default AI model")
    table.add_row("Default Temperature", str(config.default_temperature), "Default temperature (0.0-2.0)")
    table.add_row("Default Max Tokens", str(config.default_max_tokens), "Default maximum tokens")
    table.add_row("", "", "")  # Empty row for spacing
    
    # UI Settings
    table.add_row("Syntax Highlighting", str(config.enable_syntax_highlighting), "Enable syntax highlighting")
    table.add_row("Markdown Rendering", str(config.enable_markdown_rendering), "Enable markdown rendering")
    table.add_row("Theme", config.theme, "UI theme")
    table.add_row("", "", "")  # Empty row for spacing
    
    # Cache Settings
    table.add_row("Cache Enabled", str(config.enable_cache), "Enable response caching")
    table.add_row("Cache Directory", config.cache_dir, "Cache directory path")
    table.add_row("Cache TTL", f"{config.cache_ttl}s", "Cache time-to-live")
    table.add_row("", "", "")  # Empty row for spacing
    
    # Logging
    table.add_row("Log Level", config.log_level, "Logging level")
    table.add_row("Log File", config.log_file or "Not set", "Log file path")
    
    console.print(table)


def show_available_models() -> None:
    """Show available models for each provider."""
    models_table = Table(title="[bold blue]Available Models[/bold blue]")
    models_table.add_column("Provider", style="cyan", no_wrap=True)
    models_table.add_column("Models", style="green")
    models_table.add_column("Description", style="dim")
    
    # OpenAI Models
    openai_models = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k"
    ]
    models_table.add_row(
        "OpenAI",
        "\n".join(openai_models),
        "GPT models for text generation and chat"
    )
    
    # Anthropic Models
    anthropic_models = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307"
    ]
    models_table.add_row(
        "Anthropic",
        "\n".join(anthropic_models),
        "Claude models for text generation and chat"
    )
    
    console.print(models_table)


def export_config(output_file: str) -> None:
    """Export configuration to a JSON file."""
    try:
        # Create a safe config dict (without API keys)
        safe_config = {
            "default_provider": config.default_provider,
            "default_model": config.default_model,
            "default_temperature": config.default_temperature,
            "default_max_tokens": config.default_max_tokens,
            "log_level": config.log_level,
            "log_file": config.log_file,
            "enable_syntax_highlighting": config.enable_syntax_highlighting,
            "enable_markdown_rendering": config.enable_markdown_rendering,
            "theme": config.theme,
            "enable_cache": config.enable_cache,
            "cache_dir": config.cache_dir,
            "cache_ttl": config.cache_ttl,
        }
        
        with open(output_file, 'w') as f:
            json.dump(safe_config, f, indent=2)
        
        console.print(f"[green]Configuration exported to: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to export configuration: {e}[/red]")


def import_config(input_file: str) -> None:
    """Import configuration from a JSON file."""
    try:
        with open(input_file, 'r') as f:
            imported_config = json.load(f)
        
        # Update config with imported values
        for key, value in imported_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        console.print(f"[green]Configuration imported from: {input_file}[/green]")
        console.print("[yellow]Note: API keys are not imported for security reasons[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Failed to import configuration: {e}[/red]")


def show_cache_info() -> None:
    """Show cache information."""
    cache_dir = Path(config.cache_dir)
    
    if not cache_dir.exists():
        console.print("[yellow]Cache directory does not exist[/yellow]")
        return
    
    cache_files = list(cache_dir.glob("*.json"))
    total_size = sum(f.stat().st_size for f in cache_files)
    
    cache_table = Table(title="[bold blue]Cache Information[/bold blue]")
    cache_table.add_column("Metric", style="cyan", no_wrap=True)
    cache_table.add_column("Value", style="green")
    
    cache_table.add_row("Cache Directory", str(cache_dir.absolute()))
    cache_table.add_row("Cache Enabled", str(config.enable_cache))
    cache_table.add_row("Number of Files", str(len(cache_files)))
    cache_table.add_row("Total Size", f"{total_size / 1024:.2f} KB")
    cache_table.add_row("TTL", f"{config.cache_ttl} seconds")
    
    console.print(cache_table)


@app.command()
def show() -> None:
    """Show current configuration."""
    show_current_config()


@app.command()
def models() -> None:
    """Show available models for each provider."""
    show_available_models()


@app.command()
def export(
    output: str = typer.Argument(..., help="Output file path for configuration export")
) -> None:
    """Export configuration to a JSON file."""
    export_config(output)


@app.command()
def import_config_cmd(
    input_file: str = typer.Argument(..., help="Input file path for configuration import")
) -> None:
    """Import configuration from a JSON file."""
    import_config(input_file)


@app.command()
def cache() -> None:
    """Show cache information."""
    show_cache_info()


@app.command()
def clear_cache_cmd() -> None:
    """Clear the cache."""
    clear_cache()


@app.command()
def validate() -> None:
    """Validate current configuration."""
    try:
        config.validate_api_keys()
        console.print("[green]✓ Configuration is valid[/green]")
        
        # Check if cache directory is writable
        cache_dir = Path(config.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        test_file = cache_dir / "test.txt"
        test_file.write_text("test")
        test_file.unlink()
        console.print("[green]✓ Cache directory is writable[/green]")
        
    except ValueError as e:
        console.print(f"[red]✗ Configuration error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Cache directory error: {e}[/red]")


if __name__ == "__main__":
    app() 