# auto-cli-py
Python Library that builds a complete CLI given one or more functions using introspection.

Most options are set using introspection/signature and annotation functionality, so very little configuration has to be done. The library analyzes your function signatures and automatically creates command-line interfaces with proper argument parsing, type checking, and help text generation.

## Quick Start

### Installation
```bash
# Install from PyPI
pip install auto-cli-py

# See example code and output
python examples.py
```

### Basic Usage

```python
#!/usr/bin/env python
import sys
from auto_cli.cli import CLI

def greet(name: str = "World", count: int = 1):
    """Greet someone multiple times."""
    for _ in range(count):
        print(f"Hello, {name}!")

if __name__ == '__main__':
    fn_opts = {
        'greet': {'description': 'Greet someone'}
    }
    cli = CLI(sys.modules[__name__], function_opts=fn_opts, title="My CLI")
    cli.display()
```

This automatically generates a CLI with:
- `--name` parameter (string, default: "World")  
- `--count` parameter (integer, default: 1)
- Proper help text and error handling

## Development

This project uses Poetry for dependency management and modern Python tooling.

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/tangledpath/auto-cli-py.git
cd auto-cli-py

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Setup development environment
./scripts/setup-dev.sh
```

### Development Commands

```bash
# Install dependencies
poetry install

# Run tests
./scripts/test.sh
# Or directly: poetry run pytest

# Run linting and formatting
./scripts/lint.sh

# Run examples
poetry run python examples.py

# Build package
poetry build

# Publish to PyPI (maintainers only)
./scripts/publish.sh
```

### Code Quality

The project uses several tools for code quality:
- **Black**: Code formatting
- **Ruff**: Fast Python linter
- **MyPy**: Type checking  
- **Pylint**: Additional linting
- **Pre-commit**: Automated checks on commit

### Testing

```bash
# Run all tests with coverage
poetry run pytest

# Run specific test file
poetry run pytest tests/test_cli.py

# Run with verbose output
poetry run pytest -v
```

### Requirements

- Python 3.13.5+
- No runtime dependencies (uses only standard library)

