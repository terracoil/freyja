# Installation Guide

[← Back to Help](../help.md) | [← Quick Start](quick-start.md)

## Table of Contents
- [Prerequisites](#prerequisites)
- [Standard Installation](#standard-installation)
- [Development Installation](#development-installation)
- [Poetry Installation](#poetry-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

**Python Version**: auto-cli-py requires Python 3.8 or higher.

```bash
# Check your Python version
python --version
# or
python3 --version
```

**Dependencies**: All required dependencies are automatically installed with the package.

## Standard Installation

### From PyPI (Recommended)

The easiest way to install auto-cli-py:

```bash
pip install auto-cli-py
```

### From GitHub

Install the latest development version:

```bash
pip install git+https://github.com/tangledpath/auto-cli-py.git
```

### Specific Version

Install a specific version:

```bash
pip install auto-cli-py==1.0.0
```

### Upgrade Existing Installation

Update to the latest version:

```bash
pip install --upgrade auto-cli-py
```

## Development Installation

For contributing to auto-cli-py or running from source:

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/tangledpath/auto-cli-py.git
cd auto-cli-py

# Install in development mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Using the Setup Script

For a complete development environment:

```bash
./bin/setup-dev.sh
```

This script will:
- Install Poetry (if needed)
- Set up the virtual environment  
- Install all dependencies
- Configure pre-commit hooks

## Poetry Installation

If you're using Poetry for dependency management:

### Add to Existing Project

```bash
poetry add auto-cli-py
```

### Development Dependencies

```bash
poetry add --group dev auto-cli-py
```

### From Source with Poetry

```bash
# Clone repository
git clone https://github.com/tangledpath/auto-cli-py.git
cd auto-cli-py

# Install with Poetry
poetry install

# Activate virtual environment
poetry shell
```

## Verification

### Test Installation

Verify auto-cli-py is properly installed:

```python
# test_installation.py
from auto_cli import CLI
import sys


def hello(name: str = "World"):
  """Test function for installation verification."""
  print(f"Hello, {name}! Auto-CLI-Py is working!")


cli = CLI(sys.modules[__name__])
cli.display()
```

```bash
python test_installation.py hello
# Expected output: Hello, World! Auto-CLI-Py is working!
```

### Check Version

```python
import auto_cli
print(auto_cli.__version__)
```

### Run Examples

Try the included examples:

```bash
# Download examples (if not already available)
curl -O https://raw.githubusercontent.com/tangledpath/auto-cli-py/main/examples.py

# Run examples
python examples.py hello --name "Installation Test"
```

## Troubleshooting

### Common Issues

**ImportError: No module named 'auto_cli'**
```bash
# Ensure auto-cli-py is installed in the current environment
pip list | grep auto-cli-py

# If missing, reinstall
pip install auto-cli-py
```

**Permission Errors (Linux/macOS)**
```bash
# Use --user flag for user-local installation
pip install --user auto-cli-py

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
pip install auto-cli-py
```

**Outdated pip**
```bash
# Update pip first
python -m pip install --upgrade pip
pip install auto-cli-py
```

### Virtual Environment Issues

**Creating a Virtual Environment:**
```bash
# Python 3.8+
python -m venv auto-cli-env
source auto-cli-env/bin/activate  # Linux/macOS
# or
auto-cli-env\Scripts\activate     # Windows

pip install auto-cli-py
```

**Poetry Environment Issues:**
```bash
# Clear Poetry cache
poetry cache clear --all .

# Reinstall dependencies
poetry install --no-cache
```

### Development Setup Issues

**Pre-commit Hook Errors:**
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**Missing Development Tools:**
```bash
# Install development dependencies
pip install -e ".[dev]"

# Or with Poetry
poetry install --with dev
```

### Platform-Specific Issues

**Windows PowerShell Execution Policy:**
```powershell
# If you get execution policy errors
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**macOS Catalina+ Permission Issues:**
```bash
# If you get permission errors on newer macOS versions
pip install --user auto-cli-py
```

## Next Steps

Once installation is complete:

1. **[Quick Start Guide](quick-start.md)** - Create your first CLI
2. **[Basic Usage](basic-usage.md)** - Learn core concepts  
3. **[Examples](../guides/examples.md)** - See real-world applications

## See Also
- [Quick Start Guide](quick-start.md) - Get started in 5 minutes
- [Basic Usage](basic-usage.md) - Core usage patterns
- [Development Guide](../development/contributing.md) - Contributing to auto-cli-py

---
**Navigation**: [← Quick Start](quick-start.md) | [Basic Usage →](basic-usage.md)  
**Parent**: [Help](../help.md)  
**Related**: [Contributing](../development/contributing.md) | [Testing](../development/testing.md)
