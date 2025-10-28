# 🛡️ Guard Clauses in Freyja

## 📍 Navigation
**You are here**: Features > Guard Clauses

**Parents**:
- [🏠 Main README](../../README.md) - Project overview and quick start
- [📚 Documentation Hub](../README.md) - Complete documentation index
- [✨ Features](README.md) - All Freyja features

**Related**:
- [🔧 Development > Submodules](../development/submodules.md) - Git submodule workflow for modgud
- [📝 Type Annotations](type-annotations.md) - Type-driven CLI generation
- [⚠️ Error Handling](error-handling.md) - Error handling patterns

---

## 📑 Table of Contents
- [🔍 Overview](#-overview)
- [🏁 Basic Usage](#-basic-usage)
- [🎯 Available Guards](#-available-guards)
- [📊 Position Parameters](#-position-parameters)
- [⚙️ Error Handling](#️-error-handling)
- [💫 Implicit Returns](#-implicit-returns)
- [💼 Real-World Examples](#-real-world-examples)
- [🏗️ Architecture](#️-architecture)
- [🎨 Custom Guards](#-custom-guards)
- [💡 Best Practices](#-best-practices)
- [🔗 See Also](#-see-also)

---

## 🔍 Overview

Guards are decorators that validate function parameters before execution. They replace repetitive validation boilerplate with concise, reusable validation logic.

> **📦 Powered by modgud**: Guard functionality is provided by [modgud](https://pypi.org/project/modgud/), included as a Git submodule in Freyja. For standalone usage outside of Freyja, install: `pip install modgud`

### Benefits

- **Cleaner Code**: Validation logic moves to decorators
- **Consistent Patterns**: Standardized parameter checking
- **Better Error Messages**: Clear, formatted error messages
- **Type Safety**: Validates at function entry
- **Maintains Single Return Point**: Guards handle early exits

## 🏁 Basic Usage

```python
from freyja.utils.guards import guarded, not_none, in_range

@guarded(not_none("value", 1), implicit_return=False)
def process_data(self, value: str) -> str:
  """Process data with validation."""
  return f"Processed: {value}"
```

## 🎯 Available Guards

### Common Guards

Imported from `freyja.utils.guards`:

- **`not_none(param_name, position=0)`** - Parameter must not be None
- **`not_empty(param_name, position=0)`** - String/list must not be empty
- **`positive(param_name, position=0)`** - Number must be > 0
- **`in_range(min_val, max_val, param_name, position=0)`** - Number must be in range [min, max]
- **`type_check(expected_type, param_name, position=0)`** - Parameter must match type
- **`matches_pattern(pattern, param_name, position=0)`** - String must match regex
- **`valid_file_path(param_name, position=0)`** - Must be valid file path
- **`valid_url(param_name, position=0)`** - Must be valid URL
- **`valid_enum(enum_class, param_name, position=0)`** - Must be valid enum value

### Freyja-Specific Guards

Imported from `freyja.utils.cli_guards` (auto-registered):

- **`valid_command_name(param_name, position=0)`** - Valid CLI command name (letters, numbers, hyphens, underscores)
- **`valid_theme_name(param_name, position=0)`** - Valid theme ('colorful' or 'universal')
- **`valid_shell_type(param_name, position=0)`** - Valid shell type ('bash', 'zsh', 'fish')

## 📊 Position Parameters

**CRITICAL**: For instance methods and classmethods, you **must** specify the position parameter since `self`/`cls` occupies position 0.

### Instance Methods

```python
class MyClass:
  @guarded(not_none("data", 1), implicit_return=False)  # position 1 for first parameter
  def process(self, data: str) -> str:
    return f"Processing: {data}"
```

### Classmethods

```python
class MyClass:
  @classmethod  # @classmethod MUST come first
  @guarded(
    in_range(0, 255, "r", 1),  # position 1, 2, 3 for parameters
    in_range(0, 255, "g", 2),
    in_range(0, 255, "b", 3),
    implicit_return=False
  )
  def from_rgb(cls, r: int, g: int, b: int):
    return cls(r / 255.0, g / 255.0, b / 255.0)
```

### Static Methods

```python
class MyClass:
  @staticmethod
  @guarded(not_none("value", 0), implicit_return=False)  # position 0 for static
  def validate(value: str) -> bool:
    return True
```

## ⚙️ Error Handling

By default, guards raise `GuardClauseError` on validation failure. You can customize the error type:

```python
from freyja.utils.guards import guarded, in_range

@guarded(
  in_range(0.0, 1.0, "r", 1),
  in_range(0.0, 1.0, "g", 2),
  on_error=ValueError,  # Raise ValueError instead
  implicit_return=False
)
def __init__(self, r: float, g: float):
  self._r = r
  self._g = g
```

## 💫 Implicit Returns

The `@guarded` decorator supports implicit returns (Ruby-style expression-oriented code):

```python
@guarded(not_none("x", 1))  # implicit_return=True by default
def calculate(self, x: int):
  result = x * 2
  result  # Implicit return - no explicit 'return' needed
```

For complex methods with conditionals, use `implicit_return=False`:

```python
@guarded(not_none("data", 1), implicit_return=False)
def process(self, data: str) -> str:
  result = None
  if data:
    result = f"Processed: {data}"
  return result  # Explicit return required
```

## 💼 Real-World Examples

### Range Validation (RGB Color)

```python
from freyja.utils.guards import guarded, in_range

class RGB:
  @guarded(
    in_range(0.0, 1.0, "r", 1),
    in_range(0.0, 1.0, "g", 2),
    in_range(0.0, 1.0, "b", 3),
    on_error=ValueError,
    implicit_return=False
  )
  def __init__(self, r: float, g: float, b: float):
    self._r = r
    self._g = g
    self._b = b
```

### Parameter Validation (CLI)

```python
from freyja.utils.guards import guarded, not_none, not_empty

class ValidationService:
  @staticmethod
  @guarded(not_none("cls", 0), not_none("context", 1), implicit_return=False)
  def validate_constructor_parameters(cls: type, context: str) -> None:
    # Validation logic here
    pass
```

### Collection Validation

```python
from freyja.utils.guards import guarded, not_none

class ArgumentPreprocessor:
  @guarded(not_none("args", 1), implicit_return=False)
  def preprocess_args(self, args: list[str]) -> list[str]:
    # Preprocessing logic
    return processed_args
```

## 🏗️ Architecture

### Vendored modgud

Freyja uses a **vendored** copy of modgud via git submodule at `freyja/utils/modgud/`. This maintains Freyja's zero-dependency approach while providing guard functionality.

**Benefits:**
- No external pip dependencies
- Version control over guard behavior
- Namespace isolation (no conflicts with user's modgud)

**Import Pattern:**
```python
from freyja.utils.guards import guarded, not_none  # Always import from freyja.utils
```

### Single Return Point Architecture

Guards integrate seamlessly with Freyja's single return point rule:

- Guards handle early exits (validation failures)
- Main function body maintains single return
- `implicit_return=False` ensures explicit returns for complex logic

## 🎨 Custom Guards

You can register custom Freyja-specific guards:

```python
from freyja.utils.guards import register_guard
from freyja.utils.modgud.modgud.guarded_expression.common_guards import CommonGuards
from freyja.utils.modgud.modgud.guarded_expression.types import GuardFunction

def my_custom_guard(param_name: str = 'value', position: int = 0) -> GuardFunction:
  def check(*args, **kwargs):
    value = CommonGuards._extract_param(param_name, position, args, kwargs, default=None)
    if value is None:
      return f'{param_name} is required'
    if not some_validation(value):
      return f'{param_name} failed custom validation'
    return True
  return check

# Register in 'freyja' namespace
register_guard('my_custom_guard', my_custom_guard, namespace='freyja')
```

## 💡 Best Practices

1. **Always specify position** for instance/class methods (position 1+ for parameters after self/cls)
2. **Use `implicit_return=False`** for methods with complex control flow
3. **Use `on_error=ValueError`** when tests expect specific exception types
4. **Import from `freyja.utils.guards`** (never directly from modgud submodule)
5. **Keep guards simple** - complex validation belongs in dedicated functions
6. **Combine guards** - multiple guards on one function for comprehensive validation

## 🔗 See Also

- [Git Submodules Documentation](../development/submodules.md) - Working with vendored modgud
- [modgud GitHub](https://github.com/user/modgud) - Upstream guard library
- [CLAUDE.md](../../CLAUDE.md) - Freyja coding standards
