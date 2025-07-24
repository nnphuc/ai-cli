"""AI command using LangGraph for tool selection."""

import asyncio
import re
import subprocess
from typing import TypedDict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from langgraph.graph import StateGraph, END

from ..core.client import get_client, Message
from ..core.config import Config

app = typer.Typer(help="AI-powered tool selection")
console = Console()

# Define available tools
TOOLS = {
    "ask": {
        "command": "ask",
        "description": "Ask AI a question and get a direct answer",
        "patterns": []
    },
    "chat": {
        "command": "chat",
        "description": "Start an interactive chat session with AI",
        "patterns": []
    },
    "code": {
        "command": "code",
        "description": "Generate, explain, or debug code",
        "patterns": []
    },
    "explain": {
        "command": "explain",
        "description": "Explain concepts, code, or text in detail",
        "patterns": []
    },
    "config_show": {
        "command": "config show",
        "description": "Show current configuration settings",
        "patterns": []
    },
    "edit_view": {
        "command": "edit view",
        "description": "View the contents of a text file",
        "patterns": []
    },
    "edit_find": {
        "command": "edit find",
        "description": "Find text patterns in a file",
        "patterns": []
    },
    "edit_replace": {
        "command": "edit replace",
        "description": "Replace text in a file",
        "patterns": []
    },
    "edit_insert": {
        "command": "edit insert",
        "description": "Insert text into a file",
        "patterns": []
    },
    "bash main": {
        "command": "bash main",
        "description": "Execute bash commands for system operations, file management, network queries, process management, and system information",
        "patterns": []
    },
    "web search": {
        "command": "web search",
        "description": "Search the web for information",
        "patterns": []
    },
    "web summarize": {
        "command": "web summarize",
        "description": "Summarize web content from a URL",
        "patterns": []
    },
    "web read": {
        "command": "web read",
        "description": "Read and extract content from a web page",
        "patterns": []
    },
    "web news": {
        "command": "web news",
        "description": "Search for recent news articles",
        "patterns": []
    }
}

# Define state for the workflow
class ToolSelectionState(TypedDict):
    prompt: str
    tool_name: str
    args: List[str]
    reasoning: str
    verbose: bool


def create_tool_selection_graph():
    """Create the LangGraph workflow for tool selection."""
    
    def analyze_prompt(state: ToolSelectionState) -> ToolSelectionState:
        """Analyze the prompt and select the appropriate tool."""
        # Create a fresh config instance
        fresh_config = Config.from_env()
        client = get_client(fresh_config.default_provider)
        
        # Create tool descriptions for AI
        tool_descriptions = []
        for tool_key, tool_info in TOOLS.items():
            tool_descriptions.append(f"- {tool_key}: {tool_info['description']}")
        
        system_prompt = f"""You are an AI assistant that helps users select the most appropriate tool for their request.

Available tools:
{chr(10).join(tool_descriptions)}

Guidelines for tool selection:
1. For system-related queries (time, date, directory, network, processes), use "bash main"
2. For web searches and information gathering, use "web search"
3. For summarizing web content from URLs, use "web summarize"
4. For reading web pages, use "web read"
5. For news searches, use "web news"
6. For file operations (view, find, replace, insert), use "edit view", "edit find", "edit replace", "edit insert"
7. For configuration management, use "config show"
8. For general questions and explanations, use "ask" or "explain"
9. For code-related tasks, use "code"
10. For interactive conversations, use "chat"

For bash commands:
- Use macOS-compatible syntax (e.g., `date -v+1d` instead of `date -d "+1 day"`)
- Include pipe symbols (|) for complex commands (e.g., `netstat -an | grep LISTEN`)
- For time/date queries, use `date` command
- For directory listing, use `ls -la`
- For network queries, use `netstat`, `lsof`, or `ps` commands

Response format:
TOOL: <tool_name>
ARGS: <arguments separated by | if multiple>
REASONING: <explanation of why this tool was chosen>

Examples:
- "what time is it" → TOOL: bash main, ARGS: date
- "search for python tutorials" → TOOL: web search, ARGS: python tutorials
- "summarize https://example.com" → TOOL: web summarize, ARGS: https://example.com
- "latest tech news" → TOOL: web news, ARGS: latest tech news
- "view file.txt" → TOOL: edit view, ARGS: file.txt

Do not include quotes around arguments."""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=state["prompt"])
        ]
        
        response = asyncio.run(client.chat_completion(
            messages=messages,
            model=fresh_config.default_model,
            temperature=fresh_config.default_temperature,
            max_tokens=fresh_config.default_max_tokens
        ))
        content = response.content
        
        if state["verbose"]:
            console.print(f"[dim]AI Response: {content}[/dim]")
        
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
            
            reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
            
            return {
                **state,
                "tool_name": tool_name,
                "args": args,
                "reasoning": reasoning
            }
        else:
            # Fallback to ask tool if parsing fails
            return {
                **state,
                "tool_name": "ask",
                "args": [state["prompt"]],
                "reasoning": "Failed to parse tool selection, using ask as fallback"
            }
    
    def validate_selection(state: ToolSelectionState) -> ToolSelectionState:
        """Validate the selected tool."""
        tool_name = state["tool_name"]
        
        if tool_name not in TOOLS:
            if state["verbose"]:
                console.print(f"[yellow]Unknown tool '{tool_name}', falling back to 'ask'[/yellow]")
            return {
                **state,
                "tool_name": "ask",
                "args": [state["prompt"]],
                "reasoning": f"Unknown tool '{tool_name}', using ask as fallback"
            }
        
        return state
    
    def execute_tool(state: ToolSelectionState) -> ToolSelectionState:
        """Execute the selected tool."""
        tool_name = state["tool_name"]
        args = state["args"]
        reasoning = state["reasoning"]
        
        if state["verbose"]:
            console.print(f"[dim]Executing: {tool_name} with args: {args}[/dim]")
            if reasoning:
                console.print(f"[dim]Reasoning: {reasoning}[/dim]")
        
        try:
            # Get the actual command to execute
            tool_info = TOOLS[tool_name]
            command = tool_info["command"]
            
            # Build the full command
            full_command = ["ai-cli"] + command.split() + args
            
            if state["verbose"]:
                console.print(f"[dim]Running: {' '.join(full_command)}[/dim]")
            
            # Execute the command
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                console.print(result.stdout)
            else:
                console.print(f"[red]Error executing {tool_name}:[/red]")
                console.print(result.stderr)
                
        except subprocess.TimeoutExpired:
            console.print(f"[red]Timeout executing {tool_name}[/red]")
        except Exception as e:
            console.print(f"[red]Error executing {tool_name}: {e}[/red]")
        
        return state
    
    # Create the workflow
    workflow = StateGraph(ToolSelectionState)
    
    # Add nodes
    workflow.add_node("analyze_prompt", analyze_prompt)
    workflow.add_node("validate_selection", validate_selection)
    workflow.add_node("execute_tool", execute_tool)
    
    # Add edges
    workflow.set_entry_point("analyze_prompt")
    workflow.add_edge("analyze_prompt", "validate_selection")
    workflow.add_edge("validate_selection", "execute_tool")
    workflow.add_edge("execute_tool", END)
    
    return workflow.compile()


@app.command()
def main(
    prompt: str = typer.Argument(..., help="Your request or question"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI model to use"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="AI provider (openai/anthropic)"),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t", help="AI temperature"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Maximum tokens"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """AI-powered tool selection - automatically choose and execute the best tool for your request."""
    
    # Note: Config updates are handled in the analyze_prompt function
    # by creating a fresh config instance
    
    # Create and run the workflow
    graph = create_tool_selection_graph()
    
    initial_state = {
        "prompt": prompt,
        "tool_name": "",
        "args": [],
        "reasoning": "",
        "verbose": verbose
    }
    
    try:
        graph.invoke(initial_state)
    except Exception as e:
        console.print(f"[red]Error in AI workflow: {e}[/red]")


if __name__ == "__main__":
    app() 