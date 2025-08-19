# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an active Python library (`auto-cli-py`) that automatically builds complete CLI commands from Python functions using introspection and type annotations. The library generates argument parsers and command-line interfaces with minimal configuration by analyzing function signatures. Published on PyPI at https://pypi.org/project/auto-cli-py/

## Development Environment Setup

### Poetry Environment (Recommended)
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Setup development environment
./scripts/setup-dev.sh

# Or manually:
poetry install --with dev
poetry run pre-commit install
```

### Alternative Installation
```bash
# Install from PyPI
pip install auto-cli-py

# Install from GitHub (specific branch)
pip install git+https://github.com/tangledpath/auto-cli-py.git@branch-name
```

## Common Commands

### Testing
```bash
# Run all tests with coverage
./scripts/test.sh
# Or: poetry run pytest

# Run specific test file
poetry run pytest tests/test_cli.py

# Run with verbose output
poetry run pytest -v --tb=short
```

### Code Quality
```bash
# Run all linters and formatters
./scripts/lint.sh

# Individual tools:
poetry run ruff check .              # Fast linting
poetry run black --check .          # Format checking
poetry run mypy auto_cli             # Type checking
poetry run pylint auto_cli           # Additional linting

# Auto-format code
poetry run black .
poetry run ruff check . --fix
```

### Build and Deploy
```bash
# Build package
poetry build

# Publish to PyPI (maintainers only)
./scripts/publish.sh
# Or: poetry publish

# Install development version
poetry install
```

### Examples
```bash
# Run example CLI
poetry run python examples.py

# See help
poetry run python examples.py --help

# Try example commands
poetry run python examples.py foo
poetry run python examples.py train --epochs 50 --seed 1234
poetry run python examples.py count_animals --count 10 --animal CAT
```

## Architecture

### Core Components

- **`auto_cli/cli.py`**: Main CLI class that handles:
  - Function signature introspection via `inspect` module
  - Automatic argument parser generation using `argparse`
  - Type annotation parsing (str, int, float, bool, enums)
  - Default value handling and help text generation
  
- **`auto_cli/__init__.py`**: Package initialization (minimal)

### Key Architecture Patterns

**Function Introspection**: The CLI class uses Python's `inspect.signature()` to analyze function parameters, their types, and default values to automatically generate CLI arguments.

**Type-Driven CLI Generation**: 
- Function annotations (str, int, float, bool) become argument types
- Enum types become choice arguments
- Default values become argument defaults
- Parameter names become CLI option names (--param_name)

**Subcommand Architecture**: Each function becomes a subcommand with its own help and arguments.

### Usage Pattern
```python
# Define functions with type hints
def my_function(param1: str = "default", count: int = 5):
    # Function implementation
    pass

# Setup CLI
fn_opts = {
    'my_function': {'description': 'Description text'}
}
cli = CLI(sys.modules[__name__], function_opts=fn_opts, title="My CLI")
cli.display()
```

## File Structure

- `auto_cli/cli.py` - Core CLI generation logic
- `examples.py` - Working examples showing library usage
- `pyproject.toml` - Poetry configuration and metadata
- `tests/` - Test suite with pytest
- `scripts/` - Development helper scripts
- `.pre-commit-config.yaml` - Code quality automation

## Testing Notes

- Uses pytest framework with coverage reporting
- Test configuration in `pyproject.toml`
- Tests located in `tests/` directory
- Run with `./scripts/test.sh` or `poetry run pytest`