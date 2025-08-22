# Module-based CLI Guide

[← Back to Help](../help.md) | [↑ Getting Started](../help.md#getting-started)

## Table of Contents
- [Overview](#overview)
- [Basic Usage](#basic-usage)
- [Function Requirements](#function-requirements)
- [Type Annotations](#type-annotations)
- [Module Organization](#module-organization)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [See Also](#see-also)

## Overview

Module-based CLI is the original and simplest way to create CLIs with auto-cli-py. It automatically generates a command-line interface from the functions defined in a Python module.

### When to Use Module-based CLI

- **Simple scripts** with standalone functions
- **Utility tools** that don't need shared state
- **Data processing** pipelines
- **Quick prototypes** and experiments
- **Functional programming** approaches

## Basic Usage

### Simple Example

```python
# my_cli.py
from auto_cli import CLI

def greet(name: str, excited: bool = False):
    """Greet someone by name."""
    greeting = f"Hello, {name}!"
    if excited:
        greeting += "!!!"
    print(greeting)

def calculate(x: int, y: int, operation: str = "add"):
    """Perform a calculation on two numbers."""
    if operation == "add":
        result = x + y
    elif operation == "subtract":
        result = x - y
    elif operation == "multiply":
        result = x * y
    elif operation == "divide":
        result = x / y if y != 0 else "Error: Division by zero"
    else:
        result = "Unknown operation"
    
    print(f"{x} {operation} {y} = {result}")

if __name__ == "__main__":
    import sys
    cli = CLI.from_module(sys.modules[__name__])
    cli.run()
```

### Running the CLI

```bash
# Show help
python my_cli.py --help

# Use greet command
python my_cli.py greet --name Alice
python my_cli.py greet --name Bob --excited

# Use calculate command
python my_cli.py calculate --x 10 --y 5
python my_cli.py calculate --x 10 --y 3 --operation divide
```

## Function Requirements

### Valid Functions

Functions that can be converted to CLI commands must:

1. **Be defined at module level** (not nested)
2. **Have a name** that doesn't start with underscore
3. **Accept parameters** (or no parameters)
4. **Have type annotations** (recommended)

### Example of Valid Functions

```python
# ✓ Valid - module level, public name
def process_data(input_file: str, output_file: str):
    pass

# ✓ Valid - no parameters is fine
def show_status():
    pass

# ✓ Valid - default values supported
def configure(verbose: bool = False, level: int = 1):
    pass
```

### Example of Invalid Functions

```python
# ✗ Invalid - starts with underscore (private)
def _internal_function():
    pass

# ✗ Invalid - nested function
def outer():
    def inner():  # Won't be exposed as CLI command
        pass

# ✗ Invalid - special methods
def __init__(self):
    pass
```

## Type Annotations

Type annotations determine how arguments are parsed:

```python
from typing import List, Optional
from enum import Enum

class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

def demo_types(
    # Basic types
    name: str,                    # --name TEXT
    count: int = 1,               # --count INTEGER (default: 1)
    ratio: float = 0.5,           # --ratio FLOAT (default: 0.5)
    active: bool = False,         # --active (flag)
    
    # Enum type
    color: Color = Color.RED,     # --color {red,green,blue}
    
    # Optional type
    optional_value: Optional[int] = None,  # --optional-value INTEGER
    
    # List type (requires multiple flags)
    tags: List[str] = None        # --tags TEXT (can be used multiple times)
):
    """Demonstrate various type annotations."""
    print(f"Name: {name}")
    print(f"Count: {count}")
    print(f"Ratio: {ratio}")
    print(f"Active: {active}")
    print(f"Color: {color.value}")
    print(f"Optional: {optional_value}")
    print(f"Tags: {tags}")
```

## Module Organization

### Single File Module

For simple CLIs, keep everything in one file:

```python
# simple_tool.py
from auto_cli import CLI

# Configuration
DEFAULT_TIMEOUT = 30

# Helper functions (not exposed as commands)
def _validate_input(value):
    return value.strip()

# CLI commands
def command_one(arg: str):
    """First command."""
    validated = _validate_input(arg)
    print(f"Command 1: {validated}")

def command_two(count: int = 1):
    """Second command."""
    for i in range(count):
        print(f"Command 2: iteration {i+1}")

# Main entry point
if __name__ == "__main__":
    import sys
    cli = CLI.from_module(sys.modules[__name__])
    cli.run()
```

### Multi-Module Organization

For larger CLIs, organize commands into modules:

```python
# main.py
from auto_cli import CLI
import commands.file_ops
import commands.data_ops

if __name__ == "__main__":
    # Combine multiple modules
    cli = CLI()
    cli.add_module(commands.file_ops)
    cli.add_module(commands.data_ops)
    cli.run()
```

```python
# commands/file_ops.py
def copy_file(source: str, dest: str):
    """Copy a file."""
    # Implementation

def delete_file(path: str, force: bool = False):
    """Delete a file."""
    # Implementation
```

## Advanced Features

### Custom Function Options

```python
from auto_cli import CLI

def advanced_command(
    input_file: str,
    output_file: str,
    verbose: bool = False
):
    """Process a file with advanced options."""
    print(f"Processing {input_file} -> {output_file}")
    if verbose:
        print("Verbose mode enabled")

if __name__ == "__main__":
    import sys
    
    # Customize function metadata
    function_opts = {
        'advanced_command': {
            'description': 'Advanced file processing with extra options',
            'args': {
                'input_file': {'help': 'Path to input file'},
                'output_file': {'help': 'Path to output file'},
                'verbose': {'help': 'Enable verbose output'}
            }
        }
    }
    
    cli = CLI.from_module(
        sys.modules[__name__],
        function_opts=function_opts,
        title="Advanced File Processor"
    )
    cli.run()
```

### Excluding Functions

```python
from auto_cli import CLI

def public_command():
    """This will be exposed."""
    pass

def utility_function():
    """This won't be exposed."""
    pass

if __name__ == "__main__":
    import sys
    cli = CLI.from_module(
        sys.modules[__name__],
        exclude_functions=['utility_function']
    )
    cli.run()
```

## Best Practices

### 1. Clear Function Names

```python
# ✓ Good - descriptive verb
def convert_format(input_file: str, output_format: str):
    pass

# ✗ Avoid - vague name
def process(file: str):
    pass
```

### 2. Comprehensive Docstrings

```python
def analyze_data(
    input_file: str,
    threshold: float = 0.5,
    output_format: str = "json"
):
    """
    Analyze data from input file.
    
    Processes the input file and generates analysis results
    based on the specified threshold value.
    """
    pass
```

### 3. Validate Input Early

```python
def process_file(path: str, mode: str = "read"):
    """Process a file in the specified mode."""
    # Validate inputs
    if mode not in ["read", "write", "append"]:
        print(f"Error: Invalid mode '{mode}'")
        return
    
    if not os.path.exists(path) and mode == "read":
        print(f"Error: File '{path}' not found")
        return
    
    # Process file
    print(f"Processing {path} in {mode} mode")
```

### 4. Handle Errors Gracefully

```python
import sys

def risky_operation(value: int):
    """Perform operation that might fail."""
    try:
        result = 100 / value
        print(f"Result: {result}")
    except ZeroDivisionError:
        print("Error: Cannot divide by zero", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

## See Also

- [Class-based CLI](class-cli.md) - Alternative approach using classes
- [Type Annotations](../features/type-annotations.md) - Detailed type support
- [Examples](../guides/examples.md) - More module-based examples
- [Best Practices](../guides/best-practices.md) - Design patterns
- [API Reference](../reference/api.md) - Complete API docs

---
**Navigation**: [← Installation](installation.md) | [Class-based CLI →](class-cli.md)