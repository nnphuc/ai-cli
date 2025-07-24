"""Main CLI entry point for AI CLI."""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.traceback import install

from .commands import ask, chat, code, config, edit, explain, bash
from .core.config import Config

# Install rich traceback handler
install(show_locals=True)

# Create Typer app
app = typer.Typer(
    name="ai-cli",
    help="A powerful AI-powered command line interface tool",
    add_completion=False,
    rich_markup_mode="rich",
)

# Create console for rich output
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from . import __version__
        console.print(f"[bold blue]AI CLI[/bold blue] version [bold green]{__version__}[/bold green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose output",
    ),
) -> None:
    """AI CLI - A powerful AI-powered command line interface tool."""
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")




# Add other commands
app.command("chat")(chat.start)
app.command("ask")(ask.main)
app.command("code")(code.main)
app.command("explain")(explain.main)
app.add_typer(bash.app, name="bash", help="Execute bash commands")
app.add_typer(edit.app, name="edit", help="Edit text files")
app.add_typer(config.app, name="config", help="Manage configuration settings")


def main_cli() -> None:
    """Main CLI function."""
    try:
        # Check if arguments are provided and if the first argument is not a known command
        import sys
        args = sys.argv[1:] if len(sys.argv) > 1 else []
        
        # Known commands that should not be treated as AI prompts
        known_commands = {
            "chat", "ask", "code", "explain", "bash", "edit", "config", 
            "--help", "-h", "--version", "-v", "--verbose"
        }
        
        # If first argument is not a known command and not an option, treat as AI prompt
        if args and not args[0].startswith("-") and args[0] not in known_commands:
            # Treat as AI prompt
            from .commands.ai_langgraph import main as ai_main
            # Parse remaining arguments for options
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("--model", "-m")
            parser.add_argument("--provider", "-p")
            parser.add_argument("--temperature", "-t", type=float)
            parser.add_argument("--verbose", action="store_true")
            parser.add_argument("--force-tool")
            
            # Extract the prompt and remaining args
            prompt = args[0]
            remaining_args = args[1:]
            
            # Parse options
            parsed_args, _ = parser.parse_known_args(remaining_args)
            
            ai_main(
                prompt=prompt,
                model=parsed_args.model,
                provider=parsed_args.provider,
                temperature=parsed_args.temperature,
                verbose=parsed_args.verbose,
                force_tool=parsed_args.force_tool
            )
        else:
            # Normal command execution
            app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        if console.is_interactive:
            console.print_exception()
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main_cli() 