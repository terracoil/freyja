![Freyja Action](https://github.com/terracoil/freyja/raw/main/docs/freyja-action.png)
# API Reference

[↑ Documentation Hub](../README.md)

Complete API documentation and technical reference for freyja.

## Reference Documentation

### 📚 [Complete API](api.md)
Full API documentation for all public interfaces.
- CLI class methods and properties
- Factory methods (from_module, from_class)
- Configuration options
- Return types and exceptions

### 🏗️ [CLI Class](api.md)
Detailed documentation of the CLI class.
- Constructor parameters
- Instance methods
- Class methods
- Properties and attributes
- Internal behavior

### 🔤 [Type Annotations](../features/type-annotations.md)
Complete guide to supported parameter types.
- Type mapping table
- Collection types (List, Dict, etc.)
- Optional and Union types
- Enum type support
- Path and File types

## Quick Reference

### CLI Creation

**Module-based CLI**

```python
from src import CLI
import sys

cli = CLI(
  sys.modules[__name__],
  title="My Freyja",
  theme_name="universal",
  no_color=False,
  completion=True
)
cli.display()
```

**Class-based CLI**

```python
from src import CLI

cli = CLI(
  MyClass,
  title="My Freyja",
  theme_name="colorful",
  function_opts={
    'method_name': {
      'description': 'Custom description',
      'hidden': False
    }
  }
)
cli.display()
```

### Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | str | None | CLI title (from docstring if None) |
| `theme_name` | str | "universal" | Theme name ("colorful" or "universal") |
| `no_color` | bool | False | Disable colored output |
| `completion` | bool | True | Enable shell completion |
| `function_opts` | dict | None | Per-function/method configuration |

### Type Mappings

| Python Type | CLI Argument | Example |
|-------------|--------------|---------|
| `str` | String value | `--name "John"` |
| `int` | Integer value | `--count 42` |
| `float` | Float value | `--rate 3.14` |
| `bool` | Flag (no value) | `--verbose` |
| `List[str]` | Multiple values | `--files a.txt b.txt` |
| `Enum` | Choice from enum | `--level INFO` |
| `Path` | Path value | `--config /etc/app.conf` |

### Method Signatures

**Factory Methods**
```python
@classmethod
def from_module(
    cls,
    module,
    title: Optional[str] = None,
    **kwargs
) -> 'Freyja':
    """Create Freyja from module functions."""

@classmethod  
def from_class(
    cls,
    class_type: Type,
    title: Optional[str] = None,
    **kwargs
) -> 'Freyja':
    """Create Freyja from class methods."""
```

**Instance Methods**
```python
def display(self) -> Optional[int]:
    """Display Freyja interface and execute command tree."""

def run(self) -> Optional[int]:
    """Alias for display() method."""

def add_command(
    self,
    name: str,
    function: Callable,
    description: Optional[str] = None
) -> None:
    """Add a command to the Freyja."""
```

## Architecture Overview

### Component Structure
```
freya/
├── cli.py          # Main CLI class
├── __init__.py     # Package exports
├── theme.py        # Theme system
├── completion.py   # Shell completion
└── utils.py        # Helper functions
```

### Design Principles
- Zero configuration by default
- Type-driven interface generation
- Extensible and customizable
- Performance optimized
- Well-tested and documented

## Next Steps

- Explore the [Complete API](api.md)
- Understand the [CLI Class](api.md)
- Review [Type Annotations](../features/type-annotations.md) and [Positional Parameters](../features/positional-parameters.md)
- See [Examples](../guides/examples.md) for usage

---

**Need source code?** Visit [GitHub](https://github.com/terracoil/freyja)