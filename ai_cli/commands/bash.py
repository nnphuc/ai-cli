"""Bash command execution for AI CLI."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from ..core.utils import setup_logging

app = typer.Typer(name="bash", help="Execute bash commands")

console = Console()


def execute_command(
    command: str,
    cwd: Optional[str] = None,
    timeout: Optional[int] = None,
    shell: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Execute a shell command and return the result."""
    try:
        # Use the current working directory if not specified
        working_dir = cwd or os.getcwd()
        
        # Execute the command
        result = subprocess.run(
            command,
            shell=shell,
            cwd=working_dir,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
        return result
    except subprocess.TimeoutExpired:
        # Create a mock result for timeout
        result = subprocess.CompletedProcess(
            args=command,
            returncode=-1,
            stdout="",
            stderr="Command timed out"
        )
        return result
    except Exception as e:
        # Create a mock result for other errors
        result = subprocess.CompletedProcess(
            args=command,
            returncode=-1,
            stdout="",
            stderr=str(e)
        )
        return result


def format_command_output(command: str, result: subprocess.CompletedProcess, cwd: str) -> None:
    """Format and display command output with rich formatting."""
    # Create header panel
    header_text = f"[bold blue]Command:[/bold blue] {command}\n[bold blue]Working Directory:[/bold blue] {cwd}\n[bold blue]Exit Code:[/bold blue] {result.returncode}"
    
    if result.returncode == 0:
        header_style = "bold green"
    elif result.returncode == -1:
        header_style = "bold red"
    else:
        header_style = "bold yellow"
    
    console.print(Panel(header_text, title=f"[{header_style}]Command Execution[/{header_style}]"))
    
    # Display stdout if available
    if result.stdout:
        console.print(Panel(
            Syntax(result.stdout, "bash", theme="monokai", line_numbers=True),
            title="[bold green]Standard Output[/bold green]"
        ))
    
    # Display stderr if available
    if result.stderr:
        console.print(Panel(
            Syntax(result.stderr, "bash", theme="monokai", line_numbers=True),
            title="[bold red]Standard Error[/bold red]"
        ))
    
    # Display summary
    summary_table = Table(title="[bold blue]Execution Summary[/bold blue]")
    summary_table.add_column("Property", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Exit Code", str(result.returncode))
    summary_table.add_row("Stdout Lines", str(len(result.stdout.splitlines()) if result.stdout else 0))
    summary_table.add_row("Stderr Lines", str(len(result.stderr.splitlines()) if result.stderr else 0))
    summary_table.add_row("Success", "✅ Yes" if result.returncode == 0 else "❌ No")
    
    console.print(summary_table)


def detect_language_from_output(output: str) -> str:
    """Detect the language of the output for syntax highlighting."""
    if not output:
        return "text"
    
    output_lower = output.lower()
    
    # Check for common patterns
    if any(keyword in output_lower for keyword in ["error:", "warning:", "fatal:", "exception"]):
        return "bash"
    elif any(keyword in output_lower for keyword in ["json", "{", "}"]):
        return "json"
    elif any(keyword in output_lower for keyword in ["xml", "<", ">"]):
        return "xml"
    elif any(keyword in output_lower for keyword in ["yaml", "---", "- "]):
        return "yaml"
    elif any(keyword in output_lower for keyword in ["python", "def ", "import ", "class "]):
        return "python"
    elif any(keyword in output_lower for keyword in ["javascript", "function", "var ", "let ", "const "]):
        return "javascript"
    else:
        return "bash"


def format_simple_output(command: str, result: subprocess.CompletedProcess) -> None:
    """Format output in a simple, compact way."""
    # Status indicator
    if result.returncode == 0:
        status = "[green]✓[/green]"
    else:
        status = "[red]✗[/red]"
    
    console.print(f"{status} {command}")
    
    # Show output if any
    if result.stdout:
        console.print(result.stdout)
    if result.stderr:
        console.print(f"[red]{result.stderr}[/red]")


@app.command()
def main(
    command: str = typer.Argument(..., help="Bash command to execute"),
    cwd: Optional[str] = typer.Option(None, "--cwd", "-d", help="Working directory for command execution"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Timeout in seconds"),
    simple: bool = typer.Option(False, "--simple", "-s", help="Simple output format"),
    no_capture: bool = typer.Option(False, "--no-capture", help="Don't capture output (run interactively)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed without running"),
) -> None:
    """Execute a bash command with rich output formatting."""
    # Setup logging
    setup_logging()
    
    # Validate working directory
    working_dir = cwd or os.getcwd()
    if not os.path.exists(working_dir):
        console.print(f"[red]Working directory does not exist: {working_dir}[/red]")
        raise typer.Exit(1)
    
    # Show what will be executed
    if dry_run:
        console.print(Panel(
            f"[bold blue]Command:[/bold blue] {command}\n[bold blue]Working Directory:[/bold blue] {working_dir}\n[bold blue]Timeout:[/bold blue] {timeout or 'None'}",
            title="[bold yellow]Dry Run - Would Execute[/bold yellow]"
        ))
        return
    
    # Execute the command
    console.print(f"[dim]Executing: {command}[/dim]")
    
    try:
        result = execute_command(
            command=command,
            cwd=working_dir,
            timeout=timeout,
            capture_output=not no_capture
        )
        
        # Format and display output
        if simple:
            format_simple_output(command, result)
        else:
            format_command_output(command, result, working_dir)
        
        # Exit with the command's return code
        if result.returncode != 0:
            raise typer.Exit(result.returncode)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Command interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]Error executing command: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def script(
    script_path: str = typer.Argument(..., help="Path to bash script to execute"),
    args: Optional[List[str]] = typer.Argument(None, help="Arguments to pass to the script"),
    cwd: Optional[str] = typer.Option(None, "--cwd", "-d", help="Working directory for script execution"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Timeout in seconds"),
    simple: bool = typer.Option(False, "--simple", "-s", help="Simple output format"),
) -> None:
    """Execute a bash script file."""
    # Setup logging
    setup_logging()
    
    # Validate script file
    script_file = Path(script_path)
    if not script_file.exists():
        console.print(f"[red]Script file not found: {script_path}[/red]")
        raise typer.Exit(1)
    
    if not script_file.is_file():
        console.print(f"[red]Path is not a file: {script_path}[/red]")
        raise typer.Exit(1)
    
    # Make script executable if it isn't already
    if not os.access(script_file, os.X_OK):
        try:
            script_file.chmod(0o755)
            console.print(f"[yellow]Made script executable: {script_path}[/yellow]")
        except Exception as e:
            console.print(f"[red]Could not make script executable: {e}[/red]")
            raise typer.Exit(1)
    
    # Build command
    script_args = " ".join(args) if args else ""
    command = f"{script_path} {script_args}".strip()
    
    # Validate working directory
    working_dir = cwd or script_file.parent
    if not os.path.exists(working_dir):
        console.print(f"[red]Working directory does not exist: {working_dir}[/red]")
        raise typer.Exit(1)
    
    # Execute the script
    console.print(f"[dim]Executing script: {script_path}[/dim]")
    
    try:
        result = execute_command(
            command=command,
            cwd=working_dir,
            timeout=timeout
        )
        
        # Format and display output
        if simple:
            format_simple_output(command, result)
        else:
            format_command_output(command, result, str(working_dir))
        
        # Exit with the script's return code
        if result.returncode != 0:
            raise typer.Exit(result.returncode)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Script execution interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]Error executing script: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def interactive(
    cwd: Optional[str] = typer.Option(None, "--cwd", "-d", help="Working directory for commands"),
) -> None:
    """Start an interactive bash session."""
    # Setup logging
    setup_logging()
    
    # Validate working directory
    working_dir = cwd or os.getcwd()
    if not os.path.exists(working_dir):
        console.print(f"[red]Working directory does not exist: {working_dir}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel(
        f"[bold green]Interactive Bash Session[/bold green]\n[bold blue]Working Directory:[/bold blue] {working_dir}\n[bold blue]Type 'exit' to quit[/bold blue]",
        title="[bold blue]AI CLI Bash[/bold blue]"
    ))
    
    try:
        while True:
            # Get command from user
            command = input(f"[bold green]bash[/bold green] [dim]{working_dir}[/dim] $ ")
            
            if not command.strip():
                continue
            
            if command.strip().lower() in ['exit', 'quit', 'q']:
                console.print("[green]Goodbye![/green]")
                break
            
            # Execute command
            try:
                result = execute_command(
                    command=command,
                    cwd=working_dir,
                    capture_output=True
                )
                
                # Display output
                if result.stdout:
                    console.print(result.stdout)
                if result.stderr:
                    console.print(f"[red]{result.stderr}[/red]")
                
                # Show exit code if non-zero
                if result.returncode != 0:
                    console.print(f"[yellow]Exit code: {result.returncode}[/yellow]")
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Command interrupted[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                
    except KeyboardInterrupt:
        console.print("\n[green]Goodbye![/green]")
    except EOFError:
        console.print("\n[green]Goodbye![/green]")


@app.command()
def list_commands(
    cwd: Optional[str] = typer.Option(None, "--cwd", "-d", help="Working directory to list commands from"),
) -> None:
    """List available commands in the current PATH."""
    # Setup logging
    setup_logging()
    
    # Get working directory
    working_dir = cwd or os.getcwd()
    
    # Get PATH
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    
    # Find executable files
    executables = []
    for path_dir in path_dirs:
        if os.path.exists(path_dir):
            try:
                for item in os.listdir(path_dir):
                    item_path = os.path.join(path_dir, item)
                    if os.path.isfile(item_path) and os.access(item_path, os.X_OK):
                        executables.append(item)
            except (PermissionError, OSError):
                continue
    
    # Remove duplicates and sort
    unique_executables = sorted(list(set(executables)))
    
    # Display results
    console.print(Panel(
        f"[bold blue]Working Directory:[/bold blue] {working_dir}\n[bold blue]Total Commands:[/bold blue] {len(unique_executables)}",
        title="[bold green]Available Commands[/bold green]"
    ))
    
    # Create table
    table = Table()
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    
    # Categorize commands
    categories = {
        "System": ["ls", "cd", "pwd", "mkdir", "rm", "cp", "mv", "cat", "grep", "find", "chmod", "chown"],
        "Network": ["curl", "wget", "ssh", "scp", "ping", "netstat", "ifconfig", "ip"],
        "Development": ["git", "python", "node", "npm", "pip", "conda", "docker", "kubectl"],
        "Text": ["vim", "nano", "emacs", "less", "more", "head", "tail", "sort", "uniq"],
        "Archive": ["tar", "zip", "unzip", "gzip", "gunzip", "bzip2", "bunzip2"],
        "Process": ["ps", "top", "kill", "pkill", "pgrep", "nice", "renice"],
        "Other": []
    }
    
    categorized = {cat: [] for cat in categories}
    
    for cmd in unique_executables:
        categorized_flag = False
        for category, commands in categories.items():
            if cmd in commands:
                categorized[category].append(cmd)
                categorized_flag = True
                break
        if not categorized_flag:
            categorized["Other"].append(cmd)
    
    # Add to table
    for category, commands in categorized.items():
        if commands:
            table.add_row(f"[bold]{category}[/bold]", "")
            for cmd in sorted(commands):
                table.add_row(f"  {cmd}", category)
    
    console.print(table)


if __name__ == "__main__":
    app() 