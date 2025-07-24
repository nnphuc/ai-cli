"""AI command that intelligently decides which tool to use based on natural language prompts."""

import asyncio
import re
from typing import Dict, List, Optional, Tuple

import typer
from rich.console import Console
from rich.panel import Panel

from ..core.client import Message, get_client
from ..core.config import config
from ..core.utils import setup_logging

app = typer.Typer(name="ai", help="AI-powered command that decides which tool to use")

console = Console()

# Tool definitions with descriptions and patterns
TOOLS = {
    "ask": {
        "description": "Ask a single question to the AI",
        "patterns": [
            r"ask\s+(.+)$",
            r"what\s+(.+)$",
            r"how\s+(.+)$",
            r"why\s+(.+)$",
            r"when\s+(.+)$",
            r"where\s+(.+)$",
            r"who\s+(.+)$",
            r"question[:\s]+(.+)$",
            r"tell\s+me\s+(.+)$",
            r"explain\s+(.+)$",
        ],
        "command": "ask",
        "args": ["question"]
    },
    "code": {
        "description": "Generate code based on a prompt",
        "patterns": [
            r"generate\s+code\s+(.+)$",
            r"write\s+code\s+(.+)$",
            r"create\s+code\s+(.+)$",
            r"code\s+(.+)$",
            r"program\s+(.+)$",
            r"function\s+(.+)$",
            r"class\s+(.+)$",
            r"script\s+(.+)$",
            r"algorithm\s+(.+)$",
            r"implement\s+(.+)$",
        ],
        "command": "code",
        "args": ["prompt"]
    },
    "explain": {
        "description": "Explain the given code",
        "patterns": [
            r"explain\s+code\s+(.+)$",
            r"what\s+does\s+this\s+code\s+do[:\s]+(.+)$",
            r"how\s+does\s+this\s+work[:\s]+(.+)$",
            r"break\s+down\s+this\s+code[:\s]+(.+)$",
            r"analyze\s+this\s+code[:\s]+(.+)$",
            r"understand\s+this\s+code[:\s]+(.+)$",
            r"code\s+explanation[:\s]+(.+)$",
        ],
        "command": "explain",
        "args": ["code"]
    },
    "edit_view": {
        "description": "View file content",
        "patterns": [
            r"view\s+file\s+(.+)$",
            r"show\s+file\s+(.+)$",
            r"display\s+file\s+(.+)$",
            r"read\s+file\s+(.+)$",
            r"open\s+file\s+(.+)$",
            r"cat\s+(.+)$",
            r"file\s+content[:\s]+(.+)$",
            r"view\s+(.+)$",
        ],
        "command": "edit view",
        "args": ["file_path"]
    },
    "edit_find": {
        "description": "Search for text in a file",
        "patterns": [
            r"find\s+(.+?)\s+in\s+(.+)$",
            r"search\s+(.+?)\s+in\s+(.+)$",
            r"grep\s+(.+?)\s+in\s+(.+)$",
            r"look\s+for\s+(.+?)\s+in\s+(.+)$",
            r"file\s+search[:\s]+(.+?)\s+in\s+(.+)$",
        ],
        "command": "edit find",
        "args": ["file_path", "pattern"]
    },
    "edit_replace": {
        "description": "Replace text in a file",
        "patterns": [
            r"replace\s+(.+?)\s+with\s+(.+?)\s+in\s+(.+)$",
            r"change\s+(.+?)\s+to\s+(.+?)\s+in\s+(.+)$",
            r"substitute\s+(.+?)\s+with\s+(.+?)\s+in\s+(.+)$",
            r"edit\s+file[:\s]+(.+?)\s+->\s+(.+?)\s+in\s+(.+)$",
        ],
        "command": "edit replace",
        "args": ["file_path", "pattern", "replacement"]
    },
    "edit_insert": {
        "description": "Insert text into a file",
        "patterns": [
            r"insert\s+(.+?)\s+into\s+(.+)$",
            r"add\s+(.+?)\s+to\s+(.+)$",
            r"append\s+(.+?)\s+to\s+(.+)$",
            r"put\s+(.+?)\s+in\s+(.+)$",
        ],
        "command": "edit insert",
        "args": ["file_path", "content"]
    },
    "edit_info": {
        "description": "Show file information",
        "patterns": [
            r"file\s+info[:\s]+(.+)$",
            r"info\s+about\s+file\s+(.+)$",
            r"file\s+stats[:\s]+(.+)$",
            r"file\s+details[:\s]+(.+)$",
            r"analyze\s+file\s+(.+)$",
        ],
        "command": "edit info",
        "args": ["file_path"]
    },
    "chat": {
        "description": "Start an interactive chat session",
        "patterns": [
            r"chat\s*$",
            r"start\s+chat\s*$",
            r"conversation\s*$",
            r"talk\s*$",
            r"interactive\s*$",
        ],
        "command": "chat",
        "args": []
    },
    "config_show": {
        "description": "Show configuration",
        "patterns": [
            r"config\s*$",
            r"settings\s*$",
            r"configuration\s*$",
            r"show\s+config\s*$",
            r"current\s+settings\s*$",
            r"show\s+configuration\s*$",
            r"display\s+config\s*$",
            r"display\s+settings\s*$",
        ],
        "command": "config show",
        "args": []
    },
    "bash": {
        "description": "Execute bash commands",
        "patterns": [
            r"run\s+(.+)$",
            r"execute\s+(.+)$",
            r"bash\s+(.+)$",
            r"shell\s+(.+)$",
            r"command\s+(.+)$",
            r"terminal\s+(.+)$",
            r"cmd\s+(.+)$",
            r"ls\s+(.+)$",
            r"pwd\s*$",
            r"echo\s+(.+)$",
        ],
        "command": "bash main",
        "args": ["command"]
    }
}


def parse_prompt(prompt: str) -> Tuple[str, List[str], float]:
    """
    Parse the prompt and determine which tool to use.
    Returns (tool_name, args, confidence_score)
    """
    prompt_lower = prompt.lower().strip()
    best_match = None
    best_confidence = 0.0
    best_args = []
    
    for tool_name, tool_info in TOOLS.items():
        for pattern in tool_info["patterns"]:
            match = re.match(pattern, prompt_lower)
            if match:
                # Calculate confidence based on pattern specificity and match quality
                confidence = len(pattern) / 100.0  # Simple confidence scoring
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = tool_name
                    best_args = list(match.groups())
                    break
    
    return best_match, best_args, best_confidence


async def ask_ai_for_tool_selection(prompt: str, model: str, provider: str, temperature: float) -> Tuple[str, List[str]]:
    """
    Ask the AI to help determine which tool to use for the given prompt.
    Returns (tool_name, args)
    """
    system_prompt = """You are an AI assistant that helps users choose the right tool for their task.

Available tools and their commands:
- ask: Ask a single question to the AI (command: ask)
- code: Generate code based on a prompt (command: code)
- explain: Explain the given code (command: explain)
- edit view: View file content (command: edit view)
- edit find: Search for text in a file (command: edit find)
- edit replace: Replace text in a file (command: edit replace)
- edit insert: Insert text into a file (command: edit insert)
- edit info: Show file information (command: edit info)
- chat: Start an interactive chat session (command: chat)
- config show: Show configuration (command: config show)
- bash main: Execute bash commands (command: bash main)

Respond with ONLY the tool name and arguments in this exact format:
TOOL: command_name
ARGS: arg1|arg2|arg3

For example:
TOOL: ask
ARGS: What is the capital of France?

TOOL: code
ARGS: Write a Python function to calculate fibonacci numbers

TOOL: edit find
ARGS: myfile.txt|hello

TOOL: config show
ARGS: 

IMPORTANT: Use the command name (not the tool description) and do not include quotes around arguments."""

    try:
        client = get_client(provider)
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Which tool should I use for: {prompt}")
        ]
        
        response = await client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=200
        )
        
        # Parse the AI response
        content = response.content.strip()
        tool_match = re.search(r"TOOL:\s*([^\n]+)", content)
        args_match = re.search(r"ARGS:\s*(.*)", content)
        
        if tool_match and args_match is not None:
            tool_name = tool_match.group(1).strip()
            # Remove "ARGS" from tool name if present (handle newlines)
            tool_name = tool_name.replace(" ARGS", "").replace("\nARGS", "").strip()
            args_str = args_match.group(1).strip()
            # Remove quotes and split by |
            args_str = args_str.strip('"\'')
            args = [arg.strip().strip('"\'') for arg in args_str.split('|') if arg.strip()]
            
            # Find the tool by command name and return the actual command
            for key, tool_info in TOOLS.items():
                if tool_info["command"] == tool_name:
                    return tool_info["command"], args
            
            # If not found, return the tool name as is
            return tool_name, args
        else:
            # Fallback to pattern matching
            return parse_prompt(prompt)[0], parse_prompt(prompt)[1]
            
    except Exception as e:
        console.print(f"[yellow]AI tool selection failed, using pattern matching: {e}[/yellow]")
        return parse_prompt(prompt)[0], parse_prompt(prompt)[1]


def execute_tool(tool_name: str, args: List[str]) -> None:
    """Execute the selected tool with the given arguments."""
    import subprocess
    import sys
    
    # Build the command
    cmd = ["ai-cli"] + tool_name.split() + args
    
    try:
        # Execute the command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        # Print output
        if result.stdout:
            console.print(result.stdout)
        if result.stderr:
            console.print(f"[red]{result.stderr}[/red]")
            
        if result.returncode != 0:
            console.print(f"[red]Command failed with exit code {result.returncode}[/red]")
            
    except Exception as e:
        console.print(f"[red]Error executing command: {e}[/red]")


@app.command()
def main(
    prompt: str = typer.Argument(..., help="Natural language description of what you want to do"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider to use"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Temperature for AI responses (0.0-2.0)"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
    force_tool: Optional[str] = typer.Option(None, "--force-tool", help="Force use of specific tool"),
) -> None:
    """AI-powered command that intelligently decides which tool to use."""
    # Setup logging
    setup_logging(
        level="DEBUG" if verbose else config.log_level,
        log_file=config.log_file
    )
    
    # Use defaults if not provided
    model = model or config.default_model
    provider = provider or config.default_provider
    temperature = temperature if temperature is not None else config.default_temperature
    
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
    
    # Show what we're doing
    console.print(Panel(
        f"[bold blue]Prompt:[/bold blue] {prompt}",
        title="[bold green]AI Tool Selection[/bold green]"
    ))
    
    if force_tool:
        # Use forced tool
        console.print(f"[yellow]Forcing tool: {force_tool}[/yellow]")
        tool_name = force_tool
        args = [prompt]  # Use prompt as argument
    else:
        # First try pattern matching
        pattern_tool, pattern_args, confidence = parse_prompt(prompt)
        
        if confidence > 0.5:
            # Pattern matching is confident enough
            tool_name = pattern_tool
            args = pattern_args
            console.print(f"[green]Pattern matching selected: {tool_name} (confidence: {confidence:.2f})[/green]")
        else:
            # Ask AI for tool selection
            console.print("[dim]Pattern matching uncertain, asking AI for tool selection...[/dim]")
            tool_name, args = asyncio.run(ask_ai_for_tool_selection(prompt, model, provider, temperature))
            console.print(f"[green]AI selected: {tool_name}[/green]")
    
    if not tool_name:
        console.print("[red]Could not determine which tool to use. Please be more specific.[/red]")
        console.print("\n[bold]Available tools:[/bold]")
        for tool, info in TOOLS.items():
            console.print(f"  • {tool}: {info['description']}")
        raise typer.Exit(1)
    
    # Execute the tool
    console.print(f"\n[bold]Executing: ai-cli {tool_name} {' '.join(args)}[/bold]\n")
    execute_tool(tool_name, args)


if __name__ == "__main__":
    app() 