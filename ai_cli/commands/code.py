"""Code generation command for AI CLI."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.client import Message, get_client
from ..core.config import config
from ..core.utils import detect_language, format_code_output, setup_logging

app = typer.Typer(name="code", help="Generate code based on a prompt")

console = Console()


async def generate_code(
    prompt: str,
    model: str,
    provider: str,
    temperature: float,
    max_tokens: Optional[int],
    language: Optional[str] = None,
    output_file: Optional[str] = None,
) -> None:
    """Generate code based on a prompt."""
    try:
        client = get_client(provider)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Please set up your API keys in the .env file[/yellow]")
        return
    
    # Create system prompt for code generation
    system_prompt = "You are an expert programmer. Generate clean, well-documented, and efficient code. "
    if language:
        system_prompt += f"Write the code in {language}. "
    system_prompt += "Include comments explaining complex logic and provide a brief explanation of what the code does."
    
    # Prepare messages
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=prompt)
    ]
    
    # Show the prompt
    console.print(Panel(f"[bold blue]Prompt:[/bold blue]\n{prompt}", title="[bold green]AI CLI Code Generation[/bold green]"))
    if language:
        console.print(f"[dim]Language: {language}[/dim]")
    console.print("\n[dim]Generating code...[/dim]\n")
    
    try:
        response = await client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Detect language from response if not specified
        detected_lang = language or detect_language(response.content)
        
        # Show the generated code
        console.print(Panel(
            f"[bold blue]Generated Code:[/bold blue]",
            title=f"[bold green]Code ({detected_lang.upper()})[/bold green]"
        ))
        
        format_code_output(response.content, detected_lang)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(response.content)
                console.print(f"\n[green]Code saved to: {output_file}[/green]")
            except Exception as e:
                console.print(f"[red]Failed to save code to file: {e}[/red]")
        
        # Show usage information if available
        if response.usage:
            usage = response.usage
            console.print(f"\n[dim]Usage: {usage.get('prompt_tokens', 0)} prompt tokens, "
                         f"{usage.get('completion_tokens', 0)} completion tokens, "
                         f"{usage.get('total_tokens', 0)} total tokens[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error generating code: {e}[/red]")


@app.command()
def main(
    prompt: str = typer.Argument(..., help="The code generation prompt"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Programming language to use"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider to use"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Temperature for responses (0.0-2.0)"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Maximum tokens for response"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file to save the generated code"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
) -> None:
    """Generate code based on a prompt."""
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
    
    # Validate output file
    if output:
        output_path = Path(output)
        if output_path.exists():
            console.print(f"[yellow]Warning: Output file {output} already exists and will be overwritten[/yellow]")
    
    # Validate configuration
    try:
        config.validate_api_keys()
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        raise typer.Exit(1)
    
    # Generate code
    asyncio.run(generate_code(
        prompt=prompt,
        model=model,
        provider=provider,
        temperature=temperature,
        max_tokens=max_tokens,
        language=language,
        output_file=output,
    ))


if __name__ == "__main__":
    app() 