"""Main CLI application."""

import sys
import argparse
from typing import Optional

import typer
from rich.console import Console

from .commands import ask, chat, code, config, edit, explain, bash, web
from .commands.ai_langgraph import main as ai_langgraph_main

app = typer.Typer(
    name="ai-cli",
    help="A powerful AI-powered command-line interface tool",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print("[bold blue]ai-cli[/bold blue] version [bold green]0.1.0[/bold green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, help="Show version and exit"
    ),
):
    """AI CLI - A powerful AI-powered command-line interface tool."""
    pass


# Register commands
app.command("ask")(ask.main)
app.command("chat")(chat.start)
app.command("code")(code.main)
app.command("explain")(explain.main)
app.add_typer(config.app, name="config", help="Manage configuration settings")
app.add_typer(edit.app, name="edit", help="Edit text files")
app.add_typer(bash.app, name="bash", help="Execute bash commands")
app.add_typer(web.app, name="web", help="Web tools for searching, summarizing, and reading content")


def main_cli():
    """Main CLI entry point with AI as default."""
    # Check if first argument is a known command or option
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        
        # Known commands and options
        known_commands = {
            "ask", "chat", "code", "explain", "config", "edit", "bash", "web",
            "--help", "-h", "--version", "-v"
        }
        
        # Check if it's a known command/option
        if first_arg in known_commands or first_arg.startswith("--") or first_arg.startswith("-"):
            # Normal command execution
            app()
        else:
            # Treat as AI prompt
            parser = argparse.ArgumentParser(add_help=False)
            parser.add_argument("--model", type=str, help="AI model to use")
            parser.add_argument("--provider", type=str, help="AI provider (openai/anthropic)")
            parser.add_argument("--temperature", type=float, help="AI temperature")
            parser.add_argument("--max-tokens", type=int, help="Maximum tokens")
            
            # Parse known args, ignore unknown
            args, unknown = parser.parse_known_args()
            
            # Get the prompt (first argument)
            prompt = first_arg
            
            # Convert args to kwargs for ai_langgraph_main
            kwargs = {}
            if args.model:
                kwargs["model"] = args.model
            if args.provider:
                kwargs["provider"] = args.provider
            if args.temperature:
                kwargs["temperature"] = args.temperature
            if args.max_tokens:
                kwargs["max_tokens"] = args.max_tokens
            
            # Call AI function
            ai_langgraph_main(prompt, **kwargs)
    else:
        # No arguments, show help
        app()


if __name__ == "__main__":
    main_cli() 