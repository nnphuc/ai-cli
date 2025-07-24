# AI CLI Documentation

Welcome to the AI CLI documentation! This guide will help you understand and use the AI CLI tool effectively.

## Table of Contents

- [Installation](installation.md) - How to install and set up AI CLI
- [Configuration](configuration.md) - Configuration options and environment variables
- [Usage](usage.md) - How to use the different commands
- [API Reference](api-reference.md) - Detailed API documentation
- [Examples](examples.md) - Common use cases and examples
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Contributing](contributing.md) - How to contribute to the project

## Quick Start

1. **Install the tool:**
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```

2. **Set up your API keys:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Start using AI CLI:**
   ```bash
   # Ask a question
   ai-cli ask "What is the capital of France?"
   
   # Start an interactive chat
   ai-cli chat
   
   # Generate code
   ai-cli code "Write a Python function to calculate fibonacci numbers"
   ```

## Features

- 🤖 Support for multiple AI providers (OpenAI, Anthropic)
- 💬 Interactive chat mode with command history
- 📝 Code generation and explanation
- 🔧 Rich command-line interface
- ⚙️ Configurable settings and API keys
- 🎨 Beautiful terminal UI with syntax highlighting
- 💾 Response caching for efficiency

## Getting Help

- Run `ai-cli --help` for general help
- Run `ai-cli <command> --help` for command-specific help
- Check the [troubleshooting guide](troubleshooting.md) for common issues
- Open an issue on GitHub for bugs or feature requests 