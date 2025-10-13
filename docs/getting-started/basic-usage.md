![Freyja Thumb](https://github.com/terracoil/freyja/raw/main/docs/freyja-thumb.png)
# Basic Usage Guide

[← Back to Help](../README.md) | [🚀 Quick Start](quick-start.md) | [📦 Installation](installation.md)

# Table of Contents
- [Core Concepts](#core-concepts)
- [Type Annotation Requirements](#type-annotation-requirements)
- [New Features](#new-features)
- [Common Patterns](#common-patterns)
- [Choosing Between Modes](#choosing-between-modes)
- [Configuration Options](#configuration-options)
- [Built-in Features](#built-in-features)
- [Common Pitfalls](#common-pitfalls)
- [See Also](#see-also)

## Core Concepts

freyja uses Python's introspection capabilities to automatically generate command-line interfaces from your existing code. The key principle is **minimal configuration** - most behavior is inferred from your function signatures and docstrings.

### How It Works

1. **Function/Method Discovery**: freyja scans your module or class for public functions/methods
2. **Signature Analysis**: Parameter types, default values, and names are extracted using `inspect.signature()`
3. **CLI Generation**: Each function becomes a command with arguments derived from parameters
4. **Help Text Generation**: Docstrings are parsed to create descriptive help text

### Two Creation Patterns

```python
# Module-based: Functions become command tree
CLI.from_module(module, title="My Freyja")

# Class-based: Methods become command tree, instance maintains state
CLI.from_class(SomeClass, title="My App")
```

## Type Annotation Requirements

**Critical**: All CLI-exposed functions/methods **must** have type annotations for parameters.

### ✅ Required Annotations

```python
def good_function(name: str, count: int = 5, verbose: bool = False) -> None:
    """This function will work perfectly with freyja."""
    pass
```

### ❌ Missing Annotations

```python
def bad_function(name, count=5, verbose=False):  # No type hints
    """This will cause errors - freyja can't infer types."""
    pass
```

### Supported Types

| Python Type | CLI Behavior | Example Usage |
|-------------|-------------|---------------|
| `str` | `--name VALUE` | `--name "John"` |
| `int` | `--count 42` | `--count 100` |
| `float` | `--rate 3.14` | `--rate 2.5` |
| `bool` | `--verbose` (flag) | `--verbose` |
| `Enum` | `--level CHOICE` | `--level INFO` |
| `List[str]` | `--items A B C` | `--items file1 file2` |
| `Optional[str]` | `--name VALUE` (optional) | `--name "test"` |

## New Features

### 🎯 Flexible Argument Ordering

Freyja supports **flexible argument ordering**, allowing users to specify arguments in any order that feels natural:

```python
def deploy_service(service_name: str, environment: str = "staging", 
                  replicas: int = 1, wait: bool = False):
    """Deploy service to environment."""
    print(f"Deploying {service_name} to {environment} with {replicas} replicas")
```

**All of these work identically:**
```bash
# Traditional order
my-app deploy-service --service-name web-api --environment prod --replicas 3 --wait

# User's natural flow
my-app deploy-service --environment prod --wait --service-name web-api --replicas 3

# Options-first approach  
my-app deploy-service --replicas 3 --wait --service-name web-api --environment prod
```

**[📖 Complete Flexible Ordering Guide →](../features/flexible-ordering.md)**

### 📍 Positional Parameters

The **first parameter without a default value** automatically becomes positional, creating more natural commands:

```python
def backup_database(database_name: str, output_dir: str = "./backups", 
                   compress: bool = True):
    """Backup database - database_name is automatically positional."""
    pass
```

**Natural usage:**
```bash
# Clean, intuitive command structure
db-tool backup-database production_db --compress --output-dir /secure/backups

# Works with flexible ordering too
db-tool backup-database production_db --output-dir /backups --compress

# Traditional explicit format still works
db-tool backup-database --database-name production_db --compress
```

**Key Benefits:**
- **Zero Configuration** - Works by analyzing function signatures
- **Natural Commands** - `process file.txt` vs `process --file file.txt`
- **Type Safe** - Full validation on positional parameters
- **Backward Compatible** - Existing explicit format continues working

**[📖 Complete Positional Parameters Guide →](../features/positional-parameters.md)**

## Common Patterns

### 1. Simple Utility Functions

```python
from src import CLI
import sys


def convert_temperature(celsius: float, to_fahrenheit: bool = True) -> None:
  """Convert temperature between Celsius and Fahrenheit."""
  if to_fahrenheit:
    result = (celsius * 9 / 5) + 32
    print(f"{celsius}°C = {result}°F")
  else:
    result = (celsius - 32) * 5 / 9
    print(f"{celsius}°F = {result}°C")


def calculate_bmi(weight_kg: float, height_m: float) -> None:
  """Calculate Body Mass Index."""
  bmi = weight_kg / (height_m ** 2)
  print(f"BMI: {bmi:.2f}")


if __name__ == '__main__':
  cli = CLI.from_module(sys.modules[__name__], title="Health Calculator")
  cli.run()
```

Usage:
```bash
# Traditional explicit format
python health_calc.py convert-temperature --celsius 25 --to-fahrenheit
python health_calc.py calculate-bmi --weight-kg 70 --height-m 1.75

# With positional parameters (celsius and weight_kg become positional)
python health_calc.py convert-temperature 25 --to-fahrenheit
python health_calc.py calculate-bmi 70 --height-m 1.75

# With flexible ordering
python health_calc.py convert-temperature --to-fahrenheit 25  # celsius is positional
python health_calc.py calculate-bmi --height-m 1.75 70        # weight_kg is positional
```

### 2. Stateful Application Class

```python
from src import CLI
from typing import List
import json


class ConfigManager:
  """
      Configuration Management Freyja    
  Manage application configuration with persistent state.
  """

  def __init__(self):
    self.config = {}
    self.modified = False

  def set_value(self, key: str, value: str, config_type: str = "string") -> None:
    """Set a configuration value."""
    # Convert based on type
    if config_type == "int":
      converted_value = int(value)
    elif config_type == "bool":
      converted_value = value.lower() in ('true', '1', 'yes')
    else:
      converted_value = value

    self.config[key] = converted_value
    self.modified = True
    print(f"✅ Set {key} = {converted_value} ({config_type})")

  def get_value(self, key: str) -> None:
    """Get a configuration value."""
    if key in self.config:
      print(f"{key} = {self.config[key]}")
    else:
      print(f"❌ Key '{key}' not found")

  def list_all(self, format_type: str = "table") -> None:
    """List all configuration values."""
    if not self.config:
      print("No configuration values set")
      return

    if format_type == "json":
      print(json.dumps(self.config, indent=2))
    else:
      print("Configuration Values:")
      for key, value in self.config.items():
        print(f"  {key}: {value}")

  def save_config(self, file_path: str = "config.json") -> None:
    """Save configuration to file."""
    with open(file_path, 'w') as f:
      json.dump(self.config, f, indent=2)
    self.modified = False
    print(f"✅ Saved configuration to {file_path}")


if __name__ == '__main__':
  cli = CLI.from_class(ConfigManager, theme_name="colorful")
  cli.run()
```

Usage:
```bash
# Traditional explicit format
python config_mgr.py set-value --key database_host --value localhost
python config_mgr.py set-value --key port --value 5432 --config-type int
python config_mgr.py get-value --key database_host

# With positional parameters (key parameters become positional)
python config_mgr.py set-value database_host --value localhost
python config_mgr.py set-value port --value 5432 --config-type int
python config_mgr.py get-value database_host

# With flexible ordering
python config_mgr.py set-value --value localhost database_host
python config_mgr.py set-value --config-type int --value 5432 port
python config_mgr.py list-all --format-type json
```

### 3. File Processing Pipeline

```python
from src import CLI
from pathlib import Path
from typing import List
import sys


def process_text_files(
        input_dir: str,
        output_dir: str,
        extensions: List[str] = None,
        convert_to_uppercase: bool = False,
        add_line_numbers: bool = False,
        dry_run: bool = False
) -> None:
  """Process text files with various transformations."""
  if extensions is None:
    extensions = ['.txt', '.md']

  input_path = Path(input_dir)
  output_path = Path(output_dir)

  if not input_path.exists():
    print(f"❌ Input directory '{input_dir}' does not exist")
    return

  if not dry_run:
    output_path.mkdir(parents=True, exist_ok=True)

  # Find files
  files_to_process = []
  for ext in extensions:
    files_to_process.extend(input_path.glob(f"*{ext}"))

  print(f"Found {len(files_to_process)} files to process")

  for file_path in files_to_process:
    print(f"Processing: {file_path.name}")

    if dry_run:
      print(f"  Would write to: {output_path / file_path.name}")
      continue

    # Read and process
    with open(file_path, 'r', encoding='utf-8') as f:
      content = f.read()

    if convert_to_uppercase:
      content = content.upper()

    if add_line_numbers:
      lines = content.splitlines()
      content = '\n'.join(f"{i + 1:4d}: {line}" for i, line in enumerate(lines))

    # Write output
    output_file = output_path / file_path.name
    with open(output_file, 'w', encoding='utf-8') as f:
      f.write(content)

    print(f"  ✅ Written to: {output_file}")


if __name__ == '__main__':
  cli = CLI.from_module(sys.modules[__name__], title="Text File Processor")
  cli.run()
```

## Choosing Between Modes

### Decision Tree

```
Do you need persistent state between commands?
├── Yes → Use Class-based CLI
│   ├── Configuration that affects multiple commands
│   ├── Database connections or file handles
│   ├── User sessions or authentication state
│   └── Complex workflows with dependencies
└── No → Use Module-based CLI
    ├── Independent utility functions
    ├── Data transformation scripts
    ├── Simple command-line tools
    └── Functional programming style
```

### Module-based: When Each Command is Independent

```python
# Each function is completely independent
def encode_base64(text: str) -> None:
    """Encode text to base64."""
    import base64
    encoded = base64.b64encode(text.encode()).decode()
    print(f"Encoded: {encoded}")

def decode_base64(encoded_text: str) -> None:
    """Decode base64 text."""
    import base64
    decoded = base64.b64decode(encoded_text).decode()
    print(f"Decoded: {decoded}")

def hash_text(text: str, algorithm: str = "sha256") -> None:
    """Hash text using specified algorithm."""
    import hashlib
    hasher = getattr(hashlib, algorithm)()
    hasher.update(text.encode())
    print(f"{algorithm.upper()}: {hasher.hexdigest()}")
```

### Class-based: When You Need Shared State

```python
class DatabaseManager:
    """Database operations that share connection state."""
    
    def __init__(self):
        self.connection = None
        self.current_database = None
    
    def connect(self, host: str, database: str, port: int = 5432) -> None:
        """Connect to database (state persists for other command tree)."""
        # Connection logic here
        self.connection = f"mock_connection_{database}"
        self.current_database = database
        print(f"✅ Connected to {database}")
    
    def list_tables(self) -> None:
        """List tables (requires connection from previous command)."""
        if not self.connection:
            print("❌ Not connected. Use 'connect' command first.")
            return
        
        print(f"Tables in {self.current_database}: table1, table2, table3")
    
    def execute_query(self, sql: str) -> None:
        """Execute SQL query (uses established connection)."""
        if not self.connection:
            print("❌ Not connected. Use 'connect' command first.")
            return
        
        print(f"Executing: {sql}")
        print("✅ Query executed successfully")
```

## Configuration Options

### CLI Initialization Options

```python
# Module-based configuration
cli = CLI.from_module(
    module=sys.modules[__name__],
    title="Custom Freyja Title",           # Override auto-detected title
    function_opts={                     # Per-function configuration
        'function_name': {
            'description': 'Custom description',
            'hidden': False,            # Hide from Freyja listing
        }
    },
    theme_name="colorful",             # Built-in theme: "universal", "colorful"
    no_color=False,                    # Force disable colors
    completion=True                    # Enable shell completion
)

# Class-based configuration  
cli = CLI.from_class(
    cls=MyClass,                       # Class (not instance)
    title="Custom App Title",          # Override class docstring title
    function_opts={                    # Per-method configuration
        'method_name': {
            'description': 'Custom description'
        }
    },
    theme_name="universal",
    no_color=False,
    completion=True
)
```

### Function/Method Options

```python
function_opts = {
    'my_function': {
        'description': 'Override the docstring description',
        'hidden': False,                    # Hide from command listing
        'aliases': ['mf', 'my-func'],      # Alternative command names
    },
    'another_function': {
        'description': 'Another command description'
    }
}
```

## Built-in Features

### Automatic Help Generation

```bash
# Global help
python my_cli.py --help

# Command-specific help
python my_cli.py command-name --help
```

### Theme Support

```python
# Built-in themes
cli = CLI.from_module(module, theme_name="universal")  # Default
cli = CLI.from_module(module, theme_name="colorful")   # More colors

# Disable colors entirely
cli = CLI.from_module(module, no_color=True)
```

### Shell Completion

freyja includes built-in shell completion support for bash, zsh, and fish.

```bash
# Enable completion (run once)
python my_cli.py --install-completion

# Manual setup
python my_cli.py --show-completion >> ~/.bashrc
```

### Parameter Name Conversion

Function parameter names are automatically converted to CLI-friendly formats:

```python
def my_function(input_file: str, output_dir: str, max_count: int) -> None:
    pass

# Becomes: 
# --input-file, --output-dir, --max-count
```

## Common Pitfalls

### 1. Missing Type Annotations

```python
# ❌ This will fail
def bad_function(name, count=5):
    pass

# ✅ This works
def good_function(name: str, count: int = 5) -> None:
    pass
```

### 2. Incorrect Default Value Types

```python
# ❌ Type mismatch with default
def bad_function(count: int = "5") -> None:  # str default for int type
    pass

# ✅ Matching types
def good_function(count: int = 5) -> None:
    pass
```

### 3. Complex Types Without Import

```python
# ❌ Missing import
def bad_function(items: List[str]) -> None:  # List not imported
    pass

# ✅ Proper import
from typing import List

def good_function(items: List[str]) -> None:
    pass
```

### 4. Private Methods in Classes

```python
class MyApp:
    def public_command(self) -> None:
        """This becomes a Freyja command."""
        pass
    
    def _private_method(self) -> None:
        """This is ignored (starts with underscore)."""
        pass
    
    def __special_method__(self) -> None:
        """This is also ignored (dunder method)."""
        pass
```

### 5. Mutable Default Arguments

```python
# ❌ Dangerous mutable default
def bad_function(items: List[str] = []) -> None:
    pass

# ✅ Safe default handling
def good_function(items: List[str] = None) -> None:
    if items is None:
        items = []
```

## See Also

**🔥 New Features**
- **[Flexible Argument Ordering](../features/flexible-ordering.md)** - Mix options and arguments in any order
- **[Positional Parameters](../features/positional-parameters.md)** - Automatic positional argument detection

**📚 Complete Guides**  
- **[Class-based CLI Guide](../user-guide/class-cli.md)** - Complete class-based CLI guide
- **[Class-based CLI Guide](../user-guide/class-cli.md)** - Complete method-based CLI guide
- **[Type Annotations](../features/type-annotations.md)** - Detailed type system guide

**🛠️ Reference & Help**
- **[API Reference](../reference/README.md)** - Complete method reference
- **[Troubleshooting](../guides/troubleshooting.md)** - Common issues and solutions

---

**Navigation**: [← Help Hub](../README.md) | [Quick Start →](quick-start.md) | [Installation →](installation.md)  
**Examples**: [Class Example](../../examples/cls_example)
