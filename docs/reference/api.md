![Freyja Thumb](https://github.com/terracoil/freyja/raw/main/docs/freyja-thumb.png)
# API Reference

[← Back to Help](../README.md) | [🔧 Basic Usage](../getting-started/basic-usage.md)

# Table of Contents
- [FreyjaCLI Class](#freyja-cli-class)
- [Constructor](#constructor)
- [Instance Methods](#instance-methods)
- [Configuration Options](#configuration-options)
- [Function Options](#function-options)
- [Type Annotations](#type-annotations)
- [Exceptions](#exceptions)
- [Advanced Usage](#advanced-usage)

## FreyjaCLI Class

The main `FreyjaCLI` class provides the interface for creating command-line applications from your Python classes.

```python
from freyja import FreyjaCLI
```

### Constructor

Create a CLI from a Python class with typed methods.

```python
def __init__(
    self,
    target: Target,
    title: Optional[str] = None,
    method_filter: Optional[callable] = None,
    theme=None,
    alphabetize: bool = True,
    completion: bool = True,
    theme_tuner: bool = False,
    capture_output: bool = False,
    capture_stdout: bool = True,
    capture_stderr: bool = False,
    capture_stdin: bool = False,
    output_capture_config: Optional[Dict[str, Any]] = None
) -> FreyjaCLI:
```

**Parameters:**
- **`target`** (`Target`): Class or list of classes to generate CLI from
- **`title`** (`str`, optional): CLI application title. If None, extracted from class docstring
- **`method_filter`** (`callable`, optional): Optional filter for methods (class mode)
- **`theme`** (optional): Theme for colored output
- **`alphabetize`** (`bool`): Whether to sort commands and options alphabetically (default: True)
- **`completion`** (`bool`): Enable shell completion support (default: True)
- **`theme_tuner`** (`bool`): Enable theme tuning system command (default: False)
- **`capture_output`** (`bool`): Enable output capture (opt-in, default: False)
- **`capture_stdout`** (`bool`): Capture stdout when output capture is enabled (default: True)
- **`capture_stderr`** (`bool`): Capture stderr when output capture is enabled (default: False)
- **`capture_stdin`** (`bool`): Capture stdin when output capture is enabled (default: False)
- **`output_capture_config`** (`Dict[str, Any]`, optional): Advanced OutputCapture configuration

**Returns:** `FreyjaCLI` instance

**Example:**

```python
from freyja import FreyjaCLI


class TaskManager:
    """Task Management Application."""

    def __init__(self, database: str = "tasks.db", verbose: bool = False):
        """Initialize task manager.

        All constructor parameters MUST have default values.
        These become global CLI arguments.
        """
        self.database = database
        self.verbose = verbose
        self.tasks = []

    def add_task(self, title: str, priority: str = "medium") -> None:
        """Add a new task."""
        self.tasks.append({"title": title, "priority": priority})
        if self.verbose:
            print(f"Task added to database: {self.database}")


if __name__ == '__main__':
    cli = FreyjaCLI(
        TaskManager,
        title="Task Management System"
    )
    cli.run()
```

## Instance Methods

### `run()`

Start the CLI application and process command-line arguments.

```python
def run(self) -> None:
```

This method:
1. Parses command-line arguments using `sys.argv`
2. Creates an instance of the target class
3. Executes the appropriate method
4. Handles errors and displays help text
5. Exits the program with appropriate exit code

**Example:**
```python
if __name__ == '__main__':
    cli = FreyjaCLI(MyClass, title="My Application")
    cli.run()  # Starts FreyjaCLI and handles all argument processing
```

## Configuration Options

### Function Options

Configure individual methods/commands with custom options:

```python
function_opts = {
    'method_name': {
        'description': 'Custom description for this command',
        'hidden': False,  # Hide from help output
        'name': 'custom-command-name',  # Override kebab-case naming
    }
}

cli = FreyjaCLI(
    MyClass,
    function_opts=function_opts
)
```

### Theme Options

Built-in themes control the visual appearance:

- **`"universal"`**: Default theme with moderate colors
- **`"colorful"`**: Vibrant colors for enhanced readability

Custom themes can be created by subclassing the Theme class.

### Environment Variables

- **`NO_COLOR`**: When set, disables all colored output
- **`COLUMNS`**: Terminal width for help formatting

## Type Annotations

FreyjaCLI uses type annotations to generate CLI arguments:

### Supported Types

| Python Type | CLI Argument | Example |
|------------|--------------|---------|
| `str` | Text input | `--name "John"` |
| `int` | Integer | `--count 5` |
| `float` | Decimal | `--rate 3.14` |
| `bool` | Flag | `--verbose` or `--no-verbose` |
| `Path` | File/directory path | `--input-file /path/to/file` |
| `List[str]` | Multiple values | `--items foo bar baz` |
| `Optional[T]` | Optional argument | `--value` (can be None) |
| `Enum` | Choice from enum values | `--format json` |

### Parameter Rules

1. **Required Parameters**: Parameters without defaults become required arguments
2. **Optional Parameters**: Parameters with defaults become optional arguments
3. **Positional Parameters**: First parameter without default becomes positional
4. **Boolean Flags**: Bool parameters create `--flag` and `--no-flag` options

### Constructor Requirements

**⚠️ CRITICAL**: All constructor parameters MUST have default values:

```python
class MyClass:
    def __init__(self, config: str = "default.json", debug: bool = False):
        # ✅ CORRECT - All parameters have defaults
        pass

class BadClass:
    def __init__(self, required_param: str):
        # ❌ WRONG - Will cause FreyjaCLI creation to fail
        pass
```

## Command Structure

### Direct Methods

Methods of the main class become top-level commands:

```python
class Calculator:
    def add(self, a: float, b: float) -> None:
        print(f"{a} + {b} = {a + b}")

    def multiply(self, a: float, b: float) -> None:
        print(f"{a} × {b} = {a * b}")

# CLI Usage:
# python calc.py add --a 3 --b 4
# python calc.py multiply --a 5 --b 6
```

### Inner Classes (Hierarchical Structure)

Inner classes create hierarchical command structure:

```python
class ProjectManager:
    class Database:
        def migrate(self, version: str = "latest") -> None:
            print(f"Migrating to {version}")

        def backup(self, output: str) -> None:
            print(f"Backing up to {output}")

# CLI Usage:
# python pm.py database migrate --version 2.0
# python pm.py database backup --output backup.sql
```

### Multi-level Arguments

Commands can have three levels of arguments:

1. **Global Arguments**: From main class constructor
2. **Sub-Global Arguments**: From inner class constructor
3. **Command Arguments**: From method parameters

```python
class App:
    def __init__(self, config: str = "app.json"):  # Global
        pass

    class Service:
        def __init__(self, timeout: int = 30):  # Sub-global
            pass

        def start(self, port: int = 8080):  # Command-specific
            pass

# Usage with all three levels:
# python app.py --config prod.json service--start --timeout 60 --port 3000
```

## Exceptions

### ValueError

Raised when:
- Constructor parameters lack default values
- Type annotations are missing
- Invalid configuration options

### TypeError

Raised when:
- Unsupported type annotations are used
- Method signatures are incompatible

### RuntimeError

Raised when:
- Command execution fails
- Resource initialization fails

## Advanced Usage

### Custom Help Formatting

Override help text generation:

```python
class MyClass:
    """Custom application description."""

    def my_method(self) -> None:
        """
        Extended help text with formatting.

        This supports multiple paragraphs and will be
        displayed in the help output.

        Examples:
            python script.py my-method
        """
        pass
```

### Hidden Methods

Prevent methods from appearing in CLI:

```python
class MyClass:
    def public_command(self) -> None:
        """This appears in the CLI."""
        pass

    def _private_method(self) -> None:
        """This is hidden from the CLI (starts with underscore)."""
        pass
```

### Flexible Argument Ordering

Arguments can be provided in any order:

```python
# All of these are equivalent:
python app.py --global-arg value command --cmd-arg value
python app.py command --cmd-arg value --global-arg value
python app.py command --global-arg value --cmd-arg value
```

### Shell Completion

Enable tab completion for your CLI:

```bash
# Generate completion script
python my_app.py completion install --shell bash

# Or for other shells
python my_app.py completion install --shell zsh
python my_app.py completion install --shell fish
```

## Examples

### Complete Application Example

```python
from freyja import FreyjaCLI
from pathlib import Path
from enum import Enum


class OutputFormat(Enum):
    JSON = "json"
    CSV = "csv"
    XML = "xml"


class DataProcessor:
    """Advanced data processing application."""

    def __init__(self, config_file: Path = Path("config.json"),
                 debug: bool = False):
        """Initialize processor with configuration."""
        self.config_file = config_file
        self.debug = debug

    def process_file(self, input_file: Path,
                    output_format: OutputFormat = OutputFormat.JSON,
                    validate: bool = True) -> None:
        """Process a data file.

        Args:
            input_file: Path to input file
            output_format: Desired output format
            validate: Whether to validate data
        """
        if not input_file.exists():
            raise FileNotFoundError(f"File not found: {input_file}")

        print(f"Processing {input_file}")
        print(f"Format: {output_format.value}")
        print(f"Validation: {'enabled' if validate else 'disabled'}")

        if self.debug:
            print(f"Using config: {self.config_file}")

    class BatchOperations:
        """Batch processing commands."""

        def __init__(self, parallel: bool = False,
                    max_workers: int = 4):
            """Configure batch operations."""
            self.parallel = parallel
            self.max_workers = max_workers

        def process_directory(self, directory: Path,
                            pattern: str = "*.txt") -> None:
            """Process all files in a directory."""
            mode = "parallel" if self.parallel else "sequential"
            print(f"Processing {directory} ({pattern}) in {mode} mode")
            if self.parallel:
                print(f"Using {self.max_workers} workers")


if __name__ == '__main__':
    cli = FreyjaCLI(
        DataProcessor,
        title="Data Processing Suite",
        theme_name="colorful",
        completion=True
    )
    cli.run()
```

**Usage Examples:**

```bash
# Basic command
python processor.py process-file input.json

# With options
python processor.py process-file input.json --output-format csv --no-validate

# Global options
python processor.py --debug --config-file prod.json process-file data.json

# Batch operations with sub-global options
python processor.py batch-operations--process-directory ./data \
    --parallel --max-workers 8 --pattern "*.csv"

# Get help
python processor.py --help
python processor.py process-file --help
python processor.py batch-operations--help
```

---

**Ready to build your CLI?** Start with the [Quick Start Guide →](../getting-started/quick-start.md)