"""
AI command implementation using LangGraph for structured tool selection and argument parsing.
"""

import asyncio
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import typer

from langgraph.graph import END, StateGraph
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
        "patterns": [],
        "command": "ask",
        "args": ["question"]
    },
    "code": {
        "description": "Generate code based on a prompt",
        "patterns": [],
        "command": "code",
        "args": ["prompt"]
    },
    "explain": {
        "description": "Explain the given code",
        "patterns": [],
        "command": "explain",
        "args": ["code"]
    },
    "edit_view": {
        "description": "View file content",
        "patterns": [],
        "command": "edit view",
        "args": ["file_path"]
    },
    "edit_find": {
        "description": "Search for text in a file",
        "patterns": [],
        "command": "edit find",
        "args": ["file_path", "pattern"]
    },
    "edit_replace": {
        "description": "Replace text in a file",
        "patterns": [],
        "command": "edit replace",
        "args": ["file_path", "pattern", "replacement"]
    },
    "edit_insert": {
        "description": "Insert text into a file",
        "patterns": [],
        "command": "edit insert",
        "args": ["file_path", "content"]
    },
    "edit_info": {
        "description": "Show file information",
        "patterns": [],
        "command": "edit info",
        "args": ["file_path"]
    },
    "chat": {
        "description": "Start an interactive chat session",
        "patterns": [],
        "command": "chat",
        "args": []
    },
    "config_show": {
        "description": "Show configuration",
        "patterns": [],
        "command": "config show",
        "args": []
    },
    "bash": {
        "description": "Execute bash commands",
        "patterns": [],
        "command": "bash main",
        "args": ["command"]
    }
}


class ToolSelectionState(TypedDict):
    """State for tool selection workflow."""
    prompt: str
    model: str
    provider: str
    temperature: float
    verbose: bool
    tool_name: Optional[str]
    tool_args: List[str]
    confidence: float
    reasoning: str
    error: Optional[str]


def create_tool_selection_graph() -> StateGraph:
    """Create the LangGraph for tool selection."""
    
    # Define the nodes
    def analyze_prompt(state: ToolSelectionState) -> ToolSelectionState:
        """Analyze the prompt to determine the best tool."""
        try:
            client = get_client(state["provider"])
            
            system_prompt = """You are an AI assistant that helps users choose the right tool for their task.

Available tools and their commands:
- ask: Ask a single question to the AI (command: ask) - Use for general knowledge questions, explanations, analysis
- code: Generate code based on a prompt (command: code) - Use for creating new code, functions, scripts
- explain: Explain the given code (command: explain) - Use for analyzing and explaining existing code
- edit view: View file content (command: edit view) - Use for reading/displaying file contents
- edit find: Search for text in a file (command: edit find) - Use for searching within files
- edit replace: Replace text in a file (command: edit replace) - Use for modifying file contents
- edit insert: Insert text into a file (command: edit insert) - Use for adding content to files
- edit info: Show file information (command: edit info) - Use for file metadata and statistics
- chat: Start an interactive chat session (command: chat) - Use for ongoing conversations
- config show: Show configuration (command: config show) - Use for viewing settings
- bash main: Execute bash commands (command: bash main) - Use for system operations, file operations, network queries, time/date, process management, etc.

IMPORTANT GUIDELINES:
- For system-related questions (time, date, current directory, file listings, process info, network status, etc.), use "bash main"
- For date calculations, use "bash main" with appropriate date command for the OS
- For network port queries, use "bash main" with commands like "netstat -an | grep LISTEN"
- For general knowledge questions, use "ask"
- For code generation, use "code"
- For file operations, prefer bash commands over edit commands when appropriate

Common bash commands for system queries:
- Time/date: date, date +"%Y-%m-%d %H:%M:%S"
- Date calculations (macOS): date -v+1d (tomorrow), date -v+1w (next week), date -v+1m (next month), date -v+32d (32 days from now)
- Date calculations (Linux): date -d "tomorrow", date -d "next week", date -d "next month"
- Current directory: pwd
- File listing: ls, ls -la, ls -lh
- Process info: ps aux, top
- System info: uname -a, whoami, hostname
- Network: ping, curl, wget
- Network ports: netstat -an | grep LISTEN, lsof -i -P | grep LISTEN

NOTE: This system appears to be macOS, so use macOS date syntax (-v flag) for date calculations.
NOTE: For complex commands with pipes (|), use the full command as a single argument.
IMPORTANT: When using pipes, include the pipe symbol (|) in the command.

Respond with ONLY the tool name and arguments in this exact format:
TOOL: command_name
ARGS: arg1|arg2|arg3
REASONING: brief explanation of why this tool was chosen

For example:
TOOL: ask
ARGS: What is the capital of France?
REASONING: This is a general knowledge question about geography.

TOOL: bash main
ARGS: date
REASONING: User is asking for current time/date information.

TOOL: bash main
ARGS: netstat -an | grep LISTEN
REASONING: User is asking about network ports that are listening.

IMPORTANT: Use the command name (not the tool description) and do not include quotes around arguments.
For complex commands with pipes or multiple arguments, put the entire command as a single argument.
CRITICAL: When using grep with pipes, include the pipe symbol (|) in the command, like: netstat -an | grep LISTEN"""

            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=f"Which tool should I use for: {state['prompt']}")
            ]
            
            response = asyncio.run(client.chat_completion(
                messages=messages,
                model=state["model"],
                temperature=state["temperature"],
                max_tokens=300
            ))
            
            content = response.content.strip()
            
            if state["verbose"]:
                console.print(f"[dim]AI response: {content}[/dim]")
            
            # Parse the response
            tool_match = re.search(r"TOOL:\s*([^\n]+)", content)
            
            # Handle empty ARGS case
            if "ARGS: \nREASONING:" in content:
                args_match = True
                args_str = ""
            elif "ARGS:\nREASONING:" in content:
                args_match = True
                args_str = ""
            else:
                args_match = re.search(r"ARGS:\s*(.*?)(?:\nREASONING:|$)", content, re.DOTALL)
            
            reasoning_match = re.search(r"REASONING:\s*(.*?)(?:\n|$)", content)
            
            if state["verbose"]:
                console.print(f"[dim]Parsed tool: {tool_match.group(1) if tool_match else 'None'}[/dim]")
                if isinstance(args_match, bool):
                    console.print(f"[dim]Parsed args: {args_str if 'args_str' in locals() else 'None'}[/dim]")
                else:
                    console.print(f"[dim]Parsed args: {args_match.group(1) if args_match else 'None'}[/dim]")
                console.print(f"[dim]Parsed reasoning: {reasoning_match.group(1) if reasoning_match else 'None'}[/dim]")
            
            if tool_match and args_match:
                tool_name = tool_match.group(1).strip()
                tool_name = tool_name.replace(" ARGS", "").replace("\nARGS", "").strip()
                
                # Handle the case where we already extracted args_str
                if 'args_str' not in locals():
                    args_str = args_match.group(1).strip()
                    args_str = args_str.strip('"\'')
                
                # For bash commands, don't split by | as it's part of the command
                if tool_name == "bash main":
                    args = [args_str]
                else:
                    # For other commands, split by | as separator
                    args = [arg.strip().strip('"\'') for arg in args_str.split('|') if arg.strip()]
                
                reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
                
                # Find the tool by command name
                for key, tool_info in TOOLS.items():
                    if tool_info["command"] == tool_name:
                        return {
                            **state,
                            "tool_name": tool_info["command"],
                            "tool_args": args,
                            "confidence": 0.9,
                            "reasoning": reasoning
                        }
                
                # If not found, return the tool name as is
                return {
                    **state,
                    "tool_name": tool_name,
                    "tool_args": args,
                    "confidence": 0.7,
                    "reasoning": reasoning
                }
            else:
                return {
                    **state,
                    "error": "Could not parse AI response",
                    "confidence": 0.0
                }
                
        except Exception as e:
            return {
                **state,
                "error": f"AI tool selection failed: {e}",
                "confidence": 0.0
            }
    
    def validate_selection(state: ToolSelectionState) -> ToolSelectionState:
        """Validate the tool selection and provide feedback."""
        if state.get("error"):
            return state
        
        if not state.get("tool_name"):
            return {
                **state,
                "error": "No tool was selected",
                "confidence": 0.0
            }
        
        # Check if the tool exists
        tool_exists = any(tool_info["command"] == state["tool_name"] for tool_info in TOOLS.values())
        
        if not tool_exists:
            return {
                **state,
                "error": f"Unknown tool: {state['tool_name']}",
                "confidence": 0.0
            }
        
        return state
    
    def execute_tool(state: ToolSelectionState) -> ToolSelectionState:
        """Execute the selected tool."""
        if state.get("error") or not state.get("tool_name"):
            return state
        
        try:
            # Build the command
            cmd = ["ai-cli"] + state["tool_name"].split() + state["tool_args"]
            
            if state["verbose"]:
                console.print(f"[dim]Executing: {' '.join(cmd)}[/dim]")
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
            
            # Print output
            if result.stdout:
                console.print(result.stdout)
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
                
            if result.returncode != 0:
                return {
                    **state,
                    "error": f"Command failed with exit code {result.returncode}"
                }
            
            return state
            
        except Exception as e:
            return {
                **state,
                "error": f"Error executing command: {e}"
            }
    
    # Create the graph
    workflow = StateGraph(ToolSelectionState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_prompt)
    workflow.add_node("validate", validate_selection)
    workflow.add_node("execute", execute_tool)
    
    # Add edges
    workflow.add_edge("analyze", "validate")
    workflow.add_edge("validate", "execute")
    workflow.add_edge("execute", END)
    
    # Set entry point
    workflow.set_entry_point("analyze")
    
    return workflow


@app.command()
def main(
    prompt: str = typer.Argument(..., help="Natural language description of what you want to do"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider to use"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="Temperature for AI responses (0.0-2.0)"),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
    force_tool: Optional[str] = typer.Option(None, "--force-tool", help="Force use of specific tool"),
) -> None:
    """AI-powered command that intelligently decides which tool to use using LangGraph."""
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
        title="[bold green]AI Tool Selection (LangGraph)[/bold green]"
    ))
    
    if force_tool:
        # Use forced tool
        console.print(f"[yellow]Forcing tool: {force_tool}[/yellow]")
        state = {
            "prompt": prompt,
            "model": model,
            "provider": provider,
            "temperature": temperature,
            "verbose": verbose,
            "tool_name": force_tool,
            "tool_args": [prompt],
            "confidence": 1.0,
            "reasoning": "Forced tool selection",
            "error": None
        }
    else:
        # Create and run the workflow
        graph = create_tool_selection_graph()
        app = graph.compile()
        
        # Initialize state
        initial_state = {
            "prompt": prompt,
            "model": model,
            "provider": provider,
            "temperature": temperature,
            "verbose": verbose,
            "tool_name": None,
            "tool_args": [],
            "confidence": 0.0,
            "reasoning": "",
            "error": None
        }
        
        # Run the workflow
        try:
            final_state = app.invoke(initial_state)
            state = final_state
        except Exception as e:
            console.print(f"[red]Workflow execution failed: {e}[/red]")
            raise typer.Exit(1)
    
    # Handle errors
    if state.get("error"):
        console.print(f"[red]Error: {state['error']}[/red]")
        if state.get("confidence", 0) < 0.5:
            console.print("\n[bold]Available tools:[/bold]")
            for tool, info in TOOLS.items():
                console.print(f"  • {tool}: {info['description']}")
        raise typer.Exit(1)
    
    # Show results
    if state.get("reasoning"):
        console.print(f"[dim]Reasoning: {state['reasoning']}[/dim]")
    
    if state.get("confidence"):
        console.print(f"[green]Confidence: {state['confidence']:.2f}[/green]")


if __name__ == "__main__":
    app() 