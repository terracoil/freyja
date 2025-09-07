![Freyja Action](https://github.com/terracoil/freyja/raw/main/docs/freyja-action.png)
# Development

[↑ Documentation Hub](../README.md)

Documentation for contributors and developers working on freyja.

## For Contributors

### 🤝 [Contributing](contributing.md)
How to contribute to freyja.
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

## Quick Start for Contributors

### Development Setup
```bash
# Clone the repository
git clone https://github.com/terracoil/freyja.git
cd freyja

# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run linters
poetry run ruff check .
poetry run mypy src

# Install pre-commit hooks
poetry run pre-commit install
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
├── examples/          # Example CLIs
├── pyproject.toml     # Project configuration
└── README.md          # Project README
```

### Key Development Commands

**Testing**
```bash
# Run all tests with coverage
./bin/test.sh

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

## Development Guidelines

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

## Getting Help

### For Contributors
- Open an [Issue](https://github.com/terracoil/freyja/issues) for questions
- Join our [Discord](#) community (coming soon)
- Check existing [Issues](https://github.com/terracoil/freyja/issues)
- Read the Architecture guide in [CLAUDE.md](../../CLAUDE.md)

### Maintainer Contacts
- **Steven** - Project Lead
- **Contributors** - See [contributors on GitHub](https://github.com/terracoil/freyja/graphs/contributors)

## Next Steps

- Read [Contributing Guidelines](contributing.md)
- Understand the Architecture (see [CLAUDE.md](../../CLAUDE.md))
- Set up Testing (see [CLAUDE.md](../../CLAUDE.md))
- Learn the Release Process (see [CLAUDE.md](../../CLAUDE.md))

---

**Ready to contribute?** Check out [good first issues](https://github.com/terracoil/freyja/labels/good%20first%20issue)