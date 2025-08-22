# Quick Start Guide

[← Back to Help](../help.md) | [🏠 Documentation Home](../help.md)

## Table of Contents
- [Installation](#installation)
- [Your First CLI](#your-first-cli)
- [Adding Arguments](#adding-arguments)
- [Multiple Commands](#multiple-commands)
- [Next Steps](#next-steps)

## Installation

Get started in seconds with pip:

```bash
pip install auto-cli-py
```

## Your First CLI

Create a simple CLI with just a few lines of code:

**my_cli.py:**

```python
from auto_cli import CLI
import sys


def greet(name: str = "World"):
  """Greet someone with a friendly message."""
  print(f"Hello, {name}!")


# Create and run CLI
cli = CLI(sys.modules[__name__], title="My First CLI")
cli.display()
```

**Run it:**
```bash
python my_cli.py greet --name Alice
# Output: Hello, Alice!

python my_cli.py greet
# Output: Hello, World!
```

**Get help:**
```bash
python my_cli.py --help
python my_cli.py greet --help
```

## Adding Arguments

Use Python type annotations to define CLI arguments:

```python
from typing import Optional
from auto_cli import CLI
import sys


def process_file(
    input_path: str,  # Required argument
    output_path: Optional[str] = None,  # Optional argument
    verbose: bool = False,  # Boolean flag
    count: int = 1  # Integer with default
):
  """Process a file with various options."""
  print(f"Processing {input_path}")
  if output_path:
    print(f"Output will be saved to {output_path}")
  if verbose:
    print("Verbose mode enabled")
  print(f"Processing {count} time(s)")


cli = CLI(sys.modules[__name__])
cli.display()
```

**Usage:**
```bash
python my_cli.py process-file input.txt --output-path output.txt --verbose --count 3
```

## Multiple Commands

Add multiple functions to create a multi-command CLI:

```python
from auto_cli import CLI
import sys


def create_user(username: str, email: str, admin: bool = False):
  """Create a new user account."""
  role = "admin" if admin else "user"
  print(f"Created {role}: {username} ({email})")


def delete_user(username: str, force: bool = False):
  """Delete a user account."""
  if force:
    print(f"Force deleted user: {username}")
  else:
    print(f"Deleted user: {username}")


def list_users(active_only: bool = True):
  """List all user accounts."""
  filter_text = "active users" if active_only else "all users"
  print(f"Listing {filter_text}")


cli = CLI(sys.modules[__name__], title="User Management CLI")
cli.display()
```

**Usage:**
```bash
python user_cli.py create-user alice alice@example.com --admin
python user_cli.py list-users --no-active-only
python user_cli.py delete-user bob --force
```

## Next Steps

🎉 **Congratulations!** You've created your first auto-cli-py CLI. Here's what to explore next:

### Learn More
- **[Basic Usage](basic-usage.md)** - Deeper dive into core concepts
- **[Examples](../guides/examples.md)** - More comprehensive examples
- **[Type Annotations](../features/type-annotations.md)** - Advanced type handling

### Advanced Features
- **[Themes](../features/themes.md)** - Customize your CLI's appearance
- **[Subcommands](../features/subcommands.md)** - Organize complex CLIs
- **[Autocompletion](../features/autocompletion.md)** - Add shell completion

### Get Help
- Browse the **[API Reference](../reference/api.md)** for detailed documentation
- Check out **[Best Practices](../guides/best-practices.md)** for recommended patterns
- Report issues on **[GitHub](https://github.com/tangledpath/auto-cli-py/issues)**

## See Also
- [Installation Guide](installation.md) - Detailed setup instructions
- [Basic Usage](basic-usage.md) - Core patterns and concepts
- [CLI Generation](../features/cli-generation.md) - How auto-cli-py works

---
**Navigation**: [Installation →](installation.md)  
**Parent**: [Help](../help.md)  
**Children**: [Installation](installation.md) | [Basic Usage](basic-usage.md)
