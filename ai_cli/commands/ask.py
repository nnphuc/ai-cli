"""Ask command for single question interactions."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.client import Message, get_client
from ..core.config import config
from ..core.utils import format_code_output, setup_logging

app = typer.Typer(name="ask", help="Ask a single question")

console = Console()


async def ask_question(
    question: str,
    model: str,
    provider: str,
    temperature: float,
    max_tokens: Optional[int],
    system_prompt: Optional[str] = None,
) -> None:
    """Ask a single question to the AI."""
    try:
        client = get_client(provider)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Please set up your API keys in the .env file[/yellow]")
        return
    
    # Prepare messages
    messages = []
    if system_prompt:
        messages.append(Message(role="system", content=system_prompt))
    messages.append(Message(role="user", content=question))
    
    # Show the question
    console.print(Panel(f"[bold blue]Question:[/bold blue]\n{question}", title="[bold green]AI CLI Ask[/bold green]"))
    console.print("\n[dim]AI is thinking...[/dim]\n")
    
    try:
        response = await client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Show the response
        console.print(Panel(
            f"[bold blue]Answer:[/bold blue]\n{response.content}",
            title=f"[bold green]Response (Model: {response.model})[/bold green]"
        ))
        
        # Show usage information if available
        if response.usage:
            usage = response.usage
            console.print(f"\n[dim]Usage: {usage.get('prompt_tokens', 0)} prompt tokens, "
                         f"{usage.get('completion_tokens', 0)} completion tokens, "
                         f"{usage.get('total_tokens', 0)} total tokens[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error getting AI response: {e}[/red]")


@app.command()
def main(
    question: str = typer.Argument(..., help="The question to ask"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider to use"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Temperature for responses (0.0-2.0)"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Maximum tokens for response"),
    system_prompt: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt to use"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
) -> None:
    """Ask a single question to the AI."""
    # Setup logging
    setup_logging(
        level="DEBUG" if verbose else config.log_level,
        log_file=config.log_file
    )
    
    # Use defaults if not provided
    model = model or config.default_model
    provider = provider or config.default_provider
    temperature = temperature if temperature is not None else config.default_temperature
    max_tokens = max_tokens or config.default_max_tokens
    
    # Validate temperature
    if not 0.0 <= temperature <= 2.0:
        console.print("[red]Temperature must be between 0.0 and 2.0[/red]")
        raise typer.Exit(1)
    
    # Validate configuration
    try:
        config.validate_api_keys()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)
    
    # Ask the question
    asyncio.run(ask_question(
        question=question,
        model=model,
        provider=provider,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
    ))


if __name__ == "__main__":
    app() 