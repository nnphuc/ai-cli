"""Tests for utility functions."""

import tempfile
from pathlib import Path

import pytest

from ai_cli.core.utils import (
    detect_language,
    sanitize_filename,
    truncate_text,
    get_file_extension,
    ensure_directory,
)


class TestUtils:
    """Test utility functions."""
    
    def test_detect_language_python(self):
        """Test Python language detection."""
        code = "def hello_world():\n    print('Hello, World!')"
        assert detect_language(code) == "python"
    
    def test_detect_language_javascript(self):
        """Test JavaScript language detection."""
        code = "function helloWorld() {\n    console.log('Hello, World!');\n}"
        assert detect_language(code) == "javascript"
    
    def test_detect_language_java(self):
        """Test Java language detection."""
        code = "public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println('Hello, World!');\n    }\n}"
        assert detect_language(code) == "java"
    
    def test_detect_language_html(self):
        """Test HTML language detection."""
        code = "<!DOCTYPE html>\n<html>\n<head>\n    <title>Hello World</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n</body>\n</html>"
        assert detect_language(code) == "html"
    
    def test_detect_language_css(self):
        """Test CSS language detection."""
        code = "body {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n}"
        assert detect_language(code) == "css"
    
    def test_detect_language_sql(self):
        """Test SQL language detection."""
        code = "SELECT * FROM users WHERE age > 18;"
        assert detect_language(code) == "sql"
    
    def test_detect_language_json(self):
        """Test JSON language detection."""
        code = '{"name": "John", "age": 30, "city": "New York"}'
        assert detect_language(code) == "json"
    
    def test_detect_language_text(self):
        """Test text detection for unknown language."""
        code = "This is just some plain text without any programming language indicators."
        assert detect_language(code) == "text"
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test invalid characters
        assert sanitize_filename("file<name>.txt") == "file_name_.txt"
        assert sanitize_filename("file:name.txt") == "file_name.txt"
        assert sanitize_filename("file/name.txt") == "file_name.txt"
        assert sanitize_filename("file\\name.txt") == "file_name.txt"
        assert sanitize_filename("file|name.txt") == "file_name.txt"
        assert sanitize_filename("file?name.txt") == "file_name.txt"
        assert sanitize_filename("file*name.txt") == "file_name.txt"
        
        # Test valid filename
        assert sanitize_filename("valid_filename.txt") == "valid_filename.txt"
        
        # Test whitespace
        assert sanitize_filename("  filename.txt  ") == "filename.txt"
    
    def test_truncate_text(self):
        """Test text truncation."""
        # Test short text (no truncation needed)
        assert truncate_text("Hello", 10) == "Hello"
        
        # Test long text (truncation needed)
        long_text = "This is a very long text that needs to be truncated"
        truncated = truncate_text(long_text, 20)
        assert len(truncated) == 20
        assert truncated.endswith("...")
        
        # Test exact length
        assert truncate_text("Hello World", 11) == "Hello World"
        
        # Test minimum truncation
        assert truncate_text("Hello World", 8) == "Hello..."
    
    def test_get_file_extension(self):
        """Test file extension extraction."""
        assert get_file_extension("file.txt") == ".txt"
        assert get_file_extension("file.py") == ".py"
        assert get_file_extension("file.js") == ".js"
        assert get_file_extension("file") == ""
        assert get_file_extension(".hidden") == ""
        assert get_file_extension("file.name.txt") == ".txt"
        assert get_file_extension("FILE.TXT") == ".txt"
    
    def test_ensure_directory(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new_directory"
            
            # Directory doesn't exist initially
            assert not new_dir.exists()
            
            # Create directory
            ensure_directory(new_dir)
            assert new_dir.exists()
            assert new_dir.is_dir()
            
            # Create nested directory
            nested_dir = new_dir / "nested" / "deep"
            ensure_directory(nested_dir)
            assert nested_dir.exists()
            assert nested_dir.is_dir() 