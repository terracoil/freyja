# Class-based CLI Guide

[← Back to Help](../help.md) | [↑ Getting Started](../help.md#getting-started)

## Table of Contents
- [Overview](#overview)
- [Basic Usage](#basic-usage)
- [Class Design](#class-design)
- [Method Types](#method-types)
- [Instance Management](#instance-management)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [See Also](#see-also)

## Overview

Class-based CLI allows you to create command-line interfaces from class methods. This approach is ideal for applications that need to maintain state between commands or follow object-oriented design patterns.

### When to Use Class-based CLI

- **Stateful applications** that need to maintain data between commands
- **Complex tools** with shared configuration or resources
- **API clients** that manage connections or sessions
- **Database tools** that maintain connections
- **Object-oriented designs** with encapsulated behavior

## Basic Usage

### Simple Example

```python
# calculator_cli.py
from auto_cli import CLI

class Calculator:
    """A calculator that maintains result history."""
    
    def __init__(self):
        self.history = []
        self.last_result = 0
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = a + b
        self.last_result = result
        self.history.append(f"{a} + {b} = {result}")
        print(f"Result: {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        result = a - b
        self.last_result = result
        self.history.append(f"{a} - {b} = {result}")
        print(f"Result: {result}")
        return result
    
    def show_history(self):
        """Show calculation history."""
        if not self.history:
            print("No calculations yet")
        else:
            print("Calculation History:")
            for i, calc in enumerate(self.history, 1):
                print(f"  {i}. {calc}")
    
    def clear_history(self):
        """Clear calculation history."""
        self.history = []
        self.last_result = 0
        print("History cleared")

if __name__ == "__main__":
    cli = CLI.from_class(Calculator)
    cli.run()
```

### Running the CLI

```bash
# Show available commands
python calculator_cli.py --help

# Perform calculations
python calculator_cli.py add --a 10 --b 5
python calculator_cli.py subtract --a 20 --b 8

# View history
python calculator_cli.py show-history

# Clear history
python calculator_cli.py clear-history
```

## Class Design

### Constructor Parameters

Classes can accept initialization parameters:

```python
class DatabaseCLI:
    """Database management CLI."""
    
    def __init__(self, host: str = "localhost", port: int = 5432):
        self.host = host
        self.port = port
        self.connection = None
        print(f"Initialized with {host}:{port}")
    
    def connect(self):
        """Connect to the database."""
        print(f"Connecting to {self.host}:{self.port}...")
        # Actual connection logic here
        self.connection = f"Connection to {self.host}:{self.port}"
        print("Connected!")
    
    def status(self):
        """Show connection status."""
        if self.connection:
            print(f"Connected: {self.connection}")
        else:
            print("Not connected")

# Usage with custom initialization
if __name__ == "__main__":
    cli = CLI.from_class(
        DatabaseCLI,
        init_args={"host": "db.example.com", "port": 3306}
    )
    cli.run()
```

### Property Methods

Properties can be exposed as commands:

```python
class ConfigManager:
    """Configuration management CLI."""
    
    def __init__(self):
        self._debug = False
        self._timeout = 30
    
    @property
    def debug(self) -> bool:
        """Get debug mode status."""
        return self._debug
    
    @debug.setter
    def debug(self, value: bool):
        """Set debug mode."""
        self._debug = value
        print(f"Debug mode: {'ON' if value else 'OFF'}")
    
    def get_timeout(self) -> int:
        """Get current timeout value."""
        print(f"Current timeout: {self._timeout} seconds")
        return self._timeout
    
    def set_timeout(self, seconds: int):
        """Set timeout value."""
        if seconds <= 0:
            print("Error: Timeout must be positive")
            return
        self._timeout = seconds
        print(f"Timeout set to: {seconds} seconds")
```

## Method Types

### Instance Methods

Most common - have access to instance state via `self`:

```python
class FileProcessor:
    def __init__(self):
        self.processed_count = 0
    
    def process(self, filename: str):
        """Process a file (instance method)."""
        # Access instance state
        self.processed_count += 1
        print(f"Processing file #{self.processed_count}: {filename}")
```

### Class Methods

Useful for alternative constructors or class-level operations:

```python
class DataLoader:
    default_format = "json"
    
    @classmethod
    def set_default_format(cls, format: str):
        """Set default data format (class method)."""
        cls.default_format = format
        print(f"Default format set to: {format}")
    
    @classmethod
    def show_formats(cls):
        """Show supported formats."""
        formats = ["json", "csv", "xml", "yaml"]
        print(f"Supported formats: {', '.join(formats)}")
        print(f"Default: {cls.default_format}")
```

### Static Methods

For utility functions that don't need instance or class access:

```python
class MathUtils:
    @staticmethod
    def fibonacci(n: int):
        """Calculate Fibonacci number (static method)."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        print(f"Fibonacci({n}) = {b}")
        return b
    
    @staticmethod
    def is_prime(num: int) -> bool:
        """Check if number is prime."""
        if num < 2:
            result = False
        else:
            result = all(num % i != 0 for i in range(2, int(num**0.5) + 1))
        print(f"{num} is {'prime' if result else 'not prime'}")
        return result
```

## Instance Management

### Singleton Pattern

Create a single instance for all commands:

```python
class AppConfig:
    """Application configuration manager."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.settings = {}
            self.initialized = True
    
    def set(self, key: str, value: str):
        """Set a configuration value."""
        self.settings[key] = value
        print(f"Set {key} = {value}")
    
    def get(self, key: str):
        """Get a configuration value."""
        value = self.settings.get(key, "Not set")
        print(f"{key} = {value}")
        return value
```

### Resource Management

Proper cleanup with context managers:

```python
class ResourceManager:
    """Manage external resources."""
    
    def __init__(self):
        self.resources = []
    
    def __enter__(self):
        print("Acquiring resources...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Releasing resources...")
        for resource in self.resources:
            # Clean up resources
            pass
    
    def open_file(self, filename: str):
        """Open a file resource."""
        print(f"Opening {filename}")
        self.resources.append(filename)
    
    def process_all(self):
        """Process all open resources."""
        for resource in self.resources:
            print(f"Processing {resource}")
```

## Advanced Features

### Method Filtering

Control which methods are exposed:

```python
class AdvancedCLI:
    """CLI with filtered methods."""
    
    def public_command(self):
        """This will be exposed."""
        print("Public command executed")
    
    def _private_method(self):
        """This won't be exposed (starts with _)."""
        pass
    
    def __special_method__(self):
        """This won't be exposed (dunder method)."""
        pass
    
    def internal_helper(self):
        """This can be explicitly excluded."""
        pass

if __name__ == "__main__":
    cli = CLI.from_class(
        AdvancedCLI,
        exclude_methods=['internal_helper']
    )
    cli.run()
```

### Custom Method Options

```python
class CustomCLI:
    """CLI with custom method options."""
    
    def process_data(self, input_file: str, output_file: str, format: str = "json"):
        """Process data file."""
        print(f"Processing {input_file} -> {output_file} (format: {format})")

if __name__ == "__main__":
    method_opts = {
        'process_data': {
            'description': 'Process data with custom options',
            'args': {
                'input_file': {'help': 'Input data file path'},
                'output_file': {'help': 'Output file path'},
                'format': {
                    'help': 'Output format',
                    'choices': ['json', 'csv', 'xml']
                }
            }
        }
    }
    
    cli = CLI.from_class(
        CustomCLI,
        method_opts=method_opts,
        title="Custom Data Processor"
    )
    cli.run()
```

### Inheritance Support

```python
class BaseCLI:
    """Base CLI with common commands."""
    
    def version(self):
        """Show version information."""
        print("Version 1.0.0")
    
    def help_info(self):
        """Show help information."""
        print("This is the help information")

class ExtendedCLI(BaseCLI):
    """Extended CLI with additional commands."""
    
    def status(self):
        """Show current status."""
        print("Status: OK")
    
    def process(self, item: str):
        """Process an item."""
        print(f"Processing: {item}")

# Both base and extended methods will be available
if __name__ == "__main__":
    cli = CLI.from_class(ExtendedCLI)
    cli.run()
```

## Best Practices

### 1. Meaningful Class Names

```python
# ✓ Good - descriptive name
class DatabaseMigrationTool:
    pass

# ✗ Avoid - vague name
class Tool:
    pass
```

### 2. Initialize State in __init__

```python
class StatefulCLI:
    def __init__(self):
        # Initialize all state in constructor
        self.cache = {}
        self.config = self.load_config()
        self.session = None
    
    def load_config(self):
        """Load configuration."""
        return {"debug": False, "timeout": 30}
```

### 3. Validate State Before Operations

```python
class SessionManager:
    def __init__(self):
        self.session = None
    
    def connect(self, url: str):
        """Connect to service."""
        self.session = f"Session to {url}"
        print(f"Connected to {url}")
    
    def query(self, params: str):
        """Query the service."""
        if not self.session:
            print("Error: Not connected. Run 'connect' first.")
            return
        
        print(f"Querying with: {params}")
        # Perform query
```

### 4. Clean Method Names

```python
class DataProcessor:
    # ✓ Good - action verbs for commands
    def import_data(self, source: str):
        pass
    
    def export_data(self, destination: str):
        pass
    
    def validate_schema(self):
        pass
    
    # ✗ Avoid - noun-only names
    def data(self):
        pass
```

### 5. Group Related Methods

```python
class OrganizedCLI:
    """Well-organized CLI with grouped methods."""
    
    # File operations
    def file_create(self, name: str):
        """Create a new file."""
        pass
    
    def file_delete(self, name: str):
        """Delete a file."""
        pass
    
    def file_list(self):
        """List all files."""
        pass
    
    # Data operations
    def data_import(self, source: str):
        """Import data."""
        pass
    
    def data_export(self, dest: str):
        """Export data."""
        pass
```

## See Also

- [Module-based CLI](module-cli.md) - Alternative functional approach
- [Type Annotations](../features/type-annotations.md) - Supported types
- [Examples](../guides/examples.md) - More class-based examples
- [Best Practices](../guides/best-practices.md) - Design patterns
- [API Reference](../reference/api.md) - Complete API docs

---
**Navigation**: [← Module-based CLI](module-cli.md) | [Examples →](../guides/examples.md)