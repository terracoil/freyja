# 📖 Freyja API Reference

## 📍 Navigation
**You are here**: Documentation Hub > API Reference

**Parents**:
- [🏠 Main README](../README.md) - Project overview and quick start
- [📚 Documentation Hub](README.md) - Complete documentation index

**Related**:
- [⚙️ How It Works](how-it-works.md) - Internal architecture explained
- [🏗️ Architecture](architecture/README.md) - Visual architecture diagrams
- [✨ Features](features/README.md) - Feature documentation
- [👤 User Guide](user-guide/README.md) - Building CLIs with Freyja

---

## 📑 Table of Contents
- [🎯 Public API](#-public-api)
  - [FreyjaCLI](#freyjacli)
- [🏗️ Architecture Components](#️-architecture-components)
  - [CLI Layer](#cli-layer)
  - [Command Layer](#command-layer)
  - [Parser Layer](#parser-layer)
  - [Shared Models](#shared-models)
  - [Completion System](#completion-system)
  - [Utilities](#utilities)
- [🛡️ Guards (modgud)](#️-guards-modgud)
- [🎨 Themes](#-themes)
- [📝 Type Support](#-type-support)

---

## 🎯 Public API

The Freyja public API consists primarily of the `FreyjaCLI` class. All other classes are internal implementation details.

### FreyjaCLI

**Location**: `freyja.FreyjaCLI`

The main entry point for creating command-line interfaces from Python classes.

#### Class Signature

```python
class FreyjaCLI:
    def __init__(
        self,
        target: type[Any] | Sequence[type[Any]],
        title: str | None = None,
        method_filter: Callable | None = None,
        theme = None,
        alphabetize: bool = True,
        completion: bool = True,
        theme_tuner = False,
        # Output capture parameters
        capture_output: bool = False,
        capture_stdout: bool = True,
        capture_stderr: bool = False,
        capture_stdin: bool = False,
        output_capture_config: dict[str, Any] | None = None,
    )
```

#### Parameters

**target** (`type[Any] | Sequence[type[Any]]`)
- The Python class or list of classes to generate CLI from
- **Required**: All constructor parameters must have default values
- **Supported**: Classes with direct methods and/or inner classes
- **Example**: `MyClass` or `[SystemCommands, MyClass]`

**title** (`str | None = None`)
- CLI application title shown in help text
- **Default**: Auto-generated from class name
- **Example**: `"My Amazing CLI Tool"`

**method_filter** (`Callable | None = None`)
- Optional function to filter which methods become commands
- **Signature**: `(method_name: str, method: Callable) -> bool`
- **Default**: All public methods (not starting with `_`)
- **Example**: `lambda name, method: not name.startswith('internal')`

**theme** (`Theme | None = None`)
- Optional theme for colored output
- **Default**: Built-in colorful theme
- **See**: [Themes Documentation](features/themes.md)

**alphabetize** (`bool = True`)
- Whether to sort commands and options alphabetically in help
- **Default**: `True`
- **Note**: System commands always appear first

**completion** (`bool = True`)
- Enable shell completion support
- **Default**: `True`
- **Shells**: Bash, Zsh, Fish, PowerShell
- **See**: [Shell Completion](features/shell-completion.md)

**theme_tuner** (`bool = False`)
- Enable interactive theme tuning command
- **Default**: `False`
- **Adds**: `theme-tuner` system command

**capture_output** (`bool = False`)
- Enable output capture feature
- **Default**: `False` (opt-in for performance)
- **See**: [Output Capture](features/output-capture.md)

**capture_stdout** (`bool = True`)
- Capture stdout when output capture is enabled
- **Default**: `True`
- **Requires**: `capture_output=True`

**capture_stderr** (`bool = False`)
- Capture stderr when output capture is enabled
- **Default**: `False`
- **Requires**: `capture_output=True`

**capture_stdin** (`bool = False`)
- Capture stdin when output capture is enabled
- **Default**: `False`
- **Requires**: `capture_output=True`

**output_capture_config** (`dict[str, Any] | None = None`)
- Advanced output capture configuration
- **Default**: `None`
- **See**: [Output Capture](features/output-capture.md)

#### Methods

##### `run(args: list[str] = None) -> Any`

Parse arguments and execute the appropriate command.

**Parameters**:
- `args` (`list[str] | None`): Optional command line arguments. Uses `sys.argv` if `None`.

**Returns**: Command execution result

**Example**:
```python
cli = FreyjaCLI(MyClass)
result = cli.run()  # Uses sys.argv

# Or with custom args:
result = cli.run(['command', '--option', 'value'])
```

##### `create_parser(no_color: bool = False)`

Create the argument parser using the pre-built command tree.

**Parameters**:
- `no_color` (`bool`): Disable colored output

**Returns**: Configured `argparse.ArgumentParser`

**Example**:
```python
cli = FreyjaCLI(MyClass)
parser = cli.create_parser()
args = parser.parse_args(['command', '--help'])
```

**Note**: Typically not needed - `run()` calls this automatically.

#### Output Capture API

##### `output_capture` (property)

Access the OutputCapture instance if enabled.

**Returns**: `OutputCapture | None`

**Example**:
```python
cli = FreyjaCLI(MyClass, capture_output=True)
cli.run()
if cli.output_capture:
    print("Output captured!")
```

##### `get_captured_output(stream: str = "stdout") -> str | None`

Get captured output from a specific stream.

**Parameters**:
- `stream` (`str`): Stream name (`'stdout'`, `'stderr'`, `'stdin'`)

**Returns**: Captured content or `None` if capture disabled

**Example**:
```python
cli = FreyjaCLI(MyClass, capture_output=True, capture_stdout=True)
cli.run(['command'])
output = cli.get_captured_output('stdout')
print(f"Captured: {output}")
```

##### `get_all_captured_output() -> dict[str, str | None]`

Get all captured output from all streams.

**Returns**: Dictionary with captured content for each stream

**Example**:
```python
cli = FreyjaCLI(MyClass, capture_output=True)
cli.run()
all_output = cli.get_all_captured_output()
print(f"stdout: {all_output['stdout']}")
print(f"stderr: {all_output['stderr']}")
```

##### `clear_captured_output() -> None`

Clear the captured output buffer.

**Example**:
```python
cli = FreyjaCLI(MyClass, capture_output=True)
cli.run(['command1'])
output1 = cli.get_captured_output()
cli.clear_captured_output()
cli.run(['command2'])
output2 = cli.get_captured_output()  # Only command2 output
```

##### `enable_output_capture(**kwargs) -> None`

Enable output capture dynamically after initialization.

**Parameters**:
- `**kwargs`: OutputCaptureConfig parameters

**Example**:
```python
cli = FreyjaCLI(MyClass)  # No capture initially
cli.enable_output_capture(capture_stdout=True, capture_stderr=True)
cli.run()  # Output now captured
```

##### `disable_output_capture() -> None`

Disable output capture dynamically.

**Example**:
```python
cli = FreyjaCLI(MyClass, capture_output=True)
cli.disable_output_capture()
cli.run()  # No capture
```

##### `capture_output(**kwargs)` (context manager)

Context manager for temporary output capture.

**Parameters**:
- `**kwargs`: OutputCaptureConfig parameters

**Example**:
```python
cli = FreyjaCLI(MyClass)

# Capture only for specific execution
with cli.capture_output(capture_stdout=True):
    cli.run(['command'])
    output = cli.get_captured_output('stdout')

# No capture after context
cli.run(['other-command'])
```

#### Properties

**target_class** (`type[Any]`)
- The primary class being used for CLI generation
- **Read-only**

**target_classes** (`list[type[Any]]`)
- All classes being used for CLI generation
- **Read-only**

**commands** (`dict`)
- Dictionary representation of the command tree
- **Read-only**

#### Complete Usage Example

```python
from freyja import FreyjaCLI

class DatabaseCLI:
    """Database management CLI."""

    def __init__(self, connection_string: str = "sqlite:///db.sqlite", verbose: bool = False):
        """Initialize database connection."""
        self.connection_string = connection_string
        self.verbose = verbose

    class Migrations:
        """Database migration commands."""

        def __init__(self, auto_approve: bool = False):
            """Migration settings."""
            self.auto_approve = auto_approve

        def up(self, version: str, dry_run: bool = False) -> None:
            """Migrate database to specified version."""
            print(f"Migrating to {version} (dry_run={dry_run})")

        def down(self, steps: int = 1) -> None:
            """Rollback database migrations."""
            print(f"Rolling back {steps} steps")

    def query(self, sql: str, limit: int = 100) -> None:
        """Execute SQL query."""
        print(f"Executing: {sql} (limit={limit})")


if __name__ == '__main__':
    # Create CLI with custom configuration
    cli = FreyjaCLI(
        DatabaseCLI,
        title="Database Management CLI",
        theme=None,  # Use default theme
        alphabetize=True,
        completion=True,
        capture_output=True,  # Enable output capture
        capture_stdout=True,
    )

    # Run the CLI
    result = cli.run()

    # Access captured output
    if cli.output_capture:
        output = cli.get_captured_output('stdout')
        print(f"\nCaptured output: {output}")
```

**Usage**:
```bash
# Global options + command
python db_cli.py --verbose --connection-string postgres://localhost query "SELECT * FROM users" --limit 50

# Inner class commands (hierarchical structure)
python db_cli.py migrations up --auto-approve 2.0 --dry-run
python db_cli.py migrations down --steps 2

# Help at any level
python db_cli.py --help
python db_cli.py migrations --help
python db_cli.py query --help
```

---

## 🏗️ Architecture Components

The following classes are **internal implementation details** of Freyja's architecture. They are documented here for contributors and those interested in understanding Freyja's internals.

> **💡 Note**: For a visual overview of how these components interact, see the [Architecture Diagrams](architecture/README.md) and [How It Works](how-it-works.md) guide.

### CLI Layer

#### ExecutionCoordinator

**Location**: `freyja.cli.ExecutionCoordinator`

**Purpose**: Orchestrates the command discovery, parsing, and execution pipeline.

**Key Responsibilities**:
- Coordinate between discovery, parsing, and execution
- Manage output capture
- Handle completion requests
- Check NO_COLOR flag

**Usage**: Created automatically by `FreyjaCLI`, not intended for direct use.

#### ClassHandler

**Location**: `freyja.cli.ClassHandler`

**Purpose**: Manages class-based CLI creation and validation.

**Key Responsibilities**:
- Validate class structure (constructor defaults, etc.)
- Handle multi-class CLI scenarios
- Detect command collisions

**Usage**: Created automatically by `FreyjaCLI`, not intended for direct use.

#### SystemCommand

**Location**: `freyja.cli.system.SystemCommand`

**Purpose**: Base class for built-in system commands (completion, theme tuning).

**Key Responsibilities**:
- Provide system-level commands
- Completion installation and management
- Theme tuning interface

**Built-in Commands**:
- `completion install` - Install shell completion
- `completion uninstall` - Remove shell completion
- `theme-tuner` - Interactive theme tuning (if enabled)

### Command Layer

#### CommandDiscovery

**Location**: `freyja.command.CommandDiscovery`

**Purpose**: Discovers commands from classes and builds the command tree.

**Key Responsibilities**:
- Introspect classes and methods
- Extract type annotations and docstrings
- Build `CommandTree` structure
- Handle inner classes

**Process**:
1. Analyze target class(es)
2. Discover public methods
3. Extract metadata (types, defaults, docs)
4. Build hierarchical command structure

#### CommandExecutor

**Location**: `freyja.command.CommandExecutor`

**Purpose**: Executes discovered commands by invoking class methods.

**Key Responsibilities**:
- Instantiate classes with constructor args
- Prepare method arguments
- Invoke methods safely
- Handle return values and errors

**Error Handling**: Provides detailed error messages for debugging.

### Parser Layer

#### ArgumentParser

**Location**: `freyja.parser.ArgumentParser`

**Purpose**: Creates `argparse` parsers from the command tree.

**Key Responsibilities**:
- Generate argparse structure from `CommandTree`
- Configure argument types and defaults
- Set up help text from docstrings
- Add global, sub-global, and command arguments

#### ArgumentPreprocessor

**Location**: `freyja.parser.ArgumentPreprocessor`

**Purpose**: Enables flexible argument ordering.

**Key Responsibilities**:
- Identify command name in arguments
- Separate global, sub-global, and command-specific options
- Reorder arguments for argparse compatibility

**Example**: Allows users to mix options in any order:
```bash
# These all work identically:
app --global opt cmd --method opt
app cmd --method opt --global opt
app --method opt cmd --global opt
```

#### CommandParser

**Location**: `freyja.parser.CommandParser`

**Purpose**: Parses command-specific arguments.

**Key Responsibilities**:
- Create command-specific parsers
- Handle command argument validation
- Generate command help text

#### PositionalHandler

**Location**: `freyja.parser.PositionalHandler`

**Purpose**: Manages positional argument logic.

**Key Responsibilities**:
- Identify first parameter without default
- Convert to positional argument
- Handle positional in usage strings

**Rule**: First method parameter without a default value becomes positional.

#### OptionDiscovery

**Location**: `freyja.parser.OptionDiscovery`

**Purpose**: Discovers and converts method parameters to CLI options.

**Key Responsibilities**:
- Extract method parameters
- Convert snake_case to kebab-case
- Determine argument types from annotations
- Set defaults from parameter defaults

#### CommandPathResolver

**Location**: `freyja.parser.CommandPathResolver`

**Purpose**: Resolves command paths (flat vs hierarchical).

**Key Responsibilities**:
- Handle hierarchical commands (`group subgroup command`)
- Resolve hierarchical commands (multi-class scenarios)
- Map command strings to `CommandInfo`

### Shared Models

These data structures are used across all layers for consistency.

#### CommandTree

**Location**: `freyja.shared.CommandTree`

**Purpose**: Hierarchical representation of all commands.

**Structure**:
```python
{
    "commands": {
        "command-name": CommandInfo(...),
        "inner-class--method": CommandInfo(...)
    },
    "groups": {
        "group-name": {
            "commands": { ... },
            "subgroups": { ... }
        }
    }
}
```

**Methods**:
- `to_dict()` - Convert to dictionary
- `add_command()` - Add a command
- `add_group()` - Add a command group
- `get_command()` - Retrieve command by name

#### CommandInfo

**Location**: `freyja.shared.CommandInfo`

**Purpose**: Stores metadata about a single command.

**Attributes**:
- `name` - Command name
- `method` - Python method object
- `params` - List of parameters with types and defaults
- `docstring` - Help text
- `parent_class` - Class containing the method
- `inner_class` - Inner class if applicable

#### CommandGroup

**Location**: `freyja.shared.CommandGroup`

**Purpose**: Groups related commands together.

**Attributes**:
- `name` - Group name
- `description` - Group description
- `commands` - Dictionary of commands in group
- `subgroups` - Dictionary of subgroups

### Completion System

#### CompletionSystem

**Location**: `freyja.completion.CompletionSystem`

**Purpose**: Manages shell completion functionality.

**Supported Shells**:
- Bash
- Zsh
- Fish
- PowerShell

**Key Responsibilities**:
- Generate completion scripts
- Install/uninstall completion
- Detect shell type
- Handle completion requests

**Usage**: Accessed via system commands:
```bash
python app.py completion install --shell bash
python app.py completion uninstall --shell bash
```

#### ShellIntegration

**Location**: `freyja.completion.ShellIntegration`

**Purpose**: Shell-specific completion integration.

**Key Responsibilities**:
- Generate shell-specific completion code
- Install in appropriate shell config files
- Handle shell-specific completion protocols

### Utilities

#### TextUtil

**Location**: `freyja.utils.TextUtil`

**Purpose**: String manipulation and conversion.

**Key Methods**:
- `snake_to_kebab()` - Convert `snake_case` to `kebab-case`
- `kebab_to_snake()` - Convert `kebab-case` to `snake_case`
- `capitalize_first()` - Capitalize first letter
- `wrap_text()` - Wrap text to width

#### TypeUtil

**Location**: `freyja.utils.TypeUtil`

**Purpose**: Type annotation handling and conversion.

**Key Methods**:
- `get_arg_type()` - Convert Python type to argparse type
- `is_optional()` - Check if type is `Optional[T]`
- `extract_type()` - Extract type from `Optional`, `List`, etc.
- `validate_type()` - Validate value against type

**Supported Types**:
- `str`, `int`, `float`, `bool`
- `Path`, `pathlib.Path`
- `List[T]`, `Sequence[T]`
- `Optional[T]`
- `Enum` types

#### ConsoleUtil

**Location**: `freyja.utils.ConsoleUtil`

**Purpose**: Console output formatting and utilities.

**Key Methods**:
- `print_colored()` - Colored output
- `print_table()` - Formatted tables
- `check_no_color()` - Check NO_COLOR environment variable

#### InvokerUtil

**Location**: `freyja.utils.InvokerUtil`

**Purpose**: Safe method invocation.

**Key Methods**:
- `invoke_method()` - Safely invoke method with error handling
- `prepare_args()` - Prepare arguments from parsed namespace
- `handle_return()` - Handle method return values

#### ValidationUtil

**Location**: `freyja.utils.ValidationUtil`

**Purpose**: Argument validation.

**Key Methods**:
- `validate_required()` - Check required arguments
- `validate_type()` - Type validation
- `validate_enum()` - Enum value validation
- `validate_range()` - Numeric range validation

#### NestedDict

**Location**: `freyja.utils.NestedDict`

**Purpose**: Nested dictionary operations.

**Key Methods**:
- `get_nested()` - Get value from nested path
- `set_nested()` - Set value at nested path
- `flatten()` - Flatten nested structure
- `unflatten()` - Unflatten to nested structure

---

## 🛡️ Guards (modgud)

Freyja includes declarative guard clauses powered by the modgud library.

> **📦 Standalone Package**: Guard functionality is provided by [modgud](https://pypi.org/project/modgud/), included as a Git submodule. For standalone usage outside Freyja, install: `pip install modgud`

### Usage in Freyja

```python
from freyja.utils.guards import guarded, not_none, positive

class MyClass:
    @guarded(
        not_none("value", "Value cannot be None"),
        positive("count", "Count must be positive")
    )
    def process(self, value: str, count: int = 1) -> None:
        """Process value count times."""
        for _ in range(count):
            print(value)
```

### Available Guards

See [Guards Documentation](features/guards.md) for complete reference.

**Common Guards**:
- `not_none(param, message)` - Ensure parameter is not None
- `positive(param, message)` - Ensure number is positive
- `non_empty(param, message)` - Ensure string/list is not empty
- `range_check(param, min, max, message)` - Ensure value in range

**For More**: See the [modgud PyPI page](https://pypi.org/project/modgud/) for full documentation.

---

## 🎨 Themes

Freyja supports customizable themes for colored output.

### Default Themes

**Colorful Theme** (default):
```python
cli = FreyjaCLI(MyClass)  # Uses colorful theme
```

**Universal Theme** (high contrast):
```python
from freyja.theme import UniversalTheme

cli = FreyjaCLI(MyClass, theme=UniversalTheme())
```

**Custom Theme**:
```python
from freyja.theme import Theme, ColorScheme

custom_theme = Theme(
    primary=ColorScheme.BLUE,
    secondary=ColorScheme.GREEN,
    accent=ColorScheme.YELLOW
)

cli = FreyjaCLI(MyClass, theme=custom_theme)
```

### NO_COLOR Support

Freyja respects the `NO_COLOR` environment variable:

```bash
# Disable colors
NO_COLOR=1 python app.py command

# Or use flag
python app.py --no-color command
```

### Theme Tuning

Enable interactive theme tuning:

```python
cli = FreyjaCLI(MyClass, theme_tuner=True)
```

```bash
python app.py theme-tuner
# Interactive theme customization interface
```

See [Themes Documentation](features/themes.md) for complete reference.

---

## 📝 Type Support

Freyja automatically converts Python type annotations to appropriate argparse types.

### Supported Types

**Basic Types**:
```python
str       → type=str
int       → type=int
float     → type=float
bool      → action='store_true'
```

**Path Types**:
```python
Path              → type=Path
pathlib.Path      → type=Path
```

**Collection Types**:
```python
List[str]         → nargs='*', type=str
List[int]         → nargs='*', type=int
Sequence[str]     → nargs='*', type=str
```

**Optional Types**:
```python
Optional[str]     → type=str, default=None
str | None        → type=str, default=None (Python 3.10+)
```

**Enum Types**:
```python
from enum import Enum

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

# Automatically becomes choices
def set_status(self, status: Status): pass
# → --status {active,inactive}
```

### Type Validation

Freyja validates arguments against their type annotations:

```python
def process(self, count: int, factor: float):
    pass
```

```bash
# Valid
python app.py process --count 10 --factor 1.5

# Invalid - caught at parse time
python app.py process --count abc --factor xyz
# Error: argument --count: invalid int value: 'abc'
```

See [Type Annotations Documentation](features/type-annotations.md) for complete reference.

---

## 🎓 Next Steps

### For Users
- **[User Guide](user-guide/README.md)** - Build CLIs with Freyja
- **[Features](features/README.md)** - Explore all capabilities
- **[Examples](guides/examples.md)** - Real-world use cases

### For Advanced Users
- **[How It Works](how-it-works.md)** - Deep dive into internals
- **[Architecture](architecture/README.md)** - Visual diagrams
- **[Best Practices](guides/best-practices.md)** - Professional patterns

### For Contributors
- **[Contributing](development/contributing.md)** - Contribution guide
- **[Development](development/README.md)** - Development setup
- **[Submodules](development/submodules.md)** - Git submodule management

---

**Navigation**: [← Documentation Hub](README.md) | [How It Works →](how-it-works.md) | [Architecture →](architecture/README.md)
