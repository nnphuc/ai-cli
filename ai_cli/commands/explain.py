"""Code explanation command for AI CLI."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.client import Message, get_client
from ..core.config import config
from ..core.utils import detect_language, format_code_output, setup_logging

app = typer.Typer(name="explain", help="Explain the given code")

console = Console()


async def explain_code(
    code: str,
    model: str,
    provider: str,
    temperature: float,
    max_tokens: Optional[int],
    language: Optional[str] = None,
    detail_level: str = "normal",
) -> None:
    """Explain the given code."""
    try:
        client = get_client(provider)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Please set up your API keys in the .env file[/yellow]")
        return
    
    # Detect language if not provided
    detected_lang = language or detect_language(code)
    
    # Create system prompt for code explanation
    detail_prompts = {
        "brief": "Provide a brief, high-level explanation of what this code does.",
        "normal": "Explain what this code does, how it works, and any important concepts or patterns used.",
        "detailed": "Provide a detailed explanation including line-by-line analysis, algorithms used, time complexity, and potential improvements."
    }
    
    detail_prompt = detail_prompts.get(detail_level, detail_prompts["normal"])
    
    system_prompt = f"You are an expert programmer. {detail_prompt} "
    system_prompt += f"The code is written in {detected_lang}. "
    system_prompt += "Be clear, concise, and educational in your explanation."
    
    # Prepare messages
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=f"Please explain this {detected_lang} code:\n\n{code}")
    ]
    
    # Show the code
    console.print(Panel(
        f"[bold blue]Code to Explain:[/bold blue]",
        title=f"[bold green]AI CLI Code Explanation ({detected_lang.upper()})[/bold green]"
    ))
    format_code_output(code, detected_lang)
    console.print(f"\n[dim]Detail level: {detail_level}[/dim]")
    console.print("\n[dim]Generating explanation...[/dim]\n")
    
    try:
        response = await client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Show the explanation
        console.print(Panel(
            f"[bold blue]Explanation:[/bold blue]\n{response.content}",
            title=f"[bold green]Code Explanation[/bold green]"
        ))
        
        # Show usage information if available
        if response.usage:
            usage = response.usage
            console.print(f"\n[dim]Usage: {usage.get('prompt_tokens', 0)} prompt tokens, "
                         f"{usage.get('completion_tokens', 0)} completion tokens, "
                         f"{usage.get('total_tokens', 0)} total tokens[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error explaining code: {e}[/red]")


def read_code_from_file(file_path: str) -> str:
    """Read code from a file."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        raise typer.BadParameter(f"Failed to read file {file_path}: {e}")


@app.command()
def main(
    code: str = typer.Argument(..., help="The code to explain (or file path starting with @)"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Programming language of the code"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider to use"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Temperature for responses (0.0-2.0)"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Maximum tokens for response"),
    detail: str = typer.Option("normal", "--detail", "-d", help="Detail level: brief, normal, or detailed"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
) -> None:
    """Explain the given code."""
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
    
    # Validate detail level
    if detail not in ["brief", "normal", "detailed"]:
        console.print("[red]Detail level must be one of: brief, normal, detailed[/red]")
        raise typer.Exit(1)
    
    # Check if code is a file path
    if code.startswith('@'):
        file_path = code[1:]
        try:
            code_content = read_code_from_file(file_path)
        except Exception as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)
    else:
        code_content = code
    
    # Validate configuration
    try:
        config.validate_api_keys()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)
    
    # Explain the code
    asyncio.run(explain_code(
        code=code_content,
        model=model,
        provider=provider,
        temperature=temperature,
        max_tokens=max_tokens,
        language=language,
        detail_level=detail,
    ))


if __name__ == "__main__":
    app() 