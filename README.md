# AI CLI

A powerful AI-powered command line interface tool that helps you interact with various AI models directly from your terminal.

## Features

- 🤖 Support for multiple AI providers (OpenAI, Anthropic)
- 💬 Interactive chat mode
- 📝 Code generation and explanation
- 🔧 Command-line interface with rich output
- ⚙️ Configurable settings and API keys
- 🎨 Beautiful terminal UI with syntax highlighting

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-cli.git
cd ai-cli
```

2. Create a virtual environment and install dependencies:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. Install development dependencies (optional):
```bash
uv pip install -e ".[dev]"
```

4. Set up your API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Create a `.env` file in the project root with your API keys:

```env
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Default model (optional)
DEFAULT_MODEL=gpt-4
```

## Usage

### Basic Usage

```bash
# Start an interactive chat session
ai-cli chat

# Ask a single question
ai-cli ask "What is the capital of France?"

# Generate code
ai-cli code "Write a Python function to calculate fibonacci numbers"

# Explain code
ai-cli explain "def fibonacci(n): return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)"
```

### Available Commands

- `ai-cli chat` - Start an interactive chat session
- `ai-cli ask <question>` - Ask a single question
- `ai-cli code <prompt>` - Generate code based on a prompt
- `ai-cli explain <code>` - Explain the given code
- `ai-cli config` - Manage configuration settings
- `ai-cli --help` - Show help information

### Options

- `--model <model>` - Specify the AI model to use
- `--provider <provider>` - Specify the AI provider (openai, anthropic)
- `--temperature <float>` - Set the temperature for responses (0.0-2.0)
- `--max-tokens <int>` - Set maximum tokens for responses
- `--verbose` - Enable verbose output

## Development

### Project Structure

```
ai-cli/
├── ai_cli/                 # Main package
│   ├── __init__.py
│   ├── main.py            # CLI entry point
│   ├── core/              # Core functionality
│   │   ├── __init__.py
│   │   ├── client.py      # AI client implementations
│   │   ├── config.py      # Configuration management
│   │   └── utils.py       # Utility functions
│   ├── commands/          # CLI commands
│   │   ├── __init__.py
│   │   ├── chat.py        # Chat command
│   │   ├── ask.py         # Ask command
│   │   ├── code.py        # Code generation command
│   │   └── config.py      # Config command
│   └── models/            # Data models
│       ├── __init__.py
│       ├── chat.py        # Chat models
│       └── config.py      # Configuration models
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_core/
│   ├── test_commands/
│   └── test_models/
├── docs/                  # Documentation
├── pyproject.toml         # Project configuration
├── README.md             # This file
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
└── .pre-commit-config.yaml # Pre-commit hooks
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=ai_cli

# Run specific test file
pytest tests/test_core/test_client.py
```

### Code Quality

```bash
# Format code
black ai_cli tests

# Sort imports
isort ai_cli tests

# Lint code
flake8 ai_cli tests

# Type checking
mypy ai_cli
```

### Pre-commit Hooks

Install pre-commit hooks to automatically run code quality checks:

```bash
pre-commit install
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAI](https://openai.com/) for providing the GPT models
- [Anthropic](https://www.anthropic.com/) for providing Claude models
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Typer](https://github.com/tiangolo/typer) for CLI framework 