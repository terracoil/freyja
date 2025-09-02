![Freyja](../freyja.png)

# 📚 Freyja Documentation Hub
**No-dependency, zero-configuration CLI tool to build command-line interfaces purely from your code.**

[← Back to Main README](../README.md) | [⚙️ Development Guide](../CLAUDE.md)

Welcome to the complete documentation for Freyja! Transform your Python functions and classes into powerful command-line applications in minutes.

## Table of Contents
* [🚀 Why Freyja?](#-why-freyja)
* [⚡ Quick Start](#-quick-start)
* [🗂️ Module-based CLI](#️-module-based-cli)
* [🏗️ Class-based CLI](#️-class-based-cli)
  * [Direct Methods Pattern](#direct-methods-pattern)
  * [Inner Classes Pattern](#inner-classes-pattern)
* [📊 Mode Comparison](#-mode-comparison)
* [✨ Key Features](#-key-features)
* [🎯 Getting Started](#-getting-started)
* [📖 Next Steps](#-next-steps)

# Children

### 📚 Core Documentation
* **[🚀 Getting Started](getting-started/README.md)** - Installation, quick start, and first steps with Freyja
* **[👤 User Guide](user-guide/README.md)** - Comprehensive guides for both module-based and class-based CLI patterns
* **[⚙️ Features](features/README.md)** - Type annotations, shell completion, error handling, and advanced features
* **[🔧 Advanced Topics](advanced/README.md)** - Complex patterns, performance optimization, and advanced usage
* **[📖 API Reference](reference/README.md)** - Complete API documentation and technical specifications

### 🛠️ Resources & Support
* **[📋 Guides](guides/README.md)** - Best practices, real-world examples, and troubleshooting
* **[❓ FAQ](faq.md)** - Frequently asked questions and common solutions
* **[🤝 Development](development/README.md)** - Contributing guidelines and development setup

## 🚀 Why Freyja?

**Build professional CLIs in under 5 minutes!** No configuration files, no learning curve, no dependencies. Just add type annotations to your existing Python code and Freyja automatically generates a complete command-line interface.

### Before Freyja
```python
import argparse

parser = argparse.ArgumentParser(description='Process some data')
parser.add_argument('--input', required=True, help='Input file path')
parser.add_argument('--output', default='output.json', help='Output format')
parser.add_argument('--verbose', action='store_true', help='Enable verbose mode')
args = parser.parse_args()

def process_data(input_file, output_format, verbose):
    # Your actual logic here
    pass

process_data(args.input, args.output, args.verbose)
```

### After Freyja
```python
from freyja import CLI

def process_data(input_file: str, output_format: str = "json", verbose: bool = False) -> None:
    """Process data file and convert to specified format."""
    # Your actual logic here - no argument parsing needed!
    pass

if __name__ == '__main__':
    CLI.display()  # That's it! ✨
```

## ⚡ Quick Start

**1. Install Freyja**
```bash
pip install freyja
# Zero dependencies, works instantly!
```

**2. Add type annotations to your function**
```python
def greet(name: str = "World", excited: bool = False) -> None:
    """Greet someone by name."""
    greeting = f"Hello, {name}!"
    if excited:
        greeting += " 🎉"
    print(greeting)
```

**3. Add the magic 2 lines**
```python
from freyja import CLI
CLI.display()  # Seriously, that's all! 🚀
```

**4. Use your new CLI!**
```bash
python script.py greet --name Alice --excited
# Output: Hello, Alice! 🎉

python script.py --help
# Beautiful auto-generated help with your docstring!
```

## 🗂️ Module-based CLI

**Perfect for:** Functional programming, data processing scripts, simple utilities

Transform any Python module into a CLI by treating each function as a command:

```python
# data_tools.py
from freyja import CLI


def convert_csv(input_file: str, output_format: str = "json", encoding: str = "utf-8") -> None:
    """Convert CSV file to different formats with custom encoding."""
    print(f"Converting {input_file} to {output_format} (encoding: {encoding})")
    # Your conversion logic here


def analyze_logs(log_file: str, pattern: str, max_lines: int = 1000, case_sensitive: bool = False) -> None:
    """Analyze log files for specific patterns with line limits."""
    sensitivity = "case-sensitive" if case_sensitive else "case-insensitive"
    print(f"Analyzing {log_file} for '{pattern}' ({sensitivity}, max {max_lines} lines)")
    # Your analysis logic here


def generate_report(data_dir: str, format: str = "html", include_charts: bool = True) -> None:
    """Generate comprehensive reports from data directory."""
    charts = "with charts" if include_charts else "without charts"
    print(f"Generating {format} report from {data_dir} ({charts})")
    # Your report logic here


if __name__ == '__main__':
    CLI.display()
```

**Instant CLI magic:**
```bash
# All functions become commands automatically
python data_tools.py convert-csv --input-file data.csv --output-format xml --encoding latin-1
python data_tools.py analyze-logs --log-file app.log --pattern "ERROR" --max-lines 5000 --case-sensitive
python data_tools.py generate-report --data-dir ./reports --format pdf --include-charts

# Beautiful help generated from docstrings
python data_tools.py --help
python data_tools.py convert-csv --help
```

## 🏗️ Class-based CLI

**Perfect for:** Stateful applications, complex workflows, enterprise tools

### Direct Methods Pattern

Simple and clean - each method becomes a command:

```python
# calculator.py
from freyja import CLI


class Calculator:
    """Advanced calculator with memory and precision control."""

    def __init__(self, precision: int = 2, memory_enabled: bool = True):
        """Initialize calculator with global settings."""
        self.precision = precision
        self.memory = 0 if memory_enabled else None
        self.history = []

    def add(self, a: float, b: float, store_in_memory: bool = False) -> None:
        """Add two numbers with optional memory storage."""
        result = round(a + b, self.precision)
        self.history.append(f"{a} + {b} = {result}")
        print(f"Result: {result}")
        
        if store_in_memory and self.memory is not None:
            self.memory = result
            print(f"Stored in memory: {result}")

    def multiply(self, a: float, b: float, use_memory: bool = False) -> None:
        """Multiply numbers, optionally using memory as first operand."""
        first = self.memory if use_memory and self.memory is not None else a
        result = round(first * b, self.precision)
        self.history.append(f"{first} × {b} = {result}")
        print(f"Result: {result}")

    def show_history(self, last_n: int = 10) -> None:
        """Display calculation history."""
        recent_history = self.history[-last_n:] if len(self.history) > last_n else self.history
        for entry in recent_history:
            print(entry)


if __name__ == '__main__':
    CLI.display()
```

### Inner Classes Pattern

Organize complex applications with flat double-dash commands:

```python
# project_manager.py
from freyja import CLI
from pathlib import Path


class ProjectManager:
    """Enterprise project management suite with organized flat commands."""

    def __init__(self, config_file: str = "config.json", environment: str = "development"):
        """Initialize with global configuration."""
        self.config_file = config_file
        self.environment = environment

    class Database:
        """Database operations and maintenance."""

        def __init__(self, connection_timeout: int = 30, pool_size: int = 10):
            """Database configuration settings."""
            self.connection_timeout = connection_timeout
            self.pool_size = pool_size

        def migrate(self, target_version: str = "latest", dry_run: bool = False) -> None:
            """Run database migrations to target version."""
            action = "Would migrate" if dry_run else "Migrating"
            print(f"{action} database to version {target_version}")
            print(f"Connection timeout: {self.connection_timeout}s, Pool size: {self.pool_size}")

        def backup(self, output_path: Path, compress: bool = True, include_indexes: bool = True) -> None:
            """Create comprehensive database backup."""
            compression = "compressed" if compress else "uncompressed"
            indexes = "with indexes" if include_indexes else "without indexes"
            print(f"Creating {compression} backup at {output_path} ({indexes})")

        def optimize(self, analyze_tables: bool = True, rebuild_indexes: bool = False) -> None:
            """Optimize database performance."""
            tasks = []
            if analyze_tables:
                tasks.append("analyze tables")
            if rebuild_indexes:
                tasks.append("rebuild indexes")
            print(f"Optimizing database: {', '.join(tasks)}")

    class Deploy:
        """Application deployment and management."""

        def __init__(self, build_timeout: int = 300, parallel_jobs: int = 4):
            """Deployment configuration settings."""
            self.build_timeout = build_timeout
            self.parallel_jobs = parallel_jobs

        def build(self, target: str = "production", clean: bool = False, skip_tests: bool = False) -> None:
            """Build application for deployment."""
            clean_flag = " (clean build)" if clean else ""
            test_flag = " (skipping tests)" if skip_tests else ""
            print(f"Building for {target}{clean_flag}{test_flag}")
            print(f"Timeout: {self.build_timeout}s, Jobs: {self.parallel_jobs}")

        def deploy(self, environment: str, version: str = "latest", force: bool = False) -> None:
            """Deploy to target environment."""
            force_flag = " (forced)" if force else ""
            print(f"Deploying version {version} to {environment}{force_flag}")

        def rollback(self, environment: str, steps: int = 1, confirm: bool = False) -> None:
            """Rollback deployment by specified steps."""
            if confirm:
                print(f"Rolling back {steps} steps in {environment}")
            else:
                print(f"Would rollback {steps} steps in {environment} (use --confirm to execute)")


if __name__ == '__main__':
    CLI.display()
```

**Usage with powerful flat commands:**
```bash
# Global + Sub-global + Command arguments (beautifully organized)
python project_manager.py --config-file prod.json --environment production \
  database--migrate --connection-timeout 60 --pool-size 20 \
  --target-version 2.1.0 --dry-run

# Build and deploy with custom settings
python project_manager.py deploy--build --build-timeout 600 --parallel-jobs 8 \
  --target production --clean --skip-tests

# Quick operations
python project_manager.py database--backup --output-path ./backup-$(date +%Y%m%d).sql --compress
python project_manager.py deploy--rollback --environment staging --steps 2 --confirm

# Amazing help shows all organized commands
python project_manager.py --help
python project_manager.py database--help
```

## 📊 Mode Comparison

| Aspect | Module-based | Class-based (Direct) | Class-based (Inner) |
|--------|-------------|---------------------|-------------------|
| **🎯 Best For** | Scripts, utilities | Simple applications | Complex applications |
| **🏗️ Structure** | Functions → Commands | Methods → Commands | Inner classes → Command groups |
| **💾 State** | Parameters only | Instance variables | Global + Sub-global + Instance |
| **📚 Organization** | Flat functions | Class methods | Hierarchical with flat execution |
| **⚙️ Configuration** | Function parameters | Constructor parameters | Multi-level parameters |
| **🚀 Complexity** | Simplest | Medium | Most flexible |
| **🛠️ Maintenance** | Easy | Medium | Best for large projects |

## ✨ Key Features

🚀 **Zero Configuration** - Works instantly with just type annotations  
⚡ **Lightning Fast** - No dependencies, minimal overhead  
🎯 **Type Safe** - Automatic validation from Python type hints  
📚 **Auto Documentation** - Beautiful help from your docstrings  
🎨 **Professional Themes** - Colorful output with NO_COLOR support  
🔧 **Flexible Patterns** - Module, class, and inner class support  
📦 **No Dependencies** - Pure Python standard library  
🌈 **Shell Completion** - Tab completion for Bash, Zsh, Fish, PowerShell  
✅ **Production Ready** - Enterprise-tested in real applications  
🔍 **Developer Friendly** - Clear error messages and debugging support  

## 🎯 Getting Started

### 🆕 New to Freyja?
Choose your path based on your experience level:

#### **🚀 I want to start immediately!**
**[Quick Start Guide →](getting-started/quick-start.md)** - Working CLI in 5 minutes

#### **📚 I want to understand the concepts**
**[Basic Usage Guide →](getting-started/basic-usage.md)** - Core patterns explained

#### **🤔 I need help choosing an approach**
**[CLI Mode Comparison →](getting-started/choosing-cli-mode.md)** - Module vs Class decision guide

#### **⚙️ I need detailed installation info**
**[Installation Guide →](getting-started/installation.md)** - Complete setup instructions

### 💪 Ready to Build Something?
Jump straight into the comprehensive guides:

* **[👤 User Guide →](user-guide/README.md)** - Everything about building CLIs
* **[⚙️ Features →](features/README.md)** - Explore all capabilities  
* **[📋 Examples →](guides/examples.md)** - Real-world use cases

## 📖 Next Steps

### 🎯 Learning Path for New Users
1. **Start Here:** [Quick Start](getting-started/quick-start.md) - Get your first CLI running
2. **Choose Mode:** [Module vs Class](getting-started/choosing-cli-mode.md) - Pick your approach
3. **Deep Dive:** [User Guide](user-guide/README.md) - Master your chosen pattern
4. **Enhance:** [Features](features/README.md) - Add advanced capabilities
5. **Optimize:** [Best Practices](guides/best-practices.md) - Professional techniques

### 🔧 For Developers Building Tools
* **[Real Examples →](guides/examples.md)** - Database tools, API clients, DevOps utilities
* **[Type Annotations →](features/type-annotations.md)** - Supported types and patterns
* **[Shell Completion →](features/shell-completion.md)** - Enable tab completion
* **[Error Handling →](features/error-handling.md)** - Robust error management

### 🚀 For Advanced Users
* **[Advanced Patterns →](advanced/README.md)** - Complex architectures and techniques
* **[API Reference →](reference/README.md)** - Complete technical documentation
* **[Troubleshooting →](guides/troubleshooting.md)** - Solve any issues
* **[Contributing →](development/README.md)** - Help make Freyja even better

### ❓ Need Quick Answers?
* **[FAQ →](faq.md)** - Common questions and solutions
* **[Troubleshooting →](guides/troubleshooting.md)** - Problem-solving guide

---

**Ready to transform your Python code into amazing CLIs?**

```bash
pip install freyja
# Start building professional command-line tools now! ⚡
```

**Navigation**: [← Main README](../README.md) | [Development Guide →](../CLAUDE.md)  
**Examples**: [Browse Examples →](guides/examples.md) | [Quick Start →](getting-started/quick-start.md)