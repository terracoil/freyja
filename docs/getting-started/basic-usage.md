# Basic Usage Guide

[← Back to Help](../help.md) | [← Installation](installation.md)

## Table of Contents
- [Creating Your First CLI](#creating-your-first-cli)
- [Function Requirements](#function-requirements)
- [Type Annotations](#type-annotations)
- [CLI Configuration](#cli-configuration)
- [Running Your CLI](#running-your-cli)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)

## Creating Your First CLI

The basic pattern for creating a CLI with auto-cli-py:

```python
from auto_cli import CLI
import sys


def your_function(param1: str, param2: int = 42):
  """Your function docstring becomes help text."""
  print(f"Received: {param1}, {param2}")


# Create CLI from current module
cli = CLI(sys.modules[__name__], title="My CLI")
cli.display()
```

### Key Components

1. **Import CLI**: The main class for creating command-line interfaces
2. **Define Functions**: Regular Python functions with type annotations
3. **Create CLI Instance**: Pass the module containing your functions
4. **Call display()**: Start the CLI and process command-line arguments

## Function Requirements

### Minimal Function
```python
def simple_command():
    """This is the simplest possible CLI command."""
    print("Hello from auto-cli-py!")
```

### Function with Parameters
```python
def process_data(
    input_file: str,                    # Required parameter
    output_dir: str = "./output",       # Optional with default
    verbose: bool = False               # Boolean flag
):
    """Process data from input file to output directory.
    
    Args:
        input_file: Path to the input data file
        output_dir: Directory for output files
        verbose: Enable detailed logging
    """
    # Your logic here
    pass
```

### Docstring Guidelines

Auto-cli-py uses function docstrings for help text:

```python
def example_command(param: str):
    """Brief description of what this command does.
    
    Detailed explanation can go here. This will appear
    in the help output when users run --help.
    
    Args:
        param: Description of this parameter
    """
    pass
```

## Type Annotations

Type annotations define how command-line arguments are parsed:

### Basic Types
```python
def basic_types_example(
    text: str,              # String argument
    number: int,            # Integer argument  
    decimal: float,         # Float argument
    flag: bool = False      # Boolean flag (--flag/--no-flag)
):
    """Example of basic type annotations."""
    pass
```

### Optional Parameters
```python
from typing import Optional

def optional_example(
    required: str,                     # Required argument
    optional: Optional[str] = None,    # Optional string
    default_value: str = "default"     # Optional with default
):
    """Optional parameters become optional CLI arguments."""
    pass
```

### Enum Types
```python
from enum import Enum

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

def logging_example(level: LogLevel = LogLevel.INFO):
    """Enums become choice arguments."""
    print(f"Log level: {level.value}")
```

**Usage:**
```bash
python script.py logging-example --level debug
```

### File Paths
```python
from pathlib import Path

def file_example(
    input_path: Path,               # File path argument
    output_path: Path = Path(".")   # Path with default
):
    """File paths are automatically validated."""
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
```

## CLI Configuration

### Basic Configuration
```python
cli = CLI(
    sys.modules[__name__],
    title="My Application",
    description="A comprehensive CLI tool"
)
```

### Function-Specific Options
```python
# Configure specific functions
function_opts = {
    'process_data': {
        'description': 'Custom description for this command',
        'hidden': False  # Show/hide this command
    }
}

cli = CLI(
    sys.modules[__name__],
    function_opts=function_opts
)
```

### Custom Themes
```python
from auto_cli.theme import create_default_theme_colorful

cli = CLI(
    sys.modules[__name__],
    theme=create_default_theme_colorful()
)
```

## Running Your CLI

### Command Structure
```bash
python script.py [global-options] <command> [command-options]
```

### Global Options
Every CLI automatically includes:
- `--help, -h`: Show help message
- `--verbose, -v`: Enable verbose output  
- `--no-color`: Disable colored output

### Examples
```bash
# Show all available commands
python my_cli.py --help

# Get help for specific command
python my_cli.py process-data --help

# Run command with arguments
python my_cli.py process-data input.txt --output-dir ./results --verbose

# Boolean flags
python my_cli.py process-data input.txt --verbose          # Enable flag
python my_cli.py process-data input.txt --no-verbose       # Disable flag
```

## Common Patterns

### Data Processing CLI
```python
from pathlib import Path
from typing import Optional
from enum import Enum

class Format(Enum):
    JSON = "json"
    CSV = "csv"
    XML = "xml"

def convert_data(
    input_file: Path,
    output_format: Format,
    output_file: Optional[Path] = None,
    compress: bool = False
):
    """Convert data between different formats."""
    # Implementation here
    pass

def validate_data(input_file: Path, schema: Optional[Path] = None):
    """Validate data against optional schema."""
    # Implementation here
    pass

cli = CLI(sys.modules[__name__], title="Data Processing Tool")
cli.display()
```

### Configuration Management CLI
```python
def set_config(key: str, value: str, global_setting: bool = False):
    """Set a configuration value."""
    scope = "global" if global_setting else "local"
    print(f"Set {key}={value} ({scope})")

def get_config(key: str):
    """Get a configuration value."""
    # Implementation here
    pass

def list_config():
    """List all configuration values."""
    # Implementation here
    pass

cli = CLI(sys.modules[__name__], title="Config Manager")
cli.display()
```

### Batch Processing CLI
```python
def batch_process(
    pattern: str,
    recursive: bool = False,
    dry_run: bool = False,
    workers: int = 4
):
    """Process multiple files matching a pattern."""
    mode = "dry run" if dry_run else "processing"
    search = "recursive" if recursive else "current directory"
    print(f"{mode} files matching '{pattern}' ({search}) with {workers} workers")

cli = CLI(sys.modules[__name__], title="Batch Processor")
cli.display()
```

## Error Handling

### Parameter Validation
```python
def validate_example(port: int, timeout: float):
    """Example with parameter validation."""
    if port < 1 or port > 65535:
        raise ValueError("Port must be between 1 and 65535")
    
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
    
    print(f"Connecting to port {port} with {timeout}s timeout")
```

### Graceful Error Handling
```python
import sys

def safe_operation(risky_param: str):
    """Example of safe error handling."""
    try:
        # Your risky operation here
        result = some_risky_function(risky_param)
        print(f"Success: {result}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: File not found", file=sys.stderr)  
        sys.exit(2)
```

## Next Steps

Now that you understand the basics:

### Explore Advanced Features
- **[Subcommands](../features/subcommands.md)** - Organize complex CLIs
- **[Themes](../features/themes.md)** - Customize appearance
- **[Type Annotations](../features/type-annotations.md)** - Advanced type handling

### See Real Examples
- **[Examples Guide](../guides/examples.md)** - Comprehensive real-world examples
- **[Best Practices](../guides/best-practices.md)** - Recommended patterns

### Deep Dive
- **[CLI Generation](../features/cli-generation.md)** - How auto-cli-py works
- **[API Reference](../reference/api.md)** - Complete technical documentation

## See Also
- [Quick Start Guide](quick-start.md) - 5-minute introduction
- [Installation](installation.md) - Setup instructions
- [Examples](../guides/examples.md) - Real-world applications
- [Type Annotations](../features/type-annotations.md) - Advanced type usage

---
**Navigation**: [← Installation](installation.md) | [Examples →](../guides/examples.md)  
**Parent**: [Help](../help.md)  
**Children**: [Examples](../guides/examples.md)
