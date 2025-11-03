# Freyja ⚡
<img src="https://github.com/terracoil/freyja/raw/main/docs/freyja.png" alt="Freyja" title="Freyja" width="400"/>

_**[Freyja](https://pypi.org/project/freyja/)** is a no-dependency, zero-configuration CLI tool to build command-line interfaces purely from python classes._

## Summary

Transform your Python classes into powerful command-line applications in seconds! 

**[Freyja](https://pypi.org/project/freyja/)** uses your class to generate a powerful CLI:
* Methods become commands with automatic usage, help and validation.  
* Type annotations and docstrings are used to enhance CLI functionality. 
* Inner classes can be used to organize commands into groups. 

**⚠️ Important:** All constructor parameters MUST have default values for CLI generation to work. Parameters without defaults will cause CLI creation to fail.

## 🎉 What's New in v1.1.5

### Enhanced Features
- **🔄 ExecutionSpinner**: Beautiful progress indicators with command context tracking
- **🎨 Theme Adjustments**: Dynamic theme customization with multiple adjustment strategies
- **📊 Dependency Analysis**: New tools for analyzing project dependencies
- **🛡️ Improved Error Handling**: Better validation and clearer error messages
- **⚡ Performance Improvements**: Faster command discovery and execution

## Table of Contents
* [🎉 What's New](#-whats-new-in-v115)  
* [🚀 Why Freyja?](#-why-freyja)
* [⚡ Quick Start](#-quick-start)
* [🏗️ Class-based CLI](#️-class-based-cli)
  * [Direct Methods Pattern](#direct-methods-pattern)
  * [Inner Classes Pattern](#inner-classes-pattern)
  * [🔄 ExecutionSpinner](#-executionspinner-new)
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

    def __init__(self, default_name: str = "World", verbose: bool = False):
        """Initialize greeter with default name."""
        self.default_name = default_name
        self.verbose = verbose

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

# With verbose mode (shows execution spinner in v1.1.5+)
python script.py --verbose greet --name Bob
# Output: Executing greet [greet:name:Bob]
#         Hello, Bob!
```


## 🏗️ Class-based CLI

Freyja transforms your Python classes into powerful CLI applications. Supports flexible patterns for organizing your commands:

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

Organize complex applications with hierarchical command structure using space-separated commands:

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

**Usage with Hierarchical Commands:**
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

**⚠️ Important:** Freyja uses ONLY hierarchical space-separated commands. Flat dash-separated syntax (e.g., `database--migrate` or `system__completion__install`) is NOT supported.

### 🔄 ExecutionSpinner (NEW)

Freyja v1.1.5+ includes an enhanced execution feedback system that provides visual progress indicators:

```python
from freyja import FreyjaCLI
from freyja.utils.spinner import ExecutionSpinner, CommandContext
import time


class DataProcessor:
    """Data processing with progress feedback."""
    
    def __init__(self, verbose: bool = False):
        """Initialize with verbose mode support."""
        self.verbose = verbose
    
    def process_large_file(self, input_file: str, chunk_size: int = 1024) -> None:
        """Process a large file with progress indication."""
        # ExecutionSpinner is automatically integrated when verbose=True
        print(f"Processing {input_file} in {chunk_size}-byte chunks")
        
        # Simulate processing
        for i in range(5):
            time.sleep(0.5)
            print(f"  Processed chunk {i+1}/5")
        
        print("✓ Processing complete!")


if __name__ == '__main__':
    cli = FreyjaCLI(DataProcessor, title="Data Processor")
    cli.run()
```

**Usage with ExecutionSpinner:**
```bash
# Verbose mode shows execution context
python processor.py --verbose process-large-file input.csv --chunk-size 2048
# Output: Executing process-large-file [positional:0:input.csv, process-large-file:chunk_size:2048]
#         Processing input.csv in 2048-byte chunks
#         ...

# Normal mode (no spinner for quick operations)
python processor.py process-large-file input.csv
```

**Key ExecutionSpinner Features:**
- **Automatic Integration**: Works with any Freyja CLI when `verbose=True`
- **Command Context**: Shows namespace, command, and all arguments
- **Thread-Safe**: Handles concurrent operations properly
- **Custom Status**: Can augment status during execution
- **Clean Output**: Proper cleanup on success or failure

## ✨ Key Features

🚀 **Zero Configuration** - Works out of the box with just type annotations
⚡ **Lightning Fast** - No runtime dependencies, minimal overhead
🎯 **Type Safe** - Automatic validation from your type hints
🔄 **ExecutionSpinner** - Beautiful progress indicators with command context (v1.1.5+)
🛡️ **Guard Clauses** - Built-in parameter validation with declarative guards
📚 **Auto Documentation** - Help text generated from your docstrings
🎨 **Beautiful Output** - Professional themes with dynamic adjustment capabilities
🔧 **Flexible Architecture** - Direct methods or inner class patterns
📦 **No Dependencies** - Uses only Python standard library
🌈 **Shell Completion** - Bash, Zsh, Fish, and PowerShell support
📊 **Dependency Analysis** - Built-in tools for analyzing project dependencies (v1.1.5+)
✅ **Production Ready** - Battle-tested in enterprise applications  

## 📚 Documentation

**[📖 Complete Documentation Hub](docs/README.md)** - Everything you need to master Freyja

### Quick Links
* **[🚀 Getting Started](docs/getting-started/README.md)** - Installation and first steps
* **[👤 User Guide](docs/user-guide/README.md)** - Comprehensive guides for class-based CLI patterns
* **[⚙️ Features](docs/features/README.md)** - Type annotations, themes, completion, ExecutionSpinner, and more
* **[📋 Examples & Best Practices](docs/guides/README.md)** - Real-world examples and patterns
* **[🔄 Migration Guide](docs/guides/README.md)** - Upgrading from older versions
* **[❓ FAQ](docs/faq.md)** - Frequently asked questions
* **[🔧 API Reference](docs/reference/README.md)** - Complete API documentation

### New in v1.1.5 Documentation
* **[ExecutionSpinner Guide](docs/features/execution-spinner.md)** - Progress indication system
* **[Theme System](docs/features/themes.md)** - Dynamic theme customization
* **[Dependency Analysis](docs/features/README.md)** - Project dependency tools

## 🛠️ Development
See [Development Environment Setup](docs/development/README.md#development-setup) for detailed instructions.

**[📖 Development Guide](CLAUDE.md)** - Comprehensive guide for contributors

### Development Commands

```bash
poetry install                    # Install dependencies
./bin/dev-tools test run          # Run tests with coverage
./bin/dev-tools build lint        # Run all linters and formatters
./bin/dev-tools build compile     # Build package
./bin/dev-tools build publish     # Publish to PyPI (maintainers)
./bin/dev-tools build tag-version # Create version tags
```

## ⚙️ Requirements

* **Python 3.13.5+** (recommended) or Python 3.8+
* **Zero runtime dependencies** - uses only Python standard library
* **Type annotations required** - for automatic CLI generation
* **Constructor defaults required** - all constructor parameters must have default values
* **Docstrings recommended** - for automatic help text generation

### Command Syntax Rules

✅ **CORRECT - Hierarchical Commands:**
```bash
my_cli database migrate             # Hierarchical with spaces
my_cli system completion install    # Multi-level hierarchy
my_cli projects create              # Clean and intuitive
```

❌ **INCORRECT - Forbidden Syntax:**
```bash
my_cli database--migrate            # Double-dash syntax NOT supported
my_cli system__completion__install  # Dunder syntax NOT supported
my_cli data-ops--process           # Mixed syntax NOT supported
```

---

**Ready to transform your Python code into powerful CLIs?**

```bash
pip install freyja
# Start building amazing command-line tools in minutes! ⚡
```

**[📚 Get Started Now →](docs/getting-started/README.md)** | **[🎉 What's New →](docs/guides/README.md)**
