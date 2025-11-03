# 🔧 Development 
<img src="https://github.com/terracoil/freyja/raw/main/docs/freyja-thumb.png" alt="Freyja" title="Freyja" width="300"/>

## 📍 Navigation
**You are here**: Development Overview

**Parents**:
- [🏠 Main README](../../README.md) - Project overview and quick start
- [📚 Documentation Hub](../README.md) - Complete documentation index

**Children**:
- **[🤝 Contributing](contributing.md)** - How to contribute to Freyja

**Related**:
- **[🏗️ Architecture (CLAUDE.md)](../../CLAUDE.md)** - Codebase structure and design
- **[🧪 Testing (CLAUDE.md)](../../CLAUDE.md)** - Testing guidelines and strategies

---

Documentation for contributors and developers working on Freyja.

## 📑 Table of Contents
* [🤝 For Contributors](#-for-contributors)
* [🏁 Quick Start for Contributors](#-quick-start-for-contributors)
* [📋 Development Guidelines](#-development-guidelines)
* [💡 Getting Help](#-getting-help)
* [📖 Next Steps](#-next-steps)

---

## 🤝 For Contributors

### 🤝 [Contributing](contributing.md)
How to contribute to Freyja.
- Setting up development environment
- Code style guidelines
- Submitting pull requests
- Issue reporting guidelines
- Community standards

### 🏗️ Architecture
Understanding the codebase structure - see [CLAUDE.md](../../CLAUDE.md).
- Project organization
- Core components
- Design decisions
- Extension points
- Future roadmap

### 🧪 Testing
Testing guidelines and strategies - see [CLAUDE.md](../../CLAUDE.md).
- Running the test suite
- Writing new tests
- Test organization
- Coverage requirements
- CI/CD pipeline

### 📦 Release Process
How releases are managed.
- Version numbering
- Release checklist
- Publishing to PyPI
- Documentation updates
- Announcement process

## 🏁 Quick Start for Contributors

### Development Setup
### Using Poetry (Recommended)

1. Install Poetry:

```bash
# Install pipx
brew update && brew upgrade pipx
# Install poetry
pipx install poetry
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

### Using Poetry (Recommended)

1. Install Poetry:

```shell
# Install pipx
brew update && brew upgrade pipx
# Install poetry
pipx install poetry
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


### Project Structure
```
freyja/
├── freya/          # Source code
│   ├── __init__.py
│   └── cli.py
├── tests/             # Test suite
│   ├── conftest.py
│   └── test_*.py
├── docs/              # Documentation
├── freyja/            # Source code and examples
│   ├── examples/      # Example CLIs
├── pyproject.toml     # Project configuration
└── README.md          # Project README
```

## Verify Installation

### Check Version

```python
import src

print(src.__version__)
```


### Key Development Commands

**Testing**
```bash
# Run all tests with coverage
./bin/dev-tools test run

# Run specific test file
poetry run pytest tests/test_cli.py -v

# Run with debugging
poetry run pytest -vv --tb=short
```

**Code Quality**
```bash
# Run all checks
./bin/lint.sh

# Format code
poetry run black src tests

# Type checking
poetry run mypy src --strict
```

**Building**
```bash
# Build distribution packages
poetry build

# Install locally for testing
poetry install
```

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 with Black formatting
- Use type hints for all functions
- Write descriptive docstrings
- Keep functions focused and testable

### Commit Messages
- Use conventional commits format
- Include issue numbers when applicable
- Write clear, descriptive messages
- Separate concerns in commits

### Testing Philosophy
- Write tests for new features
- Maintain high test coverage (>90%)
- Test edge cases and errors
- Use fixtures for common setups

## 💡 Getting Help

### For Contributors
- Open an [Issue](https://github.com/terracoil/freyja/issues) for questions
- Join our [Discord](#) community (coming soon)
- Check existing [Issues](https://github.com/terracoil/freyja/issues)
- Read the Architecture guide in [CLAUDE.md](../../CLAUDE.md)

### Maintainer Contacts
- **Steven** - Project Lead
- **Contributors** - See [contributors on GitHub](https://github.com/terracoil/freyja/graphs/contributors)

## 📖 Next Steps

- Read [Contributing Guidelines](contributing.md)
- Understand the Architecture (see [CLAUDE.md](../../CLAUDE.md))
- Set up Testing (see [CLAUDE.md](../../CLAUDE.md))
- Learn the Release Process (see [CLAUDE.md](../../CLAUDE.md))

---

**Ready to contribute?** Check out [good first issues](https://github.com/terracoil/freyja/labels/good%20first%20issue) 🌟
