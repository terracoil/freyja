![Freyja Action](https://github.com/terracoil/freyja/raw/main/docs/freyja-action.png)
# API Reference

[↑ Documentation Hub](../README.md)

Complete API documentation and technical reference for freyja.

## Reference Documentation

### 📚 [Complete API](api.md)
Full API documentation for all public interfaces.
- FreyjaCLI class methods and properties
- Constructor parameters
- Configuration options
- Return types and exceptions

### 🏗️ [FreyjaCLI Class](api.md)
Detailed documentation of the FreyjaCLI class.
- Constructor parameters
- Instance methods
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

```python
from freyja import FreyjaCLI

cli = FreyjaCLI(
  MyClass,
  title="My CLI",
  theme_name="colorful",
  function_opts={
    'method_name': {
      'description': 'Custom description',
      'hidden': False,
    },
  },
)
cli.run()
```

### Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target` | `type \| Sequence[type]` | required | Class (or list of classes) to build CLI from |
| `title` | `str \| None` | `None` | CLI title (from class docstring if None) |
| `theme_name` | `str` | `"universal"` | Theme name (`"colorful"` or `"universal"`) |
| `no_color` | `bool` | `False` | Disable colored output |
| `completion` | `bool` | `True` | Enable shell completion |
| `function_opts` | `dict \| None` | `None` | Per-method configuration |

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

### Instance Methods

```python
def run(self, args: list[str] | None = None) -> Any:
    """Parse arguments and execute the appropriate command."""

def create_parser(self, no_color: bool = False) -> argparse.ArgumentParser:
    """Create the argparse parser used internally (escape hatch)."""
```

## Architecture Overview

### Component Structure
```
freyja/
├── freyja_cli.py        # Main FreyjaCLI entry point
├── __init__.py          # Package exports
├── cli/                 # CLI coordination + execution
├── command/             # Command discovery and execution
├── parser/              # argparse integration
├── completion/          # Shell completion
├── help/                # Help formatting
├── theme/               # Theme system
└── utils/               # Helper utilities
```

### Design Principles
- Zero configuration by default
- Type-driven interface generation
- Extensible and customizable
- Performance optimized
- Well-tested and documented

## Next Steps

- Explore the [Complete API](api.md)
- Review [Type Annotations](../features/type-annotations.md) and [Positional Parameters](../features/positional-parameters.md)
- See [Examples](../guides/examples.md) for usage

---

**Need source code?** Visit [GitHub](https://github.com/terracoil/freyja)
