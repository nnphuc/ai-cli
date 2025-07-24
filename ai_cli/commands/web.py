"""Web tools for searching, summarizing, and reading web content."""

import asyncio
import re
from typing import List, Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from ..core.client import get_client, Message
from ..core.config import config

app = typer.Typer(help="Web tools for searching, summarizing, and reading content")
console = Console()


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def clean_text(text: str, max_length: int = 2000) -> str:
    """Clean and truncate text."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text


def extract_article_content(url: str) -> dict:
    """Extract article content from a URL using BeautifulSoup."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Extract title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Extract main content
        content = ""
        
        # Try to find main content areas
        main_selectors = [
            'article',
            '[role="main"]',
            '.content',
            '.post-content',
            '.entry-content',
            'main',
            '.main-content'
        ]
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                content = main_content.get_text()
                break
        
        # If no main content found, get body text
        if not content:
            content = soup.get_text()
        
        # Clean the content
        content = clean_text(content, 5000)
        
        # Extract meta description
        description = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '')
        
        return {
            'title': title,
            'content': content,
            'description': description,
            'url': url
        }
        
    except Exception as e:
        return {
            'title': 'Error',
            'content': f'Failed to extract content: {str(e)}',
            'description': '',
            'url': url
        }


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    max_results: int = typer.Option(5, "--max", "-m", help="Maximum number of results"),
    region: str = typer.Option("us-en", "--region", "-r", help="Search region"),
):
    """Search the web using DuckDuckGo."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Searching...", total=None)
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results, region=region))
            
            progress.update(task, completed=True)
            
            if not results:
                console.print("[yellow]No results found.[/yellow]")
                return
            
            # Create results table
            table = Table(title=f"Search Results for: {query}")
            table.add_column("Title", style="cyan", no_wrap=True)
            table.add_column("URL", style="blue")
            table.add_column("Snippet", style="white")
            
            for i, result in enumerate(results, 1):
                title = clean_text(result.get('title', ''), 60)
                url = result.get('href', '')  # Changed from 'link' to 'href'
                snippet = clean_text(result.get('body', ''), 100)
                
                table.add_row(
                    f"{i}. {title}",
                    url or "No URL",
                    snippet
                )
            
            console.print(table)
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error searching: {e}[/red]")


@app.command()
def summarize(
    url: str = typer.Argument(..., help="URL to summarize"),
    max_length: int = typer.Option(500, "--max", "-m", help="Maximum summary length"),
):
    """Summarize web content using AI."""
    if not is_valid_url(url):
        console.print("[red]Invalid URL provided.[/red]")
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching and analyzing content...", total=None)
        
        try:
            # Extract article content
            article_data = extract_article_content(url)
            
            if not article_data['content'] or article_data['content'].startswith('Failed to extract'):
                progress.update(task, completed=True)
                console.print("[yellow]No content found at the URL.[/yellow]")
                return
            
            # Get AI summary
            client = get_client(config.default_provider)
            
            prompt = f"""Please provide a concise summary of the following web content in {max_length} words or less:

Title: {article_data['title']}

Content:
{article_data['content'][:3000]}

Please focus on the main points and key information."""

            response = asyncio.run(client.chat_completion(
                messages=[Message(role="user", content=prompt)],
                model=config.default_model,
                temperature=config.default_temperature,
                max_tokens=config.default_max_tokens
            ))
            summary = response.content
            
            progress.update(task, completed=True)
            
            # Display results
            console.print(Panel(
                f"[bold cyan]Title:[/bold cyan] {article_data['title']}\n\n"
                f"[bold green]AI Summary:[/bold green]\n{summary}\n\n"
                f"[dim]Source: {url}[/dim]",
                title="Web Content Summary",
                border_style="blue"
            ))
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error summarizing content: {e}[/red]")


@app.command()
def read(
    url: str = typer.Argument(..., help="URL to read"),
    format: str = typer.Option("text", "--format", "-f", help="Output format (text/markdown/html)"),
    max_length: int = typer.Option(5000, "--max", "-m", help="Maximum content length"),
):
    """Read and extract content from a web page."""
    if not is_valid_url(url):
        console.print("[red]Invalid URL provided.[/red]")
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching content...", total=None)
        
        try:
            # Extract content
            article_data = extract_article_content(url)
            
            progress.update(task, completed=True)
            
            # Format output
            if format == "markdown":
                # Convert HTML to markdown
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                markdown_content = md(str(soup))
                content = clean_text(markdown_content, max_length)
            elif format == "html":
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                content = str(soup)
                content = clean_text(content, max_length)
            else:  # text
                content = article_data['content']
                content = clean_text(content, max_length)
            
            # Display results
            console.print(Panel(
                f"[bold cyan]Title:[/bold cyan] {article_data['title']}\n\n"
                f"[bold green]Content:[/bold green]\n{content}\n\n"
                f"[dim]Source: {url}[/dim]",
                title=f"Web Content ({format.upper()})",
                border_style="green"
            ))
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error reading content: {e}[/red]")


@app.command()
def news(
    topic: Optional[str] = typer.Argument(None, help="News topic to search for"),
    max_results: int = typer.Option(10, "--max", "-m", help="Maximum number of results"),
    region: str = typer.Option("us-en", "--region", "-r", help="Search region"),
):
    """Search for recent news articles."""
    query = f"latest news {topic}" if topic else "latest news"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Searching for news...", total=None)
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=max_results, region=region))
            
            progress.update(task, completed=True)
            
            if not results:
                console.print("[yellow]No news found.[/yellow]")
                return
            
            # Create news table
            table = Table(title=f"News Results: {topic or 'Latest News'}")
            table.add_column("Title", style="cyan", no_wrap=True)
            table.add_column("Source", style="blue")
            table.add_column("Date", style="yellow")
            table.add_column("URL", style="green")
            table.add_column("Snippet", style="white")
            
            for i, result in enumerate(results, 1):
                title = clean_text(result.get('title', ''), 60)
                source = result.get('source', 'Unknown')
                date = result.get('date', 'Unknown')
                url = result.get('url', '')  # Changed from 'href' to 'url'
                snippet = clean_text(result.get('body', ''), 80)
                
                table.add_row(
                    f"{i}. {title}",
                    source,
                    date,
                    url or "No URL",
                    snippet
                )
            
            console.print(table)
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]Error searching news: {e}[/red]")


if __name__ == "__main__":
    app() 