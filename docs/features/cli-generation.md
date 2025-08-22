# CLI Generation

[← Back to Help](../help.md)

## Table of Contents
- [How It Works](#how-it-works)
- [Function Introspection](#function-introspection)
- [Signature Analysis](#signature-analysis)
- [Parameter Mapping](#parameter-mapping)
- [Default Value Handling](#default-value-handling)
- [Help Text Generation](#help-text-generation)
- [Advanced Features](#advanced-features)

## How It Works

Auto-cli-py uses Python's introspection capabilities to automatically generate command-line interfaces from function signatures. This eliminates the need for manual argument parser setup while providing a natural, Pythonic way to define CLI commands.

### The Magic Behind the Scenes

```python
def example_function(name: str, count: int = 5, verbose: bool = False):
    """Example function that becomes a CLI command."""
    pass
```

Auto-cli-py automatically:
1. **Analyzes** the function signature using `inspect.signature()`
2. **Maps** parameters to CLI arguments based on types and defaults
3. **Generates** help text from docstrings and type information
4. **Creates** an `argparse.ArgumentParser` with appropriate configuration
5. **Handles** argument parsing and validation

## Function Introspection

### Python's Inspect Module

Auto-cli-py leverages Python's built-in `inspect` module to examine function signatures:

```python
import inspect

def user_function(param1: str, param2: int = 42):
    """Example function."""
    pass

# What auto-cli-py sees:
sig = inspect.signature(user_function)
for param_name, param in sig.parameters.items():
    print(f"Parameter: {param_name}")
    print(f"  Type: {param.annotation}")
    print(f"  Default: {param.default}")
    print(f"  Required: {param.default == inspect.Parameter.empty}")
```

### Supported Function Features

**Parameter Types:**
- Positional arguments
- Keyword arguments with defaults
- Type annotations
- Docstring documentation

**What Gets Analyzed:**
- Parameter names → CLI argument names
- Type annotations → Argument type validation
- Default values → Optional vs required arguments
- Docstrings → Help text generation

## Signature Analysis

### Parameter Classification

Auto-cli-py classifies function parameters into CLI argument types:

```python
def comprehensive_example(
    required_arg: str,                    # Required positional
    optional_with_default: str = "hello", # Optional with default
    flag: bool = False,                   # Boolean flag
    number: int = 42,                     # Typed with default
    choice: Optional[str] = None          # Optional nullable
):
    pass
```

**Generated CLI:**
```bash
comprehensive-example REQUIRED_ARG 
    [--optional-with-default TEXT]
    [--flag / --no-flag]
    [--number INTEGER]
    [--choice TEXT]
```

### Type Annotation Processing

**Basic Types:**
```python
def typed_function(
    text: str,      # → TEXT argument
    number: int,    # → INTEGER argument  
    decimal: float, # → FLOAT argument
    flag: bool      # → Boolean flag
):
    pass
```

**Complex Types:**
```python
from typing import Optional, List
from enum import Enum
from pathlib import Path

class Mode(Enum):
    FAST = "fast"
    SLOW = "slow"

def advanced_types(
    files: List[Path],        # → Multiple file arguments
    mode: Mode,               # → Choice from enum values
    output: Optional[Path],   # → Optional file path
    config: dict = {}         # → JSON string parsing
):
    pass
```

## Parameter Mapping

### Naming Conventions

Auto-cli-py automatically converts Python parameter names to CLI argument names:

```python
# Python parameter → CLI argument
user_name        → --user-name
input_file       → --input-file  
maxRetryCount    → --max-retry-count
enableVerbose    → --enable-verbose
```

### Argument Types

**Required Arguments:**
```python
def cmd(required: str):  # No default value
    pass
# Usage: cmd REQUIRED
```

**Optional Arguments:**
```python  
def cmd(optional: str = "default"):  # Has default value
    pass
# Usage: cmd [--optional TEXT]
```

**Boolean Flags:**
```python
def cmd(flag: bool = False):
    pass
# Usage: cmd [--flag] or cmd [--no-flag]
```

### Special Parameter Handling

**Variadic Arguments:**
```python
def cmd(*args: str):         # Not supported - use List[str] instead
    pass

def cmd(files: List[str]):   # Supported - multiple arguments
    pass
# Usage: cmd --files file1.txt file2.txt file3.txt
```

**Keyword Arguments:**
```python
def cmd(**kwargs):           # Not supported - use explicit parameters
    pass
```

## Default Value Handling

### Default Value Types

**Primitive Defaults:**
```python
def example(
    text: str = "hello",      # String default
    count: int = 5,           # Integer default  
    ratio: float = 1.5,       # Float default
    active: bool = True       # Boolean default (--active/--no-active)
):
    pass
```

**Complex Defaults:**
```python
from pathlib import Path

def example(
    output_dir: Path = Path("."),           # Path default
    config: dict = {},                      # Empty dict (becomes None)
    items: List[str] = []                   # Empty list (becomes None)
):
    pass
```

### None vs Empty Defaults

```python
from typing import Optional

def example(
    explicit_none: Optional[str] = None,    # Truly optional
    empty_list: List[str] = [],             # Converted to None  
    empty_dict: dict = {}                   # Converted to None
):
    pass
```

## Help Text Generation

### Docstring Processing

Auto-cli-py extracts help text from function docstrings:

```python
def well_documented(param1: str, param2: int = 5):
    """Process data with specified parameters.
    
    This function demonstrates how docstrings are used to generate
    comprehensive help text for CLI commands.
    
    Args:
        param1: The input string to process
        param2: Number of iterations to perform
        
    Returns:
        Processed result
        
    Example:
        well-documented "input text" --param2 10
    """
    pass
```

**Generated Help:**
```
Process data with specified parameters.

This function demonstrates how docstrings are used to generate
comprehensive help text for CLI commands.

positional arguments:
  param1                The input string to process

optional arguments:
  --param2 INTEGER      Number of iterations to perform (default: 5)
```

### Parameter Documentation

**Google Style Docstrings:**
```python
def google_style(param1: str, param2: int):
    """Function with Google-style parameter documentation.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    """
    pass
```

**NumPy Style Docstrings:**
```python  
def numpy_style(param1: str, param2: int):
    """Function with NumPy-style parameter documentation.
    
    Parameters
    ----------
    param1 : str
        Description of param1
    param2 : int
        Description of param2
    """
    pass
```

## Advanced Features

### Custom Argument Configuration

```python
from auto_cli import CLI


def custom_config_example(input_file: str):
  """Example with custom configuration."""
  pass


# Custom function options
function_opts = {
  'custom_config_example': {
    'description': 'Override the function docstring',
    'hidden': False,  # Show/hide from help
    'aliases': ['custom', 'config']  # Command aliases
  }
}

cli = CLI(
  sys.modules[__name__],
  function_opts=function_opts
)
```

### Module-Level Configuration

```python
# Configure multiple functions
CLI_CONFIG = {
    'title': 'My Advanced CLI',
    'description': 'A comprehensive tool for data processing',
    'epilog': 'For more help, visit https://example.com/docs'
}

cli = CLI(sys.modules[__name__], **CLI_CONFIG)
```

### Exclusion Patterns

```python
def _private_function():
    """Private functions (starting with _) are automatically excluded."""
    pass

def internal_helper():
    """Use function_opts to exclude specific functions."""
    pass

function_opts = {
    'internal_helper': {'hidden': True}
}
```

### Error Handling

```python
def robust_command(port: int):
    """Command with input validation."""
    if port < 1 or port > 65535:
        raise ValueError(f"Invalid port: {port}. Must be 1-65535.")
    
    # Auto-cli-py will catch and display the ValueError appropriately
    print(f"Connecting to port {port}")
```

## See Also
- [Type Annotations](type-annotations.md) - Detailed type system documentation
- [Subcommands](subcommands.md) - Organizing complex CLIs  
- [Basic Usage](../getting-started/basic-usage.md) - Getting started guide
- [API Reference](../reference/api.md) - Complete technical reference

---
**Navigation**: [Type Annotations →](type-annotations.md)  
**Parent**: [Help](../help.md)  
**Children**: [Type Annotations](type-annotations.md) | [Subcommands](subcommands.md)
