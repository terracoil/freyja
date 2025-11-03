**[← Getting Started](README.md) | [🚀 Quick Start](quick-start.md)**

# 📦 Installation Guide
<img src="https://github.com/terracoil/freyja/raw/main/docs/freyja-github.jpg" alt="Freyja" title="Freyja" height="200"/>

# Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Install from PyPI](#install-from-pypi)
  - [From GitHub](#from-github)
- [Development Setup](../development/README.md)
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
# Install from specific branch (e.g., main)
pip install git+https://github.com/terracoil/freyja.git@main

# Or add to requirements.txt
git+https://github.com/terracoil/freyja.git@main

# Or add to pyproject.toml (Poetry)
[tool.poetry.dependencies]
freyja = {git = "https://github.com/terracoil/freyja.git", branch = "main"}

# Install from main branch (latest development)
pip install git+https://github.com/terracoil/freyja.git@main
```

### Clone and Install

```bash
git clone https://github.com/terracoil/freyja.git
cd freyja
pip install .
```

### Test Basic Functionality

Create a test file `test_install.py`:

```python
from freyja import FreyjaCLI


class TestApp:
  """Test application."""
  
  def hello(self, name: str = "World"):
    """Test function."""
    print(f"Hello, {name}!")


if __name__ == "__main__":
  cli = FreyjaCLI(TestApp)
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
- [Basic Usage](basic-usage.md) - Learn the fundamentals
- [Class-based CLI](class-cli.md) - Create your first class CLI
- [Contributing](../development/contributing.md) - Setup for contributors

---
**Navigation**: [← Quick Start](quick-start.md) | [Basic Usage →](basic-usage.md)
