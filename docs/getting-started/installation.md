![Freyja Thumb](https://github.com/terracoil/freyja/blob/f7f3411a3ea7346d9294e394629e78f078352579/freyja-thumb.png)

# 📦 Installation Guide

[← Getting Started](README.md) | [🚀 Quick Start](quick-start.md)

# Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Install from PyPI](#install-from-pypi)
  - [From GitHub](#from-github)
- [Development Setup](#development-setup)
- [Verify Installation](#verify-installation)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Optional: Poetry for development

## Installation

### Install from PyPI
_The simplest way to install freyja:_
```bash
pip install freyja
```

#### Install with Extras
_Install with shell completion support:_

```bash
pip install "freyja[completion]"
```

#### Install specific version:

```bash
pip install freyja==0.5.0
```

### From GitHub

#### From GitHub (Latest)

```bash
pip install git+https://github.com/terracoil/freyja.git
```

#### From GitHub (Specific Branch)

```bash
# Install from specific branch (e.g., feature/modernization)
pip install git+https://github.com/terracoil/freyja.git@feature/modernization

# Or add to requirements.txt
git+https://github.com/terracoil/freyja.git@feature/modernization

# Or add to pyproject.toml (Poetry)
[tool.poetry.dependencies]
freyja = {git = "https://github.com/terracoil/freyja.git", branch = "feature/modernization"}

# Install from main branch (latest development)
pip install git+https://github.com/terracoil/freyja.git@main
```

### Clone and Install

```bash
git clone https://github.com/terracoil/freyja.git
cd freyja
pip install .
```

## Development Setup

### Using Poetry (Recommended)

1. Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone the repository:
```bash
git clone https://github.com/terracoil/freyja.git
cd freyja
```

3. Install dependencies:
```bash
poetry install --with dev
```

4. Activate the virtual environment:
```bash
poetry shell
```

### Using pip

1. Clone the repository:
```bash
git clone https://github.com/terracoil/freyja.git
cd freyja
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

## Verify Installation

### Check Version

```python
import src

print(src.__version__)
```

### Test Basic Functionality

Create a test file `test_install.py`:

```python
from src import CLI


def hello(name: str = "World"):
  """Test function."""
  print(f"Hello, {name}!")


if __name__ == "__main__":
  import sys

  cli = CLI.from_module(sys.modules[__name__])
  cli.run()
```

Run it:

```bash
python test_install.py hello --name "Install Test"
```

Expected output:
```
Hello, Install Test!
```

## Troubleshooting

### Common Issues

#### Import Error

**Problem**: `ModuleNotFoundError: No module named 'freya'`

**Solution**: Ensure freyja is installed in the active environment:
```bash
pip list | grep freyja
```

#### Python Version Error

**Problem**: `ERROR: freyja requires Python >=3.8`

**Solution**: Check your Python version:
```bash
python --version
```

Update Python if needed or use a virtual environment with the correct version.

#### Permission Error

**Problem**: `Permission denied` during installation

**Solution**: Use user installation:
```bash
pip install --user freyja
```

Or use a virtual environment (recommended).

### Getting Help

If you encounter issues:

1. Check [GitHub Issues](https://github.com/terracoil/freyja/issues)
2. Search for similar problems
3. Create a new issue with:
   - Python version
   - freyja version
   - Complete error message
   - Minimal reproducible example

## See Also

- [Quick Start Guide](quick-start.md) - Get started quickly
- [Module-based CLI](module-cli.md) - Create your first module CLI
- [Class-based CLI](class-cli.md) - Create your first class CLI
- [Contributing](../development/contributing.md) - Setup for contributors

---
**Navigation**: [← Quick Start](quick-start.md) | [Module-based CLI →](module-cli.md)
