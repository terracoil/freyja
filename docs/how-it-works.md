# ⚙️ How Freyja Works
<img src="https://github.com/terracoil/freyja/raw/main/docs/freyja-github.jpg" alt="Freyja" title="Freyja" width="300"/>

## 📍 Navigation
**You are here**: Documentation Hub > How It Works

**Parents**:
- [🏠 Main README](../README.md) - Project overview and quick start
- [📚 Documentation Hub](README.md) - Complete documentation index

**Related**:
- [📖 API Reference](api-docs.md) - Complete API documentation
- [👤 User Guide](user-guide/README.md) - Building CLIs with Freyja
- [✨ Features](features/README.md) - Detailed feature documentation

---

## 📑 Table of Contents
- [🌟 Overview](#-overview)
- [⚡ The Magic of Zero Configuration](#-the-magic-of-zero-configuration)
- [🔄 The Transformation Pipeline](#-the-transformation-pipeline)
- [🏗️ Architecture Layers](#️-architecture-layers)
- [📊 Data Flow](#-data-flow)
- [🎯 Key Design Decisions](#-key-design-decisions)
- [🔍 Under the Hood: A Real Example](#-under-the-hood-a-real-example)
- [💡 Why It's Fast](#-why-its-fast)
- [🚀 What Makes Freyja Different](#-what-makes-freyja-different)

---

## 🌟 Overview

Freyja transforms your Python classes into fully-functional command-line interfaces through **pure introspection**. No decorators, no configuration files, no complex setup. Just type annotations and docstrings.

**The Core Principle**: Your class methods define the CLI structure, and Python's type system provides all the validation and help text needed.

```python
# This is all you need
class MyApp:
    def process(self, file: str, verbose: bool = False) -> None:
        """Process a file."""
        pass

cli = FreyjaCLI(MyApp)
cli.run()  # ← This creates a complete CLI!
```

## ⚡ The Magic of Zero Configuration

### How Does It Work Without Configuration?

Freyja leverages **three powerful Python features**:

1. **Type Annotations** → Automatic argument types and validation
2. **Docstrings** → Automatic help text and documentation
3. **Default Values** → Optional vs required arguments

```python
def process_file(
    self,
    input_file: str,              # → Required positional argument
    output_format: str = "json",  # → Optional --output-format flag
    verbose: bool = False         # → Optional --verbose flag
) -> None:
    """Process a file and convert format.

    This docstring becomes the help text!
    """
    pass
```

**Result**:
```bash
python app.py process-file --help
# Automatically generates:
#   usage: app.py process-file <input_file> [--output-format FORMAT] [--verbose]
#
#   Process a file and convert format.
#   This docstring becomes the help text!
#
#   positional arguments:
#     input_file            Required input file
#
#   options:
#     --output-format FORMAT  Output format (default: json)
#     --verbose              Enable verbose mode
```

### Zero Dependencies = Pure Speed

**No external libraries means**:
- ⚡ Instant imports (no dependency resolution)
- 🎯 No version conflicts
- 📦 Tiny package size
- 🚀 Lightning-fast CLI startup

## 🔄 The Transformation Pipeline

Freyja's transformation happens in **four distinct phases**:

### Phase 1: Class Introspection
**What happens**: `FreyjaCLI.__init__()` analyzes your class

```python
cli = FreyjaCLI(MyClass)  # ← Introspection starts here
```

**Process**:
1. ✅ Validates class structure (all constructor params have defaults)
2. 🔍 Discovers all public methods (non-underscore methods)
3. 🏗️ Identifies inner classes for command grouping
4. 📝 Extracts docstrings for help text
5. 🎯 Analyzes type annotations for validation

**Key Classes Involved**:
- `FreyjaCLI` - Entry point
- `ClassHandler` - Manages class-based CLI creation
- `CommandDiscovery` - Discovers and analyzes methods

### Phase 2: Command Discovery
**What happens**: Build the command tree structure

<img src="architecture/diagram.dependency.package.pdf" alt="Package Dependencies" width="600"/>

**Process**:
1. 🌳 Create `CommandTree` - hierarchical command structure
2. 📋 Generate `CommandInfo` for each method - stores metadata
3. 🏷️ Convert method names to CLI commands (snake_case → kebab-case)
4. 🎨 Organize commands by pattern:
   - **Direct methods** → flat commands (`my-method`)
   - **Inner classes** → grouped commands (`inner-class--method`)

**Example Transformation**:
```python
class ProjectManager:
    class Database:
        def migrate(self, version: str): pass
        def backup(self, path: str): pass

# Becomes:
# - database migrate <version>
# - database backup <path>
```

**Key Classes Involved**:
- `CommandDiscovery` - Discovers all commands
- `CommandTree` - Stores hierarchical structure
- `CommandInfo` - Stores method metadata
- `CommandGroup` - Groups related commands

### Phase 3: Argument Parser Generation
**What happens**: Convert command tree to argparse structure

**Process**:
1. 🎯 Create main ArgumentParser
2. 🔧 Add global arguments (from constructor)
3. 📦 Add sub-global arguments (from inner class constructors)
4. ⚙️ Add command-specific arguments (from method parameters)
5. 📍 Configure positional arguments (first non-default param)
6. ✅ Set up type validation from annotations

**Flexible Ordering with ArgumentPreprocessor**:
```python
# All of these work identically!
python app.py --global-opt value command --method-opt value
python app.py command --method-opt value --global-opt value
python app.py --method-opt value --global-opt value command
```

**How?** The `ArgumentPreprocessor` reorders arguments before parsing:
1. Identifies command name in arguments
2. Separates global, sub-global, and command-specific options
3. Reorders to match argparse expectations
4. Passes to ArgumentParser

**Key Classes Involved**:
- `ArgumentParser` - Creates argparse structure
- `ArgumentPreprocessor` - Enables flexible ordering
- `CommandParser` - Parses command-specific arguments
- `PositionalHandler` - Manages positional arguments
- `OptionDiscovery` - Discovers and converts method options

### Phase 4: Command Execution
**What happens**: Execute the user's command

<img src="architecture/diagram.dependency.class.pdf" alt="Class Dependencies" width="800"/>

**Process**:
1. 🎯 Parse command-line arguments
2. 🔍 Resolve which method to call
3. 🏗️ Instantiate class with constructor arguments
4. 🔧 Instantiate inner class if needed
5. ⚙️ Prepare method arguments
6. 🚀 Invoke the method
7. ✅ Handle return value and errors

**Example Flow**:
```python
# User runs:
python app.py --config prod.json database migrate --version 2.0

# Execution flow:
1. Parse: config="prod.json", command="database migrate", version="2.0"
2. Instantiate: app = MyApp(config="prod.json")
3. Instantiate inner: db = app.Database()
4. Call: db.migrate(version="2.0")
```

**Key Classes Involved**:
- `ExecutionCoordinator` - Orchestrates execution
- `CommandExecutor` - Executes the command
- `InvokerUtil` - Invokes methods safely
- `ValidationUtil` - Validates arguments

## 🏗️ Architecture Layers

Freyja follows a **clean layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────┐
│    FreyjaCLI (Entry Point)          │
│    - Main API surface                │
│    - Initialization & validation     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Coordination Layer                  │
│  - ExecutionCoordinator              │
│  - ClassHandler                      │
│  - Orchestrates pipeline             │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼─────┐   ┌─────▼────────┐
│ Discovery   │   │   Parsing    │
│ Layer       │   │   Layer      │
│             │   │              │
│ - CommandDi │   │ - ArgumentPr │
│   scovery   │   │   eprocessor │
│ - CommandEx │   │ - ArgumentPa │
│   ecutor    │   │   rser       │
│             │   │ - CommandPar │
│             │   │   ser        │
└──────┬──────┘   └─────┬────────┘
       │                │
       └───────┬────────┘
               │
┌──────────────▼──────────────────────┐
│   Shared Data Models                 │
│   - CommandTree                      │
│   - CommandInfo                      │
│   - CommandGroup                     │
│   (Used by all layers)               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Utilities Layer                    │
│   - TextUtil (string conversions)   │
│   - TypeUtil (type handling)         │
│   - InvokerUtil (method calls)       │
│   - ValidationUtil (validation)      │
│   - ConsoleUtil (output)             │
└──────────────────────────────────────┘
```

### Layer Responsibilities

**Entry Layer (`FreyjaCLI`)**:
- Public API surface
- Initial validation
- Pipeline initialization

**Coordination Layer**:
- `ExecutionCoordinator` - Manages flow between layers
- `ClassHandler` - Handles class-based CLI setup
- `SystemCommand` - Built-in system commands

**Discovery Layer**:
- `CommandDiscovery` - Analyzes classes and methods
- `CommandExecutor` - Executes discovered commands
- Builds the command tree

**Parsing Layer**:
- `ArgumentPreprocessor` - Flexible argument ordering
- `ArgumentParser` - Creates argparse structure
- `CommandParser` - Command-specific parsing
- `PositionalHandler` - Positional argument logic
- `OptionDiscovery` - Method option discovery

**Shared Models Layer**:
- `CommandTree` - Hierarchical command structure
- `CommandInfo` - Method metadata
- `CommandGroup` - Command grouping
- Used across all layers for consistency

**Utilities Layer**:
- Cross-cutting concerns
- Reusable functionality
- Type conversions and validations

## 📊 Data Flow

Here's what happens when you run a Freyja CLI:

```
 User Types Command
       │
       ▼
 ┌─────────────┐
 │  FreyjaCLI  │ ← Entry point
 │   .run()    │
 └──────┬──────┘
        │
        ▼
 ┌──────────────────┐
 │ ExecutionCoord.  │ ← Orchestration
 └──────┬───────────┘
        │
        ├─────────────────────┐
        │                     │
        ▼                     ▼
 ┌─────────────┐      ┌──────────────┐
 │  Command    │      │  Argument    │
 │  Discovery  │      │  Preprocessor│ ← Reorder args
 └──────┬──────┘      └──────┬───────┘
        │                    │
        ▼                    ▼
 ┌─────────────┐      ┌──────────────┐
 │ CommandTree │      │  Argument    │
 │  (built)    │      │  Parser      │ ← Parse args
 └──────┬──────┘      └──────┬───────┘
        │                    │
        └─────────┬──────────┘
                  │
                  ▼
          ┌───────────────┐
          │   Command     │
          │   Executor    │ ← Execute
          └───────┬───────┘
                  │
                  ▼
          ┌───────────────┐
          │  Your Method  │ ← User code runs!
          │    Runs       │
          └───────────────┘
```

## 🎯 Key Design Decisions

### Why Class-Based Only?

**Decision**: Freyja only supports class-based CLIs, not module/function-based.

**Rationale**:
- ✅ **State Management**: Classes naturally handle state (config, connections, etc.)
- ✅ **Logical Grouping**: Inner classes provide excellent command organization
- ✅ **Consistent API**: Single, clear pattern to learn
- ✅ **Constructor Args**: Global options from `__init__` parameters
- ✅ **Better for Complex Apps**: Enterprise tools need stateful operations

**Example**:
```python
class DatabaseCLI:
    def __init__(self, connection_string: str = "..."):
        self.connection = connect(connection_string)  # ← Stateful!

    def query(self, sql: str):
        return self.connection.execute(sql)  # ← Uses state
```

### Why Zero Dependencies?

**Decision**: Use only Python standard library.

**Rationale**:
- ⚡ **Fast Imports**: No dependency resolution overhead
- 🎯 **No Conflicts**: Won't conflict with user's dependencies
- 📦 **Tiny Size**: Minimal package footprint
- 🚀 **Easy Installation**: `pip install freyja` just works
- ✅ **Reliable**: No breaking changes from external packages

### Why Type Annotations?

**Decision**: Require type annotations on all method parameters.

**Rationale**:
- ✅ **Automatic Validation**: Types → argparse types automatically
- 🎯 **Better Help Text**: Types appear in usage docs
- 📝 **Self-Documenting**: Code describes its own interface
- ⚡ **No Extra Work**: Modern Python best practice anyway
- 🔒 **Type Safety**: Catch errors before runtime

### Why Constructor Defaults Required?

**Decision**: All constructor parameters must have default values.

**Rationale**:
- ✅ **Optional Global Flags**: Constructor params become optional `--flags`
- 🎯 **Usability**: Users can run commands without specifying every config
- 🚫 **Error Prevention**: Required constructor params break CLI flow
- ⚡ **Flexibility**: Defaults provide sensible behavior out of box

## 🔍 Under the Hood: A Real Example

Let's trace exactly what happens with a real example:

### The Code
```python
# app.py
from freyja import FreyjaCLI

class DataProcessor:
    def __init__(self, config: str = "config.json", debug: bool = False):
        """Initialize with configuration."""
        self.config = config
        self.debug = debug

    class Database:
        def __init__(self, timeout: int = 30):
            """Database configuration."""
            self.timeout = timeout

        def migrate(self, version: str, dry_run: bool = False) -> None:
            """Run database migration."""
            print(f"Migrating to {version} (dry_run={dry_run})")

if __name__ == '__main__':
    cli = FreyjaCLI(DataProcessor)
    cli.run()
```

### The Command
```bash
python app.py --debug database migrate --timeout 60 2.0 --dry-run
```

### Step-by-Step Execution

#### 1️⃣ **Initialization** (`FreyjaCLI.__init__`)
```python
cli = FreyjaCLI(DataProcessor)
```
- Validates `DataProcessor` class structure
- Checks constructor params have defaults ✅
- Creates `ClassHandler` for class-based CLI
- Passes to `CommandDiscovery`

#### 2️⃣ **Discovery** (`CommandDiscovery`)
- Scans `DataProcessor`:
  - Constructor: `config`, `debug` → Global arguments
  - Inner class `Database` found
- Scans `Database`:
  - Constructor: `timeout` → Sub-global argument
  - Method: `migrate` → Command
- Creates `CommandTree`:
  ```
  database
    migrate
      Global: --config, --debug
      Sub-global: --timeout
      Command: <version>, --dry-run
  ```
- Creates `CommandInfo` for `migrate`:
  ```python
  CommandInfo(
      name="database migrate",
      method=Database.migrate,
      params=[
          ("version", str, NO_DEFAULT),      # Positional
          ("dry_run", bool, False)            # Optional
      ],
      docstring="Run database migration."
  )
  ```

#### 3️⃣ **Parser Generation** (`ArgumentParser`)
- Creates argparse structure:
  ```python
  parser = argparse.ArgumentParser()
  parser.add_argument('--config', default='config.json')
  parser.add_argument('--debug', action='store_true')

  subparser = parser.add_subparsers()
  db_parser = subparser.add_parser('database')
  db_subparser = db_parser.add_subparsers()
  migrate_parser = db_subparser.add_parser('migrate')
  migrate_parser.add_argument('--timeout', type=int, default=30)
  migrate_parser.add_argument('version', type=str)  # Positional!
  migrate_parser.add_argument('--dry-run', action='store_true')
  ```

#### 4️⃣ **Argument Preprocessing** (`ArgumentPreprocessor`)
```python
# Input args:
["--debug", "database", "migrate", "--timeout", "60", "2.0", "--dry-run"]

# After preprocessing (reordered for argparse):
["--debug", "database", "migrate", "2.0", "--timeout", "60", "--dry-run"]
#  ^^^^^^  ^^^^^^^^^^  ^^^^^^^^^  ^^^  ^^^^^^^^^^  ^^  ^^^^^^^^^
#  Global  Group       Command    Pos  Sub-global  Val Command-opt
```

#### 5️⃣ **Parsing** (`ArgumentParser.parse_args()`)
```python
Namespace(
    config='config.json',  # Default
    debug=True,            # From --debug
    command='database migrate',
    timeout=60,            # From --timeout 60
    version='2.0',         # Positional
    dry_run=True           # From --dry-run
)
```

#### 6️⃣ **Execution** (`CommandExecutor`)
```python
# 1. Instantiate main class with global args
processor = DataProcessor(config='config.json', debug=True)

# 2. Instantiate inner class with sub-global args
db = processor.Database(timeout=60)

# 3. Call method with command args
db.migrate(version='2.0', dry_run=True)
```

#### 7️⃣ **Output**
```
Migrating to 2.0 (dry_run=True)
```

## 💡 Why It's Fast

Freyja achieves exceptional performance through:

### 1. Zero Dependencies
```python
# Freyja import time: ~10ms
import freyja  # ← Only stdlib imports

# Compare to typical CLI frameworks: ~100-500ms
import click   # ← Many dependencies
import typer   # ← Even more dependencies
```

### 2. Introspection at Startup Only
```python
cli = FreyjaCLI(MyClass)  # ← Introspection happens ONCE here
cli.run()                  # ← No introspection, just execution
```

### 3. Direct Method Calls
```python
# Freyja: Direct call
method(*args, **kwargs)

# No intermediate layers
# No decorators to unwrap
# No complex middleware
```

### 4. Minimal Object Creation
- CommandTree created once
- Argument parser created once
- Class instantiated once
- Method called directly

## 🚀 What Makes Freyja Different

### Comparison with Other Frameworks

| Feature | Freyja | Click | Typer | Argparse |
|---------|--------|-------|-------|----------|
| **Dependencies** | 0 | Many | Many | 0 |
| **Configuration** | None | Decorators | Decorators | Manual |
| **Learning Curve** | Minutes | Hours | Hours | Days |
| **Type Safety** | Built-in | Optional | Built-in | Manual |
| **Stateful Apps** | Natural | Complex | Medium | Manual |
| **Inner Classes** | Native | No | No | Manual |
| **Auto Help** | Yes | Yes | Yes | Manual |
| **Flexible Ordering** | Yes | No | No | No |
| **Positional Auto** | Yes | No | Manual | Manual |

### Unique Freyja Features

✨ **True Zero Configuration**
```python
# Freyja: Just write classes
class App:
    def cmd(self, arg: str): pass

cli = FreyjaCLI(App).run()
```

✨ **Natural Inner Class Pattern**
```python
# Organizes commands naturally
class App:
    class Database:
        def migrate(self): pass  # → database migrate
```

✨ **Flexible Argument Ordering**
```bash
# All work identically
app cmd --opt val --global g
app --global g cmd --opt val
app --opt val cmd --global g
```

✨ **Automatic Positional Arguments**
```python
def process(self, file: str, opts: str = ""):
    pass
# → process <file> [--opts OPTS]
# First param without default becomes positional!
```

---

## 🎓 Next Steps

Now that you understand how Freyja works internally:

### 📖 Deep Dive into Components
- **[API Reference](api-docs.md)** - Complete technical documentation

### 🛠️ Build Something
- **[User Guide](user-guide/README.md)** - Comprehensive building guide
- **[Examples](guides/examples.md)** - Real-world applications
- **[Best Practices](guides/best-practices.md)** - Professional patterns

### 🚀 Advanced Topics
- **[Type Annotations](features/type-annotations.md)** - Supported types and validation
- **[Shell Completion](features/shell-completion.md)** - Tab completion setup
- **[Error Handling](features/error-handling.md)** - Robust error management

---

**Navigation**: [← Documentation Hub](README.md) | [API Reference →](api-docs.md)
