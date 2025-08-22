# Auto-CLI-Py Documentation

[← Back to README](../README.md) | [⚙️ Development Guide](../CLAUDE.md)

## Table of Contents
- [Overview](#overview)
- [Two CLI Creation Modes](#two-cli-creation-modes)
- [Quick Comparison](#quick-comparison)
- [Getting Started](#getting-started)
- [Feature Guides](#feature-guides)
- [Reference Documentation](#reference-documentation)

## Overview

Auto-CLI-Py is a Python library that automatically builds complete CLI applications from your existing code using introspection and type annotations. It supports two distinct modes of operation, each designed for different use cases and coding styles.

## Two CLI Creation Modes

### 🗂️ Module-based CLI
Create CLIs from module functions - perfect for functional programming styles and simple utilities.

```python
# mod_example.py
def greet(name: str, excited: bool = False) -> None:
    """Greet someone by name."""
    greeting = f"Hello, {name}!"
    if excited:
        greeting += " 🎉"
    print(greeting)

# Create CLI from module
from auto_cli import CLI
import sys
cli = CLI.from_module(sys.modules[__name__], title="My Module CLI")
cli.display()
```

### 🏗️ Class-based CLI
Create CLIs from class methods - ideal for stateful applications and object-oriented designs.

```python
# cls_example.py
class UserManager:
    """User management CLI application."""
    
    def __init__(self):
        self.users = []
    
    def add_user(self, username: str, email: str, active: bool = True) -> None:
        """Add a new user to the system."""
        user = {"username": username, "email": email, "active": active}
        self.users.append(user)
        print(f"Added user: {username}")
    
    def list_users(self, active_only: bool = False) -> None:
        """List all users in the system."""
        users_to_show = self.users
        if active_only:
            users_to_show = [u for u in users_to_show if u["active"]]
        
        for user in users_to_show:
            status = "✓" if user["active"] else "✗"
            print(f"{status} {user['username']} ({user['email']})")

# Create CLI from class
from auto_cli import CLI
cli = CLI.from_class(UserManager, theme_name="colorful")
cli.display()
```

## Quick Comparison

| Feature | Module-based | Class-based |
|---------|-------------|-------------|
| **Use Case** | Functional utilities, scripts | Stateful apps, complex workflows |
| **State Management** | Function parameters only | Instance variables + parameters |
| **Organization** | Functions in module | Methods in class |
| **CLI Creation** | `CLI.from_module(module)` | `CLI.from_class(SomeClass)` |
| **Title Source** | Manual or module docstring | Class docstring |
| **Best For** | Simple tools, data processing | Applications with persistent state |

## Getting Started

### 📚 New to Auto-CLI-Py?
- [Quick Start Guide](getting-started/quick-start.md) - Get running in 5 minutes
- [Installation Guide](getting-started/installation.md) - Detailed setup instructions
- [Basic Usage Patterns](getting-started/basic-usage.md) - Core concepts and examples

### 🎯 Choose Your Mode
- [**Module-based CLI Guide**](module-cli-guide.md) - Complete guide to function-based CLIs
- [**Class-based CLI Guide**](class-cli-guide.md) - Complete guide to method-based CLIs

## Feature Guides

Both CLI modes support the same advanced features:

### 🎨 Theming & Appearance
- [Theme System](features/themes.md) - Color schemes and visual customization
- [Theme Tuner](features/theme-tuner.md) - Interactive theme customization tool

### ⚡ Advanced Features  
- [Type Annotations](features/type-annotations.md) - Supported types and validation
- [Subcommands](features/subcommands.md) - Hierarchical command structures
- [Autocompletion](features/autocompletion.md) - Shell completion setup

### 📖 User Guides
- [Complete Examples](guides/examples.md) - Real-world usage patterns
- [Best Practices](guides/best-practices.md) - Recommended approaches
- [Migration Guide](guides/migration.md) - Upgrading between versions

## Reference Documentation

### 📋 API Reference
- [CLI Class API](reference/api.md) - Complete method reference
- [Configuration Options](reference/configuration.md) - All available settings
- [Command-line Options](reference/cli-options.md) - Built-in CLI flags

### 🔧 Development
- [Architecture Overview](development/architecture.md) - Internal design
- [Contributing Guide](development/contributing.md) - How to contribute
- [Testing Guide](development/testing.md) - Test setup and guidelines

---

**Navigation**: [README](../README.md) | [Development](../CLAUDE.md)
**Examples**: [Module Example](../mod_example.py) | [Class Example](../cls_example.py)