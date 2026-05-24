![Freyja](https://github.com/terracoil/freyja/raw/main/docs/freyja.png)

# ❓ Frequently Asked Questions (FAQ)

[← Back to Documentation Hub](README.md) | [🔧 Basic Usage](getting-started/basic-usage.md)

# Table of Contents
- [General Questions](#general-questions)
- [Comparison with Other Tools](#comparison-with-other-tools)
- [Technical Questions](#technical-questions)
- [Usage and Best Practices](#usage-and-best-practices)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## General Questions

### What is freyja?

Freyja is a Python library that automatically generates complete command-line interfaces from your existing Python class methods using introspection and type annotations. It requires minimal configuration — just add type hints to your methods and you get a fully-featured CLI.

### How is it different from writing CLI code manually?

Traditional CLI development requires:
- Manual argument parser setup
- Type validation code
- Help text generation
- Error handling
- Command organization

freyja handles all of this automatically by analyzing your function signatures and docstrings.

```python
# Traditional approach (with argparse)
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--name', type=str, required=True, help='Name to greet')
parser.add_argument('--excited', action='store_true', help='Use excited greeting')
args = parser.parse_args()
greet(args.name, args.excited)

# freyja approach
from freyja import FreyjaCLI

class Greeter:
    """Simple greeting application."""

    def __init__(self):
        pass

    def greet(self, name: str, excited: bool = False) -> None:
        """Greet someone by name."""
        pass

cli = FreyjaCLI(Greeter)
cli.run()
```

### What are the benefits of class-based CLIs?

**Class-based CLIs offer significant advantages:**
- ✅ **State Management**: Persistent application state across commands
- ✅ **Configuration**: Easy global and sub-global argument handling
- ✅ **Organization**: Clean separation of concerns with inner classes
- ✅ **Resource Management**: Database connections, file handles, API clients
- ✅ **Complex Workflows**: Multi-step operations with dependencies
- ✅ **Code Reusability**: Methods can be called programmatically
- ✅ **Testing**: Easy to unit test individual methods

### Does freyja have any dependencies?

No! freyja uses only Python standard library modules. It has zero runtime dependencies, making it lightweight and easy to install anywhere.

## Comparison with Other Tools

### How does it compare to Click?

| Feature | freyja | Click |
|---------|-------------|--------|
| **Setup** | Automatic from type hints | Manual decorators |
| **Learning curve** | Minimal (just type hints) | Medium (decorator syntax) |
| **Code style** | Use existing functions | Decorator-wrapped functions |
| **Dependencies** | Zero | Click package |
| **Flexibility** | Good for standard CLIs | Highly customizable |

```python
# freyja: Use class methods
class FileTools:
    def __init__(self):
        pass

    def process_file(self, input_path: str, format: str = "json") -> None:
        """Process a file."""
        pass

# Click: Requires decorators
import click
@click.command()
@click.option('--input-path', required=True, help='Input file path')
@click.option('--format', default='json', help='Output format')
def process_file(input_path, format):
    """Process a file."""
    pass
```

### How does it compare to Typer?

| Feature | freyja | Typer |
|---------|-------------|--------|
| **Type hints** | Required | Optional but recommended |
| **Setup** | Automatic class introspection | Manual function registration |
| **Class support** | First-class (the only mode) | Limited |
| **Dependencies** | None | Typer + Click |
| **State management** | Excellent (class-based) | Manual |

```python
# freyja: Automatic introspection of a class
class MyTools:
    def __init__(self):
        pass

    def cmd1(self, name: str) -> None: pass
    def cmd2(self, count: int) -> None: pass

cli = FreyjaCLI(MyTools)  # Methods become commands automatically

# Typer: Manual registration
import typer
app = typer.Typer()
@app.command()
def cmd1(name: str): pass
@app.command()
def cmd2(count: int): pass
```

### How does it compare to argparse?

freyja is built on top of argparse but eliminates the boilerplate:

| Feature | freyja | Raw argparse |
|---------|-------------|--------------|
| **Code amount** | ~5 lines | ~20+ lines |
| **Type validation** | Automatic | Manual |
| **Help generation** | From docstrings | Manual strings |
| **Command Groups** | Automatic | Complex setup |
| **Error handling** | Built-in | Manual |

### When should I use other CLI libraries instead?

**Use Click when:**
- You need highly customized CLI behavior
- You want extensive plugin systems
- You need complex parameter validation

**Use Typer when:**
- You want Click-like features with type hints
- You need FastAPI integration
- You don't mind adding dependencies

**Use raw argparse when:**
- You need absolute control over argument parsing
- You're working with legacy code
- You want to minimize any abstractions

## Technical Questions

### Can I use async functions?

Currently, freyja supports synchronous methods only. For async work, wrap it in a sync method:

```python
import asyncio
from freyja import FreyjaCLI


class AsyncProcessor:
    """Async-friendly processing wrapper."""

    def __init__(self):
        pass

    async def _async_process(self, data: str) -> None:
        """Async worker."""
        await some_async_operation(data)

    def process(self, data: str) -> None:
        """Sync wrapper for async processing."""
        asyncio.run(self._async_process(data))


cli = FreyjaCLI(AsyncProcessor)
```

### How do I handle file uploads or binary data?

Pass file paths as strings and handle file operations inside your functions:

```python
def process_image(image_path: str, output_path: str, quality: int = 80) -> None:
    """Process image file."""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Process image_data
        processed_data = process_image_data(image_data, quality)
        
        with open(output_path, 'wb') as f:
            f.write(processed_data)
            
    except FileNotFoundError:
        print(f"❌ Image file not found: {image_path}")
    except PermissionError:
        print(f"❌ Permission denied: {output_path}")

# Usage: python script.py process-image --image-path photo.jpg --output-path result.jpg
```

### Can I use complex data structures as parameters?

For complex data, use JSON strings or configuration files:

```python
import json
from typing import Dict, Any

def configure_app(config_json: str) -> None:
    """Configure app using JSON string."""
    try:
        config = json.loads(config_json)
        print(f"Configuration: {config}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")

def load_config_file(config_file: str) -> None:
    """Load configuration from file."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"Loaded config: {config}")
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_file}")

# Usage:
# python script.py configure-app --config-json '{"debug": true, "port": 8080}'
# python script.py load-config-file --config-file settings.json
```

### How do I add custom type validation?

Perform validation inside your functions:

```python
def set_port(port: int) -> None:
    """Set server port (1-65535)."""
    if not (1 <= port <= 65535):
        print(f"❌ Port must be between 1-65535, got: {port}")
        return
    
    print(f"✅ Port set to: {port}")

def set_email(email: str) -> None:
    """Set email address."""
    if '@' not in email or '.' not in email:
        print(f"❌ Invalid email format: {email}")
        return
    
    print(f"✅ Email set to: {email}")
```

### Can I use freyja with existing Click/Typer code?

You can gradually migrate or use them side-by-side via separate entry points:

```python
# Existing Click code
import click


@click.command()
@click.option('--name')
def click_command(name):
  print(f"Click: {name}")


# New freyja code
from freyja import FreyjaCLI


class Freya:
  """Freyja-managed commands."""

  def __init__(self):
    pass

  def freya_command(self, name: str) -> None:
    """Freyja command."""
    print(f"Freyja: {name}")


# Separate entry points
if __name__ == '__main__':
  import sys

  if '--click' in sys.argv:
    sys.argv.remove('--click')
    click_command()
  else:
    cli = FreyjaCLI(Freya)
    cli.run()
```

## Usage and Best Practices

### How do I organize large applications?

For large applications, use class-based CLI with logical method grouping:

```python
class DatabaseCLI:
    """Database management command tree."""
    
    def __init__(self):
        self.connection = None
    
    # Connection management
    def connect(self, host: str, database: str, port: int = 5432) -> None:
        """Connect to database."""
        pass
    
    def disconnect(self) -> None:
        """Disconnect from database."""
        pass
    
    # Data operations  
    def backup(self, output_file: str, compress: bool = True) -> None:
        """Create database backup."""
        pass
    
    def restore(self, backup_file: str, confirm: bool = False) -> None:
        """Restore from backup."""
        pass
    
    # Maintenance
    def vacuum(self, analyze: bool = True) -> None:
        """Vacuum database."""
        pass

cli = FreyjaCLI(DatabaseCLI, title="Database Tools")
```

### How do I handle configuration across commands?

Use class-based CLI with instance variables:

```python
class AppCLI:
    """Application with persistent configuration."""
    
    def __init__(self):
        self.config = {
            'debug': False,
            'output_format': 'json',
            'api_url': 'http://localhost:8080'
        }
    
    def set_config(self, key: str, value: str) -> None:
        """Set configuration value."""
        self.config[key] = value
        print(f"✅ Set {key} = {value}")
    
    def show_config(self) -> None:
        """Display current configuration."""
        for key, value in self.config.items():
            print(f"{key}: {value}")
    
    def process_data(self, data: str) -> None:
        """Process data using current configuration."""
        if self.config['debug']:
            print(f"Debug: Processing {data}")
        
        # Use self.config values for processing
        print(f"Format: {self.config['output_format']}")
```

### How do I test CLI applications?

Test functions directly rather than through CLI:

```python
import pytest

def process_numbers(values: List[int], threshold: int = 10) -> List[int]:
    """Filter numbers above threshold."""
    return [v for v in values if v > threshold]

# Test the function directly
def test_process_numbers():
    result = process_numbers([5, 15, 8, 20], threshold=10)
    assert result == [15, 20]

def test_process_numbers_empty():
    result = process_numbers([], threshold=10)
    assert result == []

# Integration test (when needed)
def test_cli_integration():
    import subprocess
    result = subprocess.run([
        'python', 'script.py', 'process-numbers',
        '--values', '5', '15', '8', '20',
        '--threshold', '10'
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert '[15, 20]' in result.stdout
```

### How do I handle secrets and sensitive data?

Never pass secrets as command-line arguments (they're visible in process lists):

```python
import os
import getpass
from pathlib import Path

def connect_db(host: str, database: str, username: str = None) -> None:
    """Connect to database with secure password handling."""
    
    # Try environment variable first
    password = os.getenv('DB_PASSWORD')
    
    # Try password file
    if not password:
        password_file = Path.home() / '.db_password'
        if password_file.exists():
            password = password_file.read_text().strip()
    
    # Prompt user if needed
    if not password:
        password = getpass.getpass(f"Password for {username}@{host}: ")
    
    print(f"Connecting to {database} at {host}")
    # Use password for connection

# ❌ Never do this:
def bad_connect(host: str, password: str) -> None:  # Visible in ps aux!
    pass

# ✅ Good: Use environment variables, files, or prompts
def good_connect(host: str) -> None:
    password = os.getenv('DB_PASSWORD') or getpass.getpass("Password: ")
```

## Troubleshooting

### My function isn't showing up in the CLI

Check these common issues:

1. **Missing type annotations**:
```python
# ❌ Won't work
def my_function(name):
    pass

# ✅ Will work
def my_function(name: str) -> None:
    pass
```

2. **Private function (starts with underscore)**:
```python
# ❌ Ignored by Freyja
def _private_function(data: str) -> None:
    pass

# ✅ Visible to Freyja
def public_function(data: str) -> None:
    pass
```

3. **Method defined outside the class body**:
```python
# ❌ Loose function won't be discovered (Freyja is class-only)
def my_function(data: str) -> None:
    pass

if __name__ == '__main__':
    cli = FreyjaCLI(my_function)  # TypeError — not a class

# ✅ Method inside a class
class Tools:
    def __init__(self):
        pass

    def my_function(self, data: str) -> None:
        pass

if __name__ == '__main__':
    cli = FreyjaCLI(Tools)
```

### I'm getting "TypeError: missing required argument"

This means you didn't provide a required parameter:

```bash
# ❌ Missing required parameter
python script.py process-file
# Error: missing required argument: 'input_file'

# ✅ Provide all required parameters  
python script.py process-file --input-file data.txt
```

### Boolean flags aren't working as expected

Boolean parameter behavior depends on the default value:

```python
# Default False -> Single flag to enable
def process(verbose: bool = False) -> None:
    pass
# Usage: --verbose (sets to True)

# Default True -> Dual flags to enable/disable  
def process(auto_save: bool = True) -> None:
    pass
# Usage: --auto-save (True) or --no-auto-save (False)
```

### Colors aren't showing up

Check these issues:

1. **Colors disabled**:
```python
cli = FreyjaCLI(MyClass, no_color=False)  # Ensure enabled
```

2. **Terminal doesn't support colors**:
```bash
# Test in different terminal or force COLORS
FORCE_COLOR=1 python script.py
```

3. **Output redirected**:
```bash
# Colors automatically disabled when redirected
python script.py > output.txt  # No COLORS (correct behavior)
python script.py              # Colors enabled
```

## Advanced Usage

### Can I create multiple CLIs in one script?

Yes — build a separate class for each persona and pick at the entry point:

```python
from freyja import FreyjaCLI


class AdminTools:
    """Administrative operations."""

    def __init__(self):
        pass

    def reset_database(self, confirm: bool = False) -> None:
        """Reset the entire database."""
        pass

    def backup_system(self, destination: str) -> None:
        """Create full system backup."""
        pass


class UserTools:
    """End-user operations."""

    def __init__(self):
        pass

    def view_profile(self, username: str) -> None:
        """View user profile."""
        pass

    def update_profile(self, username: str, email: str = None) -> None:
        """Update user profile."""
        pass


if __name__ == '__main__':
    import sys

    if '--admin' in sys.argv:
        sys.argv.remove('--admin')
        cli = FreyjaCLI(AdminTools, title="Admin Tools")
    else:
        cli = FreyjaCLI(UserTools, title="User Tools")

    cli.run()
```

### How do I create plugin-like architectures?

Compose multiple plugin classes via Freyja's multi-class support:

```python
from freyja import FreyjaCLI


class CorePlugin:
    """Always-available core commands."""

    def __init__(self):
        pass

    def status(self) -> None:
        """Show overall status."""
        pass


class ReportingPlugin:
    """Reporting plugin."""

    def __init__(self):
        pass

    def daily_report(self, output: str = "report.txt") -> None:
        """Generate a daily report."""
        pass


# Pass a list of classes — non-primary classes become hierarchical command groups
cli = FreyjaCLI([ReportingPlugin, CorePlugin], title="Extensible Freyja")
cli.run()
```

### How do I add progress bars or interactive features?

Use third-party libraries within your functions:

```python
import time
from typing import List

def process_large_dataset(
    files: List[str], 
    batch_size: int = 100,
    show_progress: bool = True
) -> None:
    """Process large dataset with optional progress bar."""
    
    if show_progress:
        try:
            from tqdm import tqdm
            file_iterator = tqdm(files, desc="Processing files")
        except ImportError:
            print("Install tqdm for progress bars: pip install tqdm")
            file_iterator = files
    else:
        file_iterator = files
    
    for i, file_path in enumerate(file_iterator):
        # Simulate processing
        time.sleep(0.1)  
        
        if show_progress and i % batch_size == 0:
            print(f"Processed batch {i // batch_size + 1}")

# Usage with progress: python script.py process-large-dataset --files *.txt --show-progress
```

## See Also

- **[Troubleshooting Guide](guides/troubleshooting.md)** - Detailed error solutions
- **[Type Annotations](features/type-annotations.md)** - Supported types reference
- **[API Reference](reference/api.md)** - Complete method reference
- **[Basic Usage](getting-started/basic-usage.md)** - Core concepts and patterns

---

**Navigation**: [← Help Hub](README.md) | [Troubleshooting →](guides/troubleshooting.md)  
**Examples**: [Class Example](../examples/cls_example)
