![Freyja](https://github.com/terracoil/freyja/raw/main/docs/freyja.png)

# Freyja ⚡
**No-dependency, zero-configuration CLI tool to build command-line interfaces purely from your code.**

## CHECK OUT https://pypi.org/project/freyja/

Transform your Python classes into powerful command-line applications in seconds! Freyja uses introspection and type annotations to automatically generate professional CLIs with zero configuration required.

**⚠️ Important:** All constructor parameters MUST have default values for CLI generation to work. Parameters without defaults will cause CLI creation to fail.

## Table of Contents
* [🚀 Why Freyja?](#-why-freyja)
* [⚡ Quick Start](#-quick-start)
* [🏗️ Class-based CLI](#️-class-based-cli)
  * [Direct Methods Pattern](#direct-methods-pattern)
  * [Inner Classes Pattern](#inner-classes-pattern)
* [✨ Key Features](#-key-features)
* [📚 Documentation](#-documentation)
* [🛠️ Development](#️-development)
* [⚙️ Requirements](#️-requirements)

## 🚀 Why Freyja?

**Build CLIs in under 5 minutes!** No configuration files, no complex setup, no learning curve. Just add type annotations to your class methods and Freyja does the rest.

```bash
pip install freyja
# That's it! No dependencies, no configuration needed.
```

**Before Freyja:**
```bash
python script.py --config-file /path/to/config --database-host localhost --database-port 5432 --username admin --password secret --table-name users --action create --data '{"name": "Alice", "email": "alice@example.com"}'
```

**After Freyja:**
```bash
python script.py database create-user --name Alice --email alice@example.com
# Global config handled automatically, clean syntax, built-in help
```

## ⚡ Quick Start

**Step 1:** Install Freyja
```bash
pip install freyja
```

**Step 2:** Create a class with typed methods
```python
from freyja import FreyjaCLI


class Greeter:
    """Simple greeting application."""

    def __init__(self, default_name: str = "World"):
        """Initialize greeter with default name."""
        self.default_name = default_name

    def greet(self, name: str = None, excited: bool = False) -> None:
        """Greet someone by name."""
        actual_name = name or self.default_name
        greeting = f"Hello, {actual_name}!"
        if excited:
            greeting += " 🎉"
        print(greeting)
```

**Step 3:** Add 3 lines of Freyja code
```python
if __name__ == '__main__':
    cli = FreyjaCLI(Greeter, title="My CLI")
    cli.run()
```

**Step 4:** Use your new CLI!
```bash
python script.py greet --name Alice --excited
# Output: Hello, Alice! 🎉

python script.py --help
# Automatic help generation with beautiful formatting
```


## 🏗️ Class-based CLI

Freyja transforms your Python classes into powerful CLI applications. Supports two flexible patterns:

### Direct Methods Pattern

Simple and clean - each method becomes a command:

```python
# calculator.py
from freyja import FreyjaCLI


class Calculator:
    """Advanced calculator with memory and history."""

    def __init__(self, precision: int = 2, memory_enabled: bool = True):
        """Initialize calculator with global settings."""
        self.precision = precision
        self.memory = 0 if memory_enabled else None

    def add(self, a: float, b: float, store_result: bool = False) -> None:
        """Add two numbers together."""
        result = round(a + b, self.precision)
        print(f"{a} + {b} = {result}")
        
        if store_result and self.memory is not None:
            self.memory = result
            print(f"Result stored in memory: {result}")

    def multiply(self, a: float, b: float) -> None:
        """Multiply two numbers."""
        result = round(a * b, self.precision)
        print(f"{a} × {b} = {result}")


if __name__ == '__main__':
    cli = FreyjaCLI(Calculator, title="Advanced Calculator")
    cli.run()
```

**Usage:**
```bash
python calculator.py --precision 4 add 3.14159 --b 2.71828 --store-result
# Output: 3.14159 + 2.71828 = 5.8599
#         Result stored in memory: 5.8599
```

### Inner Classes Pattern

Organize complex applications with hierarchical command structure (e.g., `group subgroup command`):

```python
# project_manager.py
from freyja import FreyjaCLI
from pathlib import Path


class ProjectManager:
    """Complete project management suite with organized command structure."""

    def __init__(self, config_file: str = "config.json", debug: bool = False):
        """Initialize with global settings."""
        self.config_file = config_file
        self.debug = debug

    class Database:
        """Database operations and management."""

        def __init__(self, connection_string: str = "sqlite:///projects.db", timeout: int = 30):
            """Initialize database connection."""
            self.connection_string = connection_string
            self.timeout = timeout

        def migrate(self, version: str = "latest", dry_run: bool = False) -> None:
            """Run database migrations."""
            action = "Would run" if dry_run else "Running"
            print(f"{action} migration to version: {version}")
            print(f"Connection: {self.connection_string}")

        def backup(self, output_path: Path, compress: bool = True) -> None:
            """Create database backup."""
            compression = "compressed" if compress else "uncompressed"
            print(f"Creating {compression} backup at: {output_path}")

    class Projects:
        """Project creation and management operations."""

        def __init__(self, workspace: str = "./projects", auto_save: bool = True):
            """Initialize project operations."""
            self.workspace = workspace
            self.auto_save = auto_save

        def create(self, name: str, template: str = "basic", description: str = "") -> None:
            """Create a new project from template."""
            print(f"Creating project '{name}' using '{template}' template")
            print(f"Workspace: {self.workspace}")
            print(f"Description: {description}")
            print(f"Auto-save: {'enabled' if self.auto_save else 'disabled'}")

        def deploy(self, project_name: str, environment: str = "staging", force: bool = False) -> None:
            """Deploy project to specified environment."""
            action = "Force deploying" if force else "Deploying"
            print(f"{action} {project_name} to {environment}")


if __name__ == '__main__':
    cli = FreyjaCLI(ProjectManager, title="Project Management Suite")
    cli.run()
```

**Usage:**
```bash
# Global + Sub-global + Command arguments (hierarchical structure)
python project_manager.py --config-file prod.json --debug \
  database migrate --timeout 60 --version 2.1.0 --dry-run

# Create new project with custom workspace
python project_manager.py projects create --workspace /prod/projects --auto-save \
  --name "web-app" --template "react" --description "Production web application"

# Deploy with force flag
python project_manager.py projects deploy --project-name web-app --environment production --force

# Beautiful help shows all commands organized by group
python project_manager.py --help
```

## ✨ Key Features

🚀 **Zero Configuration** - Works out of the box with just type annotations
⚡ **Lightning Fast** - No runtime dependencies, minimal overhead
🎯 **Type Safe** - Automatic validation from your type hints
🛡️ **Guard Clauses** - Built-in parameter validation with declarative guards
📚 **Auto Documentation** - Help text generated from your docstrings
🎨 **Beautiful Output** - Professional themes and formatting
🔧 **Flexible Architecture** - Direct methods or inner class patterns
📦 **No Dependencies** - Uses only Python standard library
🌈 **Shell Completion** - Bash, Zsh, Fish, and PowerShell support
✅ **Production Ready** - Battle-tested in enterprise applications  

## 📚 Documentation

**[📖 Complete Documentation Hub](docs/README.md)** - Everything you need to master Freyja

### Quick Links
* **[🚀 Getting Started](docs/getting-started/README.md)** - Installation and first steps
* **[👤 User Guide](docs/user-guide/README.md)** - Comprehensive guides for class-based CLI patterns
* **[⚙️ Features](docs/features/README.md)** - Type annotations, themes, completion, and more
* **[📋 Examples & Best Practices](docs/guides/README.md)** - Real-world examples and patterns
* **[❓ FAQ](docs/faq.md)** - Frequently asked questions
* **[🔧 API Reference](docs/reference/README.md)** - Complete API documentation

## 🛠️ Development

**[📖 Development Guide](CLAUDE.md)** - Comprehensive guide for contributors

### Quick Setup

```bash
# Clone and setup
git clone https://github.com/terracoil/freyja.git
cd freyja

# Install Poetry and setup environment  
curl -sSL https://install.python-poetry.org | python3 -
./bin/dev-tools setup env

# Run tests and examples
./bin/dev-tools test run
poetry run python examples/cls_example --help
```

### Development Commands

```bash
poetry install                    # Install dependencies
./bin/dev-tools test run          # Run tests with coverage
./bin/dev-tools build lint        # Run all linters and formatters
./bin/dev-tools build compile     # Build package
./bin/dev-tools project publish   # Publish to PyPI (maintainers)
./bin/dev-tools project tag       # Tag a release (Bump version to x.y.z)
```

## ⚙️ Requirements

* **Python 3.13+** (recommended) — supports **Python 3.11+**
* **Zero runtime dependencies** - uses only Python standard library
* **Type annotations required** - for automatic CLI generation
* **Docstrings recommended** - for automatic help text generation

---

**Ready to transform your Python code into powerful CLIs?**

```bash
pip install freyja
# Start building amazing command-line tools in minutes! ⚡
```

**[📚 Get Started Now →](docs/getting-started/README.md)**
