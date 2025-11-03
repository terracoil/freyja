![Freyja](https://github.com/terracoil/freyja/raw/main/docs/freyja.png)

# CLAUDE.md

## Table of Contents
* [Project Overview](#project-overview)
* [Development Environment Setup](#development-environment-setup)
* [Common Commands](#common-commands)
* [Creating Freyja CLIs in Other Projects](#creating-freyja-clis-in-other-projects)
  * [Quick Setup Checklist](#quick-setup-checklist)
  * [Class-based CLI Pattern](#class-based-cli-pattern-methods)
* [Architecture](#architecture)
* [File Structure](#file-structure)
* [Testing Notes](#testing-notes)

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**📚 [→ User Documentation Hub](docs/README.md)** - Complete documentation for users

## Project Overview

This is an active Python library (`freyja`) that automatically builds complete CLI applications from Python class methods using introspection and type annotations. The library creates CLI from class methods with organizational patterns:

- **Direct Methods**: Simple commands from class methods
- **Inner Classes**: Hierarchical command groups (e.g., `database migrate`, `projects create`) supporting global and sub-global arguments

**IMPORTANT**: Inner class methods create hierarchical command structures using space-separated syntax (e.g., `database migrate`, `projects create`) supporting global and sub-global arguments.

The library generates argument parsers and command-line interfaces with minimal configuration by analyzing class method signatures. Published on PyPI at https://pypi.org/project/freyja/

## Development Environment Setup

### Poetry Environment (Recommended)
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Setup development environment
./bin/dev-tools setup env

# Or manually:
poetry install --with dev
poetry run pre-commit install
```

### Alternative Installation
```bash
# Install from PyPI
pip install freyja

# Install from GitHub (specific branch)
pip install git+https://github.com/terracoil/freyja.git@main
```

## Common Commands

### Testing
```bash
# Run all tests with coverage
./bin/dev-tools test run
# Or: poetry run pytest

# Run specific test file
poetry run pytest tests/test_cli.py

# Run with verbose output
poetry run pytest -v --tb=short
```

### Code Quality
```bash
# Run all linters and formatters
./bin/dev-tools build lint

# Individual tools:
poetry run ruff check .              # Fast linting
poetry run black --check .          # Format checking
poetry run mypy src             # Type checking
poetry run pylint src           # Additional linting

# Auto-format code
poetry run black .
poetry run ruff check . --fix
```

### Build and Deploy
```bash
# Build package
poetry build

# Publish to PyPI (maintainers only)
./bin/dev-tools build publish
# Or: poetry publish

# Install development version
poetry install
```

### Examples
```bash
# Run class-based Freyja example  
poetry run python freyja/examples/cls_example --help

# Try example commands (all commands are flat)
poetry run python freyja/examples/cls_example file-operations--process-single --input-file "test.txt"
poetry run python freyja/examples/cls_example data-operations--process-batch --files "*.csv" --parallel
```

## Creating Freyja CLIs in Other Projects

When Claude Code is working in a project that needs a CLI, use Freyja for rapid CLI development:

### Quick Setup Checklist

**Prerequisites:**
```bash
pip install freyja  # Ensure Freyja is available
```

**Method Requirements:**
- ✅ All parameters must have type annotations (`str`, `int`, `bool`, etc.)
- ✅ Add docstrings for help text generation
- ✅ Use sensible default values for optional parameters
- ✅ Methods should not start with underscore (private methods ignored)
- ✅ Constructor parameters must have default values (become global/sub-global arguments)


### Class-based CLI Pattern

Freyja transforms Python classes into powerful command-line interfaces. Perfect for stateful applications, configuration management, and complex workflows.

#### **Direct Methods Pattern (Simple)**

Use direct methods for simple, flat command structures:

```python
from freyja import FreyjaCLI


class SimpleCalculator:
  """Simple calculator command tree."""

  def __init__(self):
    """Initialize calculator."""
    pass

  def add(self, a: float, b: float) -> None:
    """Add two numbers."""
    result = a + b
    print(f"{a} + {b} = {result}")

  def multiply(self, a: float, b: float) -> None:
    """Multiply two numbers."""
    result = a * b
    print(f"{a} * {b} = {result}")


if __name__ == '__main__':
  cli = FreyjaCLI(SimpleCalculator, title="Simple Calculator")
  cli.run()
```

**Usage:**
```bash
python calculator.py add --a 5 --b 3
python calculator.py multiply --a 4 --b 7
```

#### **🆕 Inner Class Pattern (Hierarchical Structure)**

Use inner classes for organized hierarchical command structure:

```python
from freyja import FreyjaCLI
from pathlib import Path


class ProjectManager:
  """
  Project Management CLI with hierarchical command structure.

  Manage projects with organized hierarchical commands and global/sub-global arguments.
  """

  def __init__(self, config_file: str = "config.json", debug: bool = False):
    """
    Initialize project manager with global settings.
    
    :param config_file: Configuration file path (global argument)
    :param debug: Enable debug mode (global argument)
    """
    self.config_file = config_file
    self.debug = debug
    self.projects = {}

  class ProjectOperations:
    """Project creation and management operations."""

    def __init__(self, workspace: str = "./projects", auto_save: bool = True):
      """
      Initialize project operations.
      
      :param workspace: Workspace directory (sub-global argument)
      :param auto_save: Auto-save changes (sub-global argument)
      """
      self.workspace = workspace
      self.auto_save = auto_save

    def create(self, name: str, description: str = "") -> None:
      """Create a new project."""
      print(f"Creating project '{name}' in workspace: {self.workspace}")
      print(f"Description: {description}")
      print(f"Auto-save enabled: {self.auto_save}")

    def delete(self, project_id: str, force: bool = False) -> None:
      """Delete an existing project."""
      action = "Force deleting" if force else "Deleting"
      print(f"{action} project {project_id} from {self.workspace}")

  class TaskManagement:
    """Task operations within projects."""

    def __init__(self, priority_filter: str = "all"):
      """
      Initialize task management.
      
      :param priority_filter: Default priority filter (sub-global argument)
      """
      self.priority_filter = priority_filter

    def add(self, title: str, priority: str = "medium") -> None:
      """Add task to project."""
      print(f"Adding task: {title} (priority: {priority})")
      print(f"Using filter: {self.priority_filter}")

    def list_tasks(self, show_completed: bool = False) -> None:
      """List project tasks."""
      print(f"Listing tasks (filter: {self.priority_filter})")
      print(f"Include completed: {show_completed}")

  class ReportGeneration:
    """Report generation without sub-global arguments."""

    def summary(self, detailed: bool = False) -> None:
      """Generate project summary report."""
      detail_level = "detailed" if detailed else "basic"
      print(f"Generating {detail_level} summary report")

    def export(self, format: str = "json", output_file: Path = None) -> None:
      """Export project data."""
      print(f"Exporting to {format} format")
      if output_file:
        print(f"Output file: {output_file}")


if __name__ == '__main__':
  cli = FreyjaCLI(ProjectManager, theme_name="colorful")
  cli.run()
```

**Usage with Hierarchical Commands:**
```bash
# Global + Sub-global + Command arguments (hierarchical structure)
python project_mgr.py --config-file prod.json --debug \
  project-operations create --workspace /prod/projects --auto-save \
  --name "web-app" --description "Production web app"

# Commands without sub-global arguments
python project_mgr.py report-generation summary --detailed

# All commands use hierarchical space-separated syntax
python project_mgr.py project-operations create --name "my-project"
python project_mgr.py task-management add --title "New task" --priority "high"
python project_mgr.py report-generation export --format "json"

# Help shows all commands hierarchically organized
python project_mgr.py --help  # Shows all available commands
```

### Common Patterns by Use Case

#### 1. Configuration Management (Inner Class Pattern)
```python
class ConfigManager:
    """Application configuration CLI with hierarchical command organization."""
    
    def __init__(self, config_file: str = "app.config"):
        """Initialize with global configuration file."""
        self.config_file = config_file
    
    class SystemConfig:
        """System-level configuration."""
        
        def __init__(self, backup_on_change: bool = True):
            """Initialize system config operations."""
            self.backup_on_change = backup_on_change
        
        def set_value(self, key: str, value: str, config_type: str = "string") -> None:
            """Set system configuration value."""
            pass
        
        def get_value(self, key: str) -> None:
            """Get system configuration value."""
            pass
    
    class UserConfig:
        """User-level configuration."""
        
        def set_preference(self, key: str, value: str) -> None:
            """Set user preference."""
            pass
```

#### 2. File Processing Pipeline (Class Pattern)
```python
class FileProcessor:
    """File processing utilities with batch operations."""
    
    def __init__(self, working_dir: str = ".", parallel: bool = False):
        """Initialize file processor."""
        self.working_dir = working_dir
        self.parallel = parallel
    
    def convert_files(self, input_dir: str, output_dir: str, format_type: str = "json") -> None:
        """Convert files between formats."""
        pass

    def validate_files(self, directory: str, extensions: List[str]) -> None:
        """Validate files in directory."""
        pass

    def batch_process(self, pattern: str, max_files: int = 100) -> None:
        """Process multiple files matching pattern."""
        pass

    def batch_validate(self, directory: str, parallel: bool = False) -> None:
        """Validate files in batch."""
        pass
```

#### 3. API Client Tool (Inner Class Pattern)
```python
class APIClient:
    """REST API client Freyja with organized endpoints."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize API client with global settings."""
        self.base_url = base_url
        self.timeout = timeout
    
    class UserEndpoints:
        """User-related API operations."""
        
        def __init__(self, auth_token: str = None):
            """Initialize user endpoints with authentication."""
            self.auth_token = auth_token
        
        def get_user(self, user_id: str) -> None:
            """Get user by ID."""
            pass
        
        def create_user(self, username: str, email: str) -> None:
            """Create new user."""
            pass
    
    class DataEndpoints:
        """Data-related API operations."""
        
        def get_data(self, endpoint: str, params: List[str] = None) -> None:
            """GET request to data endpoint."""
            pass
```

#### 4. Database Operations (Inner Class Pattern)
```python
class DatabaseCLI:
    """Database management Freyja with organized operations."""
    
    def __init__(self, connection_string: str, debug: bool = False):
        """Initialize with global database settings."""
        self.connection_string = connection_string
        self.debug = debug
    
    class QueryOperations:
        """SQL query operations."""
        
        def __init__(self, timeout: int = 30):
            """Initialize query operations."""
            self.timeout = timeout
        
        def execute(self, sql: str, limit: int = 100) -> None:
            """Execute SQL query."""
            pass
        
        def explain(self, sql: str) -> None:
            """Explain query execution plan."""
            pass
    
    class SchemaOperations:
        """Database schema operations."""
        
        def create_table(self, table_name: str, schema: str) -> None:
            """Create database table."""
            pass
        
        def drop_table(self, table_name: str, force: bool = False) -> None:
            """Drop database table."""
            pass
```

### Type Annotation Patterns

```python
# Basic types in class methods
class DataProcessor:
    def process(self, name: str, count: int, rate: float, debug: bool = False) -> None:
        pass

    # Collections  
    from typing import List, Optional
    def batch_process(self, files: List[str], options: Optional[List[str]] = None) -> None:
        pass

# Enums for choices
from enum import Enum

class OutputFormat(Enum):
    JSON = "json"
    CSV = "csv"
    XML = "xml"

class DataExporter:
    def export_data(self, data: str, format: OutputFormat = OutputFormat.JSON) -> None:
        pass
```

### Configuration and Customization

```python
# Class-based with custom options
cli = FreyjaCLI(
    MyClass,
    title="Custom CLI Title",
    function_opts={
        'method_name': {
            'description': 'Custom method description',
            'hidden': False
        }
    },
    theme_name="colorful",  # or "universal"
    no_color=False,         # Force disable colors if needed
    completion=True         # Enable shell completion
)
```

### Testing CLI Methods

```python
# Test methods directly (preferred)
def test_process_data():
    processor = DataProcessor()
    processor.process_data("test.csv", "json", True)  # Direct method call
    assert True  # Add proper assertions

# Integration testing (when needed)
import subprocess

def test_cli_integration():
    result = subprocess.run([
        'python', 'script.py', 'process-data', 
        '--input-file', 'test.csv', '--verbose'
    ], capture_output=True, text=True)
    assert result.returncode == 0
```

### Common Pitfalls to Avoid

```python
# ❌ Missing type annotations
class BadClass:
    def bad_method(self, name, count=5):  # Will cause errors
        pass

# ❌ Private method (starts with _) 
class MyClass:
    def _private_method(self, data: str) -> None:  # Ignored by Freyja
        pass

# ❌ Complex types not supported
class ComplexClass:
    def complex_method(self, callback: Callable[[str], int]) -> None:  # Too complex
        pass

# ❌ Mutable defaults
class RiskyClass:
    def risky_method(self, items: List[str] = []) -> None:  # Dangerous
        pass

# ✅ Correct patterns
class GoodClass:
    def good_method(self, name: str, count: int = 5) -> None:
        pass

    def public_method(self, data: str) -> None:
        pass

    def simple_method(self, callback_name: str) -> None:  # Use string lookup
        pass

    def safe_method(self, items: List[str] = None) -> None:
        if items is None:
            items = []
```

### Constructor Parameter Requirements

**CRITICAL**: For class-based CLIs, all constructor parameters (both parent class and inner class constructors) **MUST** have default values.

#### ✅ Correct Class Constructors

```python
class MyClass:
    def __init__(self, config_file: str = "config.json", debug: bool = False):
        """All parameters have defaults - ✅ GOOD"""
        self.config_file = config_file
        self.debug = debug
    
    class InnerClass:
        def __init__(self, database_url: str = "sqlite:///app.db"):
            """All parameters have defaults - ✅ GOOD"""
            self.database_url = database_url
        
        def some_method(self):
            pass
```

#### ❌ Invalid Class Constructors

```python
class BadClass:
    def __init__(self, required_param: str):  # ❌ NO DEFAULT VALUE
        """This will cause Freyja creation to fail"""
        self.required_param = required_param
    
    class BadInnerClass:
        def __init__(self, required_config: str):  # ❌ NO DEFAULT VALUE
            """This will also cause Freyja creation to fail"""
            self.required_config = required_config
        
        def some_method(self):
            pass
```

#### Why This Requirement Exists

- **Global Arguments**: Parent class constructor parameters become global CLI arguments
- **Sub-Global Arguments**: Inner class constructor parameters become sub-global CLI arguments
- **CLI Usability**: Users should be able to run commands without specifying every parameter
- **Error Prevention**: Ensures CLI can instantiate classes during command execution

#### Error Messages

If constructor parameters lack defaults, you'll see errors like:
```
ValueError: Constructor for parent class 'MyClass' has parameters without default values: required_param. 
All constructor parameters must have default values to be used as CLI arguments.
```

### Quick Reference Links

- **[Complete Documentation](docs/README.md)** - Full user guide
- **[Type Annotations](docs/features/type-annotations.md)** - Supported types reference
- **[Troubleshooting](docs/guides/troubleshooting.md)** - Common issues and solutions
- **[Examples](freyja/examples/cls_example)** - Class-based CLI examples

## Class Namespacing Rules (CRITICAL)

**IMPORTANT**: The following rules apply to non-primary classes when multiple classes are provided to Freyja. These rules prevent regression from flat dash-prefixed commands to proper hierarchical structures.

### Namespacing Behavior for Non-Primary Classes

When providing multiple classes to Freyja, only the **last class** (primary) gets global namespace. All other classes become **namespaced** with TRUE hierarchical structure:

#### ✅ CORRECT Hierarchical Structure

Non-primary classes create proper hierarchical command groups:

```python
class System:
    """System command tree and utilities."""
    
    class Completion:
        """Shell completion management."""
        
        def install(self, shell: str = "bash") -> None:
            """Install shell completion."""
            pass
        
        def uninstall(self, shell: str = "bash") -> None:
            """Remove shell completion."""
            pass
```

**Results in CORRECT hierarchy:**
```
system                    System commands and utilities
  completion              Shell completion management  
    install               Install shell completion
    uninstall             Remove shell completion
```

**Usage:**
```bash
my_cli system completion install --shell bash
my_cli system completion uninstall --shell zsh
```

#### ❌ INCORRECT Flat Dash-Prefixed Commands (DO NOT ALLOW)

**NEVER** create flat commands with dash prefixes like:
- `system-completion → install` (OLD INCORRECT BEHAVIOR)
- `system-completion → uninstall` (OLD INCORRECT BEHAVIOR)

**NEVER** use dunder syntax like:
- `system__completion → install` (PREVIOUS INCORRECT ATTEMPT)
- `system__completion → uninstall` (PREVIOUS INCORRECT ATTEMPT)

### Implementation Rules

1. **CommandDiscovery**: Non-primary classes must create top-level groups using `kebab_case(class_name)`
2. **Inner Classes**: Inner classes within non-primary classes become **subgroups**, not flat commands
3. **Command Tree**: Use `add_subgroup_to_group()` and `add_command_to_subgroup()` for nested structures
4. **Command Parser**: Must handle nested groups (groups containing other groups)
5. **System Commands**: Non-primary system classes should appear first in help output before alphabetized commands

### Code Pattern

```python
# In CommandDiscovery._discover_from_class()
if is_namespaced:
    # Create top-level group for the namespaced class
    class_namespace = TextUtil.kebab_case(target_cls.__name__)
    command_tree.add_group(class_namespace, class_description, is_system_command=self.is_system(target_cls))
    
    # Inner classes become subgroups, NOT flat dash-prefixed command tree
    for inner_class_name, inner_class in inner_classes.items():
        subgroup_name = TextUtil.kebab_case(inner_class_name)
        command_tree.add_subgroup_to_group(class_namespace, subgroup_name, description, inner_class=inner_class)
```

### Test Verification

Always verify that:
- `system completion install` works (hierarchical)
- `system-completion install` does NOT exist (flat dash-prefixed forbidden)
- Help output shows proper nesting with indentation
- System commands appear first before alphabetized commands

## Architecture

### Core Components

- **`freyja/freyja_cli.py`**: Main `FreyjaCLI` class - entry point for CLI generation
- **`freyja/cli/`**: CLI coordination and execution components
  - `execution_coordinator.py`: Orchestrates command execution flow
  - `class_handler.py`: Manages class-based CLI creation
  - `enums.py`: Core enums and constants
  - `system/`: Built-in system commands (completion, theme tuning)
- **`freyja/command/`**: Command discovery and management
  - `command_discovery.py`: Discovers methods and builds command tree
  - `command_tree.py`: Hierarchical command structure representation
  - `command_executor.py`: Executes discovered commands
  - `command_info.py`: Command metadata and information
- **`freyja/parser/`**: Argument parsing and preprocessing
  - `argument_parser.py`: Main argparse integration
  - `command_parser.py`: Command-specific argument parsing
  - `positional_handler.py`: Handles positional argument logic
  - `option_discovery.py`: Discovers method options and converts to CLI args
  - `argument_preprocessor.py`: Pre-processes arguments for flexible ordering
  - `command_path_resolver.py`: Resolves command paths (flat vs hierarchical)
- **`freyja/completion/`**: Shell completion system
- **`freyja/utils/`**: Utility modules (text processing, data structures, etc.)

### Key Architecture Patterns

**Class-Only Introspection**: Freyja exclusively uses class-based CLI generation via `inspect.signature()` to analyze class methods, their parameters, types, and default values.

**Layered Command Discovery**:
1. **CommandDiscovery** scans classes and builds command tree
2. **ArgumentParser** creates argparse structure from command tree
3. **ExecutionCoordinator** handles command dispatch and execution

**Flexible Argument Processing**:
- **ArgumentPreprocessor**: Enables flexible argument ordering (global, sub-global, command-specific)
- **PositionalHandler**: Manages positional arguments (first non-default parameter)
- **OptionDiscovery**: Converts method parameters to CLI arguments with kebab-case

**Hierarchical Command Structure**:
- **Single Class**: Hierarchical commands (`inner-class method`)
- **Multi-Class**: Hierarchical structure for all classes

**Type-Driven Generation**: 
- Method annotations become argument types and validation
- Enum types become choice arguments  
- Default values become optional arguments
- Constructor parameters become global/sub-global arguments

### Current Usage Pattern
```python
from freyja import FreyjaCLI

class MyClass:
    def __init__(self, config: str = "default.json", debug: bool = False):
        """Constructor params become global arguments."""
        self.config = config
        self.debug = debug
    
    def process_file(self, input_file: str, output_dir: str = "./output") -> None:
        """First param without default becomes positional argument."""
        pass

# Setup Freyja
cli = FreyjaCLI(MyClass, title="My CLI")
cli.run()

# Usage: my_cli process-file <input_file> [--output-dir OUTPUT_DIR] [--config CONFIG] [--debug]
```

## Core Architectural Rules (CRITICAL)

**CRITICAL**: These architectural rules must be preserved to prevent regressions. All code changes MUST comply with these rules.

### 1. Positional Argument Rule

**RULE**: The first method parameter WITHOUT a default value becomes a positional argument and MUST be reflected as such in usage strings.

```python
class Example:
    def process(self, input_file: str, output_dir: str = "./output", verbose: bool = False) -> None:
        """Process input file."""
        pass
```

**Usage MUST show:**
```
usage: my_cli process <input_file> [--output-dir OUTPUT_DIR] [--verbose]
```

**NOT:**
```
usage: my_cli process --input-file INPUT_FILE [--output-dir OUTPUT_DIR] [--verbose]
```

### 2. Flexible Argument Ordering Rule

**RULE**: Command options MUST work in ANY order, regardless of whether they are:
- Global arguments (from parent class constructor)
- Sub-global arguments (from inner class constructors) 
- Command-specific arguments (from method parameters)

```bash
# All of these MUST work identically:
my_cli --global-arg value command --sub-global arg --method-arg value
my_cli command --method-arg value --global-arg value --sub-global arg  
my_cli --sub-global arg --global-arg value command --method-arg value
```

### 3. Class-Based CLI Only Rule

**RULE**: Freyja ONLY supports class-based CLIs. There is NO support for:
- Module-based CLIs
- Function-based CLIs
- Any non-class CLI generation

**Implications**:
- All CLI generation code assumes class input
- No module introspection code exists
- No tests for module-based CLIs exist
- Documentation only covers class-based patterns

### 4. Command Structure Rule

**RULE**: The last class in a multi-class CLI should not be namespaced (i.e., they are in the global namespace).
- Direct class methods → with no inner classes (`my_cli method_name`)
- Inner class methods → (`my_cli inner-class method-name`)

**Other classes not in the global namespace:**
- Multi-class: `my_cli system completion install` (hierarchical structure)

### 5. Type Annotation Requirement Rule

**RULE**: ALL method parameters MUST have type annotations for CLI generation to work:

```python
# ✅ CORRECT - All parameters typed
def process(self, name: str, count: int = 5, debug: bool = False) -> None:
    pass

# ❌ INCORRECT - Will cause CLI generation to fail  
def process(self, name, count=5, debug=False):
    pass
```

### 6. Constructor Default Values Rule

**RULE**: ALL constructor parameters (parent class and inner class) MUST have default values:
- Parent class constructor parameters → Global CLI arguments
- Inner class constructor parameters → Sub-global CLI arguments
- No defaults = CLI generation failure

### 7. Private Method Exclusion Rule

**RULE**: Methods starting with underscore (`_`) are automatically ignored during CLI generation:

```python
class MyClass:
    def public_method(self) -> None:  # ✅ Becomes CLI command
        pass
    
    def _private_method(self) -> None:  # ❌ Ignored by CLI generation
        pass
```

### 8. Parameter-to-Argument Mapping Rule

**RULE**: Method parameter names are converted to CLI argument names using kebab-case:
- `input_file` → `--input-file`
- `max_count` → `--max-count`  
- `enableDebug` → `--enable-debug`

### 9. Multi-Class Namespacing Rule

**RULE**: When multiple classes are provided to Freyja:
- **Last class (primary)**: Gets global namespace (flat commands)
- **Non-primary classes**: Get namespaced with TRUE hierarchical structure
- **NEVER** flat dash-prefixed commands for multi-class scenarios

### 10. Command Resolution Priority Rule

**RULE**: Command resolution follows strict precedence:
1. Direct methods of primary class
2. Inner class methods of primary class (hierarchical)
3. Hierarchical commands from non-primary classes
4. System commands (appear first in help)

### 11. Argument Parser Generation Rule

**RULE**: Argument parsers are generated automatically using:
- `inspect.signature()` for method introspection
- `argparse` for CLI parsing
- Type annotations for argument type validation
- Default values for optional arguments

### 12. Hierarchical Commands Only Rule

**RULE**: Freyja MUST ONLY use hierarchical command structures with space separators. Flat double-dash commands (`--`) and dunder (`__`) syntax are FORBIDDEN:

```bash
# ❌ NEVER USE - Flat double-dash commands FORBIDDEN
my_cli database--migrate            # FORBIDDEN
my_cli data-ops--process            # FORBIDDEN
my_cli system__completion__install  # FORBIDDEN

# ✅ CORRECT - ONLY hierarchical commands with spaces
my_cli database migrate             # Correct
my_cli system completion install    # Correct
my_cli projects create              # Correct
```

**Rationale**:
- Clean, intuitive command structure
- Consistent with industry-standard CLIs (git, docker, kubectl)
- Better discoverability and help navigation
- Eliminates confusion about command syntax

**Implications**:
- No `--` (double-dash) in command names or paths
- No `__` (dunder) in command names, paths, or internal representations
- All commands use space-separated hierarchical structure
- Inner classes become command groups, their methods become subcommands
- Help output shows proper hierarchical nesting with indentation

### 13. Error Prevention Rules

**RULE**: The following patterns MUST cause immediate failures:
- Missing type annotations on method parameters
- Constructor parameters without default values
- Complex types not supported by argparse
- Mutable default values in method signatures
- Any use of dunder (`__`) syntax for command structuring

### Implementation Verification

When implementing or modifying Freyja code, ALWAYS verify:

1. **Positional Arguments**: First non-default parameter shows as `<param>` in usage
2. **Argument Order**: All argument combinations work in any order
3. **Class-Only**: No module/function CLI generation code paths exist
4. **Hierarchical Structure**: All commands use space-separated hierarchical syntax
5. **Type Safety**: All method parameters have type annotations
6. **Constructor Defaults**: All constructor parameters have defaults
7. **Private Exclusion**: Underscore methods are ignored
8. **Kebab-Case**: Parameter names convert to kebab-case arguments
9. **Namespacing**: Multi-class scenarios use hierarchy for non-primary classes
10. **Resolution**: Command resolution follows defined precedence
11. **Auto-Generation**: Parsers generated from method introspection
12. **No Double-Dash/Dunders**: No `--` or `__` in command structures
13. **Error Handling**: Invalid patterns cause immediate failures

**BREAKING ANY OF THESE RULES CONSTITUTES A REGRESSION AND MUST BE PREVENTED.**

## File Structure

- `freya/cli.py` - Core CLI generation logic
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
