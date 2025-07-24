"""File editing command for AI CLI."""

import re
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from ..core.utils import detect_language, setup_logging

app = typer.Typer(name="edit", help="Edit text files")

console = Console()


def read_file(file_path: str) -> str:
    """Read content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise typer.BadParameter(f"File not found: {file_path}")
    except Exception as e:
        raise typer.BadParameter(f"Error reading file {file_path}: {e}")


def write_file(file_path: str, content: str) -> None:
    """Write content to a file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        raise typer.BadParameter(f"Error writing file {file_path}: {e}")


def view_file(file_path: str, line_numbers: bool = True, syntax_highlight: bool = True) -> None:
    """View file content with optional line numbers and syntax highlighting."""
    content = read_file(file_path)
    
    if not content.strip():
        console.print(f"[yellow]File {file_path} is empty[/yellow]")
        return
    
    # Detect language for syntax highlighting
    language = detect_language(content) if syntax_highlight else "text"
    
    console.print(Panel(
        f"[bold blue]File:[/bold blue] {file_path}",
        title=f"[bold green]File Viewer[/bold green]"
    ))
    
    if syntax_highlight and language != "text":
        syntax = Syntax(content, language, theme="monokai", line_numbers=line_numbers)
        console.print(syntax)
    else:
        # Split content into lines for line numbers
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if line_numbers:
                console.print(f"[dim]{i:4d}[/dim] {line}")
            else:
                console.print(line)


def find_in_file(file_path: str, pattern: str, case_sensitive: bool = False, regex: bool = False) -> List[tuple]:
    """Find pattern in file and return list of (line_number, line_content) tuples."""
    content = read_file(file_path)
    lines = content.split('\n')
    matches = []
    
    flags = 0 if case_sensitive else re.IGNORECASE
    
    for i, line in enumerate(lines, 1):
        if regex:
            if re.search(pattern, line, flags):
                matches.append((i, line))
        else:
            if pattern in line if case_sensitive else pattern.lower() in line.lower():
                matches.append((i, line))
    
    return matches


def replace_in_file(file_path: str, pattern: str, replacement: str, case_sensitive: bool = False, regex: bool = False) -> int:
    """Replace pattern in file and return number of replacements made."""
    content = read_file(file_path)
    
    flags = 0 if case_sensitive else re.IGNORECASE
    
    if regex:
        new_content, count = re.subn(pattern, replacement, content, flags=flags)
    else:
        if case_sensitive:
            new_content = content.replace(pattern, replacement)
            count = content.count(pattern)
        else:
            # Case-insensitive replacement
            pattern_lower = pattern.lower()
            content_lower = content.lower()
            count = content_lower.count(pattern_lower)
            
            # Build new content with case-insensitive replacement
            new_content = ""
            i = 0
            while i < len(content):
                if content_lower[i:i+len(pattern_lower)] == pattern_lower:
                    new_content += replacement
                    i += len(pattern_lower)
                else:
                    new_content += content[i]
                    i += 1
    
    write_file(file_path, new_content)
    return count


def insert_in_file(file_path: str, content: str, line_number: Optional[int] = None, position: str = "end") -> None:
    """Insert content into file at specified position."""
    if position not in ["start", "end", "line"]:
        raise typer.BadParameter("Position must be one of: start, end, line")
    
    if position == "line" and line_number is None:
        raise typer.BadParameter("Line number is required when position is 'line'")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        # File doesn't exist, create it
        lines = []
    
    if position == "start":
        lines.insert(0, content + '\n')
    elif position == "end":
        lines.append(content + '\n')
    elif position == "line":
        if line_number < 1 or line_number > len(lines) + 1:
            raise typer.BadParameter(f"Line number {line_number} is out of range (1-{len(lines) + 1})")
        lines.insert(line_number - 1, content + '\n')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


@app.command()
def view(
    file_path: str = typer.Argument(..., help="Path to the file to view"),
    no_line_numbers: bool = typer.Option(False, "--no-line-numbers", help="Disable line numbers"),
    no_syntax: bool = typer.Option(False, "--no-syntax", help="Disable syntax highlighting"),
) -> None:
    """View file content with syntax highlighting and line numbers."""
    view_file(file_path, line_numbers=not no_line_numbers, syntax_highlight=not no_syntax)


@app.command()
def find(
    file_path: str = typer.Argument(..., help="Path to the file to search"),
    pattern: str = typer.Argument(..., help="Pattern to search for"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", "-c", help="Case-sensitive search"),
    regex: bool = typer.Option(False, "--regex", "-r", help="Use regex pattern"),
) -> None:
    """Find pattern in file and display matching lines."""
    matches = find_in_file(file_path, pattern, case_sensitive, regex)
    
    if not matches:
        console.print(f"[yellow]No matches found for '{pattern}' in {file_path}[/yellow]")
        return
    
    console.print(Panel(
        f"[bold blue]File:[/bold blue] {file_path}\n[bold blue]Pattern:[/bold blue] {pattern}\n[bold blue]Matches:[/bold blue] {len(matches)}",
        title=f"[bold green]Search Results[/bold green]"
    ))
    
    table = Table()
    table.add_column("Line", style="cyan", no_wrap=True)
    table.add_column("Content", style="green")
    
    for line_num, line_content in matches:
        table.add_row(str(line_num), line_content.strip())
    
    console.print(table)


@app.command()
def replace(
    file_path: str = typer.Argument(..., help="Path to the file to modify"),
    pattern: str = typer.Argument(..., help="Pattern to replace"),
    replacement: str = typer.Argument(..., help="Replacement text"),
    case_sensitive: bool = typer.Option(False, "--case-sensitive", "-c", help="Case-sensitive replacement"),
    regex: bool = typer.Option(False, "--regex", "-r", help="Use regex pattern"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be changed without making changes"),
) -> None:
    """Replace pattern in file with replacement text."""
    if dry_run:
        # Show what would be changed
        matches = find_in_file(file_path, pattern, case_sensitive, regex)
        if not matches:
            console.print(f"[yellow]No matches found for '{pattern}' in {file_path}[/yellow]")
            return
        
        console.print(Panel(
            f"[bold blue]File:[/bold blue] {file_path}\n[bold blue]Pattern:[/bold blue] {pattern}\n[bold blue]Replacement:[/bold blue] {replacement}\n[bold blue]Matches:[/bold blue] {len(matches)}",
            title=f"[bold green]Dry Run - Would Replace[/bold green]"
        ))
        
        table = Table()
        table.add_column("Line", style="cyan", no_wrap=True)
        table.add_column("Current", style="red")
        table.add_column("Would Become", style="green")
        
        for line_num, line_content in matches:
            if regex:
                new_line = re.sub(pattern, replacement, line_content, flags=0 if case_sensitive else re.IGNORECASE)
            else:
                if case_sensitive:
                    new_line = line_content.replace(pattern, replacement)
                else:
                    # Case-insensitive replacement
                    pattern_lower = pattern.lower()
                    line_lower = line_content.lower()
                    if pattern_lower in line_lower:
                        # Simple replacement for display
                        new_line = line_content.replace(pattern, replacement)
                    else:
                        new_line = line_content
            
            table.add_row(str(line_num), line_content.strip(), new_line.strip())
        
        console.print(table)
    else:
        # Actually perform the replacement
        count = replace_in_file(file_path, pattern, replacement, case_sensitive, regex)
        console.print(f"[green]Replaced {count} occurrence(s) of '{pattern}' with '{replacement}' in {file_path}[/green]")


@app.command()
def insert(
    file_path: str = typer.Argument(..., help="Path to the file to modify"),
    content: str = typer.Argument(..., help="Content to insert"),
    position: str = typer.Option("end", "--position", "-p", help="Position to insert: start, end, or line"),
    line_number: Optional[int] = typer.Option(None, "--line", "-l", help="Line number for insertion (required when position is 'line')"),
) -> None:
    """Insert content into file at specified position."""
    insert_in_file(file_path, content, line_number, position)
    pos_desc = f"line {line_number}" if position == "line" else position
    console.print(f"[green]Inserted content at {pos_desc} in {file_path}[/green]")


@app.command()
def info(
    file_path: str = typer.Argument(..., help="Path to the file to analyze"),
) -> None:
    """Show file information including size, lines, and language detection."""
    try:
        path = Path(file_path)
        if not path.exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            return
        
        content = read_file(file_path)
        lines = content.split('\n')
        language = detect_language(content)
        
        # Calculate file size
        size_bytes = path.stat().st_size
        size_kb = size_bytes / 1024
        
        table = Table(title=f"[bold blue]File Information: {file_path}[/bold blue]")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Size", f"{size_kb:.2f} KB ({size_bytes} bytes)")
        table.add_row("Lines", str(len(lines)))
        table.add_row("Characters", str(len(content)))
        table.add_row("Detected Language", language)
        table.add_row("Empty", "Yes" if not content.strip() else "No")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error analyzing file: {e}[/red]")


if __name__ == "__main__":
    app() 