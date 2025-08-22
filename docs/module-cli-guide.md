# Module-based CLI Guide

[← Back to Help](help.md) | [🏗️ Class-based Guide](class-cli-guide.md)

## Table of Contents
- [Overview](#overview)
- [When to Use Module-based CLI](#when-to-use-module-based-cli)
- [Basic Setup](#basic-setup)
- [Function Requirements](#function-requirements)
- [Complete Example Walkthrough](#complete-example-walkthrough)
- [Advanced Patterns](#advanced-patterns)
- [Best Practices](#best-practices)
- [See Also](#see-also)

## Overview

Module-based CLI creation is the original and simplest way to build command-line interfaces with Auto-CLI-Py. It works by introspecting functions within a Python module and automatically generating CLI commands from their signatures and docstrings.

**Perfect for**: Scripts, utilities, data processing tools, functional programming approaches, and simple command-line tools.

## When to Use Module-based CLI

Choose module-based CLI when you have:

✅ **Stateless operations** - Each command is independent  
✅ **Simple workflows** - Direct input → processing → output  
✅ **Functional style** - Functions that don't need shared state  
✅ **Utility scripts** - One-off tools and data processors  
✅ **Quick prototypes** - Fast CLI creation for existing functions  

❌ **Avoid when you need**:
- Persistent state between commands
- Complex initialization or teardown
- Object-oriented design patterns
- Configuration that persists across commands

## Basic Setup

### 1. Import and Create CLI

```python
from auto_cli import CLI
import sys

# At the end of your module
if __name__ == '__main__':
    cli = CLI.from_module(sys.modules[__name__], title="My CLI Tool")
    cli.display()
```

### 2. Factory Method Signature

```python
CLI.from_module(
    module,                    # The module containing functions
    title: str = None,         # CLI title (optional)
    function_opts: dict = None,# Per-function options (optional)
    theme_name: str = 'universal', # Theme name
    no_color: bool = False,    # Disable colors
    completion: bool = True    # Enable shell completion
)
```

## Function Requirements

### Type Annotations (Required)

All CLI functions **must** have type annotations for parameters:

```python
# ✅ Good - All parameters have type annotations
def process_data(input_file: str, output_dir: str, verbose: bool = False) -> None:
    """Process data from input file to output directory."""
    pass

# ❌ Bad - Missing type annotations
def process_data(input_file, output_dir, verbose=False):
    pass
```

### Docstrings (Recommended)

Functions should have docstrings for help text generation:

```python
def analyze_logs(
    log_file: str,
    pattern: str,
    case_sensitive: bool = False,
    max_lines: int = 1000
) -> None:
    """
    Analyze log files for specific patterns.
    
    This function searches through log files and reports
    matches for the specified pattern.
    
    Args:
        log_file: Path to the log file to analyze
        pattern: Regular expression pattern to search for
        case_sensitive: Whether to perform case-sensitive matching
        max_lines: Maximum number of lines to process
    """
    # Implementation here
```

### Supported Parameter Types

| Type | CLI Argument | Example |
|------|-------------|---------|
| `str` | `--name VALUE` | `--name "John"` |
| `int` | `--count 42` | `--count 100` |
| `float` | `--rate 3.14` | `--rate 2.5` |
| `bool` | `--verbose` (flag) | `--verbose` |
| `Enum` | `--level CHOICE` | `--level INFO` |
| `List[str]` | `--items A B C` | `--items file1.txt file2.txt` |

## Complete Example Walkthrough

Let's build a complete CLI tool for file processing using [mod_example.py](../mod_example.py):

### Step 1: Define Functions

```python
# mod_example.py
"""File processing utility with various operations."""

from enum import Enum
from pathlib import Path
from typing import List

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info" 
    WARNING = "warning"
    ERROR = "error"

def hello(name: str = "World", excited: bool = False) -> None:
    """Greet someone by name."""
    greeting = f"Hello, {name}!"
    if excited:
        greeting += " 🎉"
    print(greeting)

def count_lines(file_path: str, ignore_empty: bool = True) -> None:
    """Count lines in a text file."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"Error: File '{file_path}' not found")
        return
    
    with path.open('r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if ignore_empty:
        lines = [line for line in lines if line.strip()]
    
    print(f"Lines in '{file_path}': {len(lines)}")

def process_files(
    input_dir: str,
    output_dir: str,
    extensions: List[str],
    log_level: LogLevel = LogLevel.INFO,
    dry_run: bool = False
) -> None:
    """Process files from input directory to output directory."""
    print(f"Processing files from {input_dir} to {output_dir}")
    print(f"Extensions: {extensions}")
    print(f"Log level: {log_level.value}")
    
    if dry_run:
        print("DRY RUN - No files will be modified")
    
    # Processing logic would go here
    print("Processing completed!")
```

### Step 2: Create CLI

```python
# At the end of mod_example.py
if __name__ == '__main__':
    from auto_cli import CLI
    import sys
    
    # Optional: Configure specific functions
    function_opts = {
        'hello': {
            'description': 'Simple greeting command'
        },
        'count_lines': {
            'description': 'Count lines in text files'
        },
        'process_files': {
            'description': 'Batch file processing with filtering'
        }
    }
    
    cli = CLI.from_module(
        sys.modules[__name__],
        title="File Processing Utility",
        function_opts=function_opts,
        theme_name="colorful"
    )
    cli.display()
```

### Step 3: Usage Examples

```bash
# Run the CLI
python mod_example.py

# Use individual commands
python mod_example.py hello --name "Alice" --excited
python mod_example.py count-lines --file-path data.txt
python mod_example.py process-files --input-dir ./input --output-dir ./output --extensions txt py --log-level DEBUG --dry-run
```

## Advanced Patterns

### Custom Function Configuration

```python
function_opts = {
    'function_name': {
        'description': 'Custom description override',
        'hidden': False,           # Hide from CLI (default: False)
        'aliases': ['fn', 'func'], # Alternative command names
    }
}

cli = CLI.from_module(
    sys.modules[__name__],
    function_opts=function_opts
)
```

### Module Docstring for Title

If you don't provide a title, the CLI will use the module's docstring:

```python
"""
My Amazing CLI Tool

This tool provides various utilities for data processing
and file manipulation tasks.
"""

# Functions here...

if __name__ == '__main__':
    # Title will be extracted from module docstring
    cli = CLI.from_module(sys.modules[__name__])
    cli.display()
```

### Complex Type Handling

```python
from pathlib import Path
from typing import Optional, Union

def advanced_function(
    input_path: Path,                    # Automatically converted to Path
    output_path: Optional[str] = None,   # Optional parameter  
    mode: Union[str, int] = "auto",      # Union types supported
    config_data: dict = None             # Complex types as JSON strings
) -> None:
    """Function with advanced type annotations."""
    pass
```

### Error Handling and Validation

```python
def validate_input(data_file: str, min_size: int = 0) -> None:
    """Validate input file meets requirements."""
    path = Path(data_file)
    
    # Validation logic
    if not path.exists():
        print(f"❌ Error: File '{data_file}' does not exist")
        return
    
    if path.stat().st_size < min_size:
        print(f"❌ Error: File too small (minimum: {min_size} bytes)")
        return
    
    print(f"✅ File '{data_file}' is valid")
```

## Best Practices

### 1. Function Design

```python
# ✅ Good: Clear, focused function
def convert_image(input_file: str, output_format: str = "PNG") -> None:
    """Convert image to specified format."""
    pass

# ❌ Avoid: Too many parameters
def do_everything(file1, file2, file3, opt1, opt2, opt3, flag1, flag2):
    pass
```

### 2. Parameter Organization

```python
# ✅ Good: Required parameters first, optional with defaults
def process_data(
    input_file: str,           # Required
    output_file: str,          # Required  
    format_type: str = "json", # Optional with sensible default
    verbose: bool = False      # Optional flag
) -> None:
    pass
```

### 3. Documentation

```python
def complex_operation(
    data_source: str,
    filters: List[str],
    output_format: str = "csv"
) -> None:
    """
    Perform complex data operation with filtering.
    
    Processes data from the specified source, applies the given
    filters, and outputs results in the requested format.
    
    Args:
        data_source: Path to input data file or database URL
        filters: List of filter expressions (e.g., ['age>18', 'status=active'])
        output_format: Output format - csv, json, or xml
        
    Examples:
        Basic usage:
        $ tool complex-operation data.csv --filters 'age>25' --output-format json
        
        Multiple filters:
        $ tool complex-operation db://localhost --filters 'dept=engineering' 'salary>50000'
    """
    pass
```

### 4. Module Organization

```python
# mod_example.py - Well-organized module structure

"""Data Processing CLI Tool

A comprehensive tool for data analysis and file processing operations.
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional
import sys

# Enums and types first
class OutputFormat(Enum):
    CSV = "csv"
    JSON = "json" 
    XML = "xml"

# Core functions
def analyze_data(source: str, format_type: OutputFormat = OutputFormat.CSV) -> None:
    """Analyze data from source file."""
    pass

def convert_files(input_dir: str, output_dir: str) -> None:
    """Convert files between directories."""
    pass

# CLI setup at bottom
if __name__ == '__main__':
    from auto_cli import CLI
    
    cli = CLI.from_module(
        sys.modules[__name__],
        title="Data Processing Tool",
        theme_name="universal"
    )
    cli.display()
```

## See Also

- [Class-based CLI Guide](class-cli-guide.md) - For stateful applications
- [Type Annotations](features/type-annotations.md) - Detailed type system guide  
- [Theme System](features/themes.md) - Customizing appearance
- [Complete Examples](guides/examples.md) - More real-world examples
- [Best Practices](guides/best-practices.md) - General CLI development tips

---

**Navigation**: [← Help Hub](help.md) | [Class-based Guide →](class-cli-guide.md)  
**Example**: [mod_example.py](../mod_example.py)