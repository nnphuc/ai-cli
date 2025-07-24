"""Interactive chat command for AI CLI."""

import asyncio
from typing import List, Optional

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel

from ..core.client import Message, get_client
from ..core.config import config
from ..core.utils import format_chat_message, setup_logging

app = typer.Typer(name="chat", help="Start an interactive chat session")

console = Console()

# Command suggestions for autocomplete
COMMANDS = [
    "/help", "/clear", "/exit", "/quit", "/save", "/load", "/model", "/provider", "/temperature"
]

# Create prompt session with history
session = PromptSession(
    history=FileHistory('.chat_history'),
    completer=WordCompleter(COMMANDS),
    style=Style.from_dict({
        'prompt': 'ansicyan bold',
    })
)


def show_help() -> None:
    """Show help information."""
    help_text = """
[bold]Available Commands:[/bold]
• /help - Show this help message
• /clear - Clear the chat history
• /exit, /quit - Exit the chat session
• /save <filename> - Save chat history to file
• /load <filename> - Load chat history from file
• /model <model> - Change the AI model
• /provider <provider> - Change the AI provider
• /temperature <value> - Set temperature (0.0-2.0)

[bold]Usage:[/bold]
Just type your message and press Enter to chat with the AI.
Type a command starting with / to execute special commands.
    """
    console.print(Panel(help_text, title="[bold blue]Chat Help[/bold blue]"))


def show_welcome() -> None:
    """Show welcome message."""
    welcome_text = f"""
[bold green]Welcome to AI CLI Chat![/bold green]

[dim]Current settings:[/dim]
• Provider: {config.default_provider}
• Model: {config.default_model}
• Temperature: {config.default_temperature}

Type your message to start chatting, or type /help for available commands.
Type /exit to quit.
    """
    console.print(Panel(welcome_text, title="[bold blue]AI CLI Chat[/bold blue]"))


async def process_command(command: str, messages: List[Message], current_model: str, current_provider: str, current_temperature: float) -> tuple[List[Message], str, str, float]:
    """Process chat commands."""
    parts = command.split()
    cmd = parts[0].lower()
    
    if cmd == "/help":
        show_help()
    elif cmd == "/clear":
        messages.clear()
        console.print("[green]Chat history cleared[/green]")
    elif cmd == "/exit" or cmd == "/quit":
        console.print("[yellow]Goodbye![/yellow]")
        raise typer.Exit()
    elif cmd == "/save" and len(parts) > 1:
        filename = parts[1]
        try:
            with open(filename, 'w') as f:
                for msg in messages:
                    f.write(f"{msg.role}: {msg.content}\n\n")
            console.print(f"[green]Chat history saved to {filename}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to save chat history: {e}[/red]")
    elif cmd == "/load" and len(parts) > 1:
        filename = parts[1]
        try:
            messages.clear()
            with open(filename, 'r') as f:
                content = f.read()
                # Simple parsing - could be improved
                for line in content.split('\n'):
                    if line.strip() and ':' in line:
                        role, msg_content = line.split(':', 1)
                        messages.append(Message(role=role.strip(), content=msg_content.strip()))
            console.print(f"[green]Chat history loaded from {filename}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to load chat history: {e}[/red]")
    elif cmd == "/model" and len(parts) > 1:
        current_model = parts[1]
        console.print(f"[green]Model changed to: {current_model}[/green]")
    elif cmd == "/provider" and len(parts) > 1:
        current_provider = parts[1]
        console.print(f"[green]Provider changed to: {current_provider}[/green]")
    elif cmd == "/temperature" and len(parts) > 1:
        try:
            current_temperature = float(parts[1])
            if 0.0 <= current_temperature <= 2.0:
                console.print(f"[green]Temperature changed to: {current_temperature}[/green]")
            else:
                console.print("[red]Temperature must be between 0.0 and 2.0[/red]")
        except ValueError:
            console.print("[red]Invalid temperature value[/red]")
    else:
        console.print(f"[red]Unknown command: {cmd}[/red]")
    
    return messages, current_model, current_provider, current_temperature


async def chat_loop() -> None:
    """Main chat loop."""
    messages: List[Message] = []
    current_model = config.default_model
    current_provider = config.default_provider
    current_temperature = config.default_temperature
    
    show_welcome()
    
    try:
        client = get_client(current_provider)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Please set up your API keys in the .env file[/yellow]")
        return
    
    while True:
        try:
            # Get user input
            user_input = await session.prompt_async("You: ")
            
            if not user_input.strip():
                continue
            
            # Check if it's a command
            if user_input.startswith('/'):
                messages, current_model, current_provider, current_temperature = await process_command(
                    user_input, messages, current_model, current_provider, current_temperature
                )
                continue
            
            # Add user message to history
            messages.append(Message(role="user", content=user_input))
            
            # Show user message
            format_chat_message("user", user_input)
            
            # Get AI response
            console.print("\n[dim]AI is thinking...[/dim]")
            
            try:
                response = await client.chat_completion(
                    messages=messages,
                    model=current_model,
                    temperature=current_temperature,
                    max_tokens=config.default_max_tokens
                )
                
                # Add AI response to history
                messages.append(Message(role="assistant", content=response.content))
                
                # Show AI response
                console.print()
                format_chat_message("assistant", response.content)
                console.print()
                
            except Exception as e:
                console.print(f"[red]Error getting AI response: {e}[/red]")
                # Remove the user message from history on error
                if messages:
                    messages.pop()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use /exit to quit the chat[/yellow]")
        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break


@app.command()
def start(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider to use"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Temperature for responses (0.0-2.0)"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
) -> None:
    """Start an interactive chat session with the AI."""
    # Setup logging
    setup_logging(
        level="DEBUG" if verbose else config.log_level,
        log_file=config.log_file
    )
    
    # Override defaults if provided
    if model:
        config.default_model = model
    if provider:
        config.default_provider = provider
    if temperature is not None:
        if 0.0 <= temperature <= 2.0:
            config.default_temperature = temperature
        else:
            console.print("[red]Temperature must be between 0.0 and 2.0[/red]")
            raise typer.Exit(1)
    
    # Validate configuration
    try:
        config.validate_api_keys()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)
    
    # Start chat loop
    asyncio.run(chat_loop())


if __name__ == "__main__":
    app() 