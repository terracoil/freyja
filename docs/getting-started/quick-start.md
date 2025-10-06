![Freyja Action](https://github.com/terracoil/freyja/raw/main/docs/freyja-action.png)
# Quick Start Guide

[← Back to Help](../README.md) | [📦 Installation](installation.md) | [📖 Basic Usage](basic-usage.md)

# Table of Contents
- [Installation](#installation)
- [5-Minute Introduction](#5-minute-introduction)
- [Class-based Example](#class-based-example)
- [Key Features Demonstrated](#key-features-demonstrated)
- [Next Steps](#next-steps)

## Installation

```bash
pip install freyja
```

That's it! No dependencies, works with Python 3.8+.

## 5-Minute Introduction

Freyja automatically creates complete command-line interfaces from your Python classes. Just add type annotations to your methods, and you get a fully-featured CLI with argument parsing, help text, and type validation.

**Class-based approach**: Transform your Python classes into powerful CLIs with hierarchical commands, global options, and professional help generation.

## Class-based Example

Perfect for stateful applications, configuration management, and complex workflows:

```python
# my_tool.py
from freyja import CLI
from pathlib import Path


class DataProcessor:
    """Advanced data processing tool with configuration management."""
    
    def __init__(self, config_file: str = "config.json", debug: bool = False):
        """Initialize processor with global settings."""
        self.config_file = config_file
        self.debug = debug
        self.processed_files = []
    
    def process_file(self, input_file: Path, output_format: str = "json") -> None:
        """Process a single data file.
        
        :param input_file: Input file to process
        :param output_format: Output format (json, csv, xml)
        """
        result = f"Processing {input_file} -> {output_format}"
        if self.debug:
            result += f" (config: {self.config_file})"
        print(result)
        self.processed_files.append(str(input_file))
    
    def list_processed(self) -> None:
        """List all files processed in this session."""
        if self.processed_files:
            print("Processed files:")
            for file in self.processed_files:
                print(f"  - {file}")
        else:
            print("No files processed yet")
    
    class BatchOperations:
        """Batch processing operations for multiple files."""
        
        def __init__(self, parallel: bool = False, max_workers: int = 4):
            """Initialize batch operations."""
            self.parallel = parallel
            self.max_workers = max_workers
        
        def process_directory(self, directory: Path, pattern: str = "*.txt") -> None:
            """Process all files in directory matching pattern."""
            mode = "parallel" if self.parallel else "sequential"
            print(f"Processing directory {directory} ({pattern}) in {mode} mode")
            if self.parallel:
                print(f"Using {self.max_workers} workers")


if __name__ == '__main__':
    cli = CLI(DataProcessor, title="Data Processing Tool")
    cli.display()
```

**Save and run:**
```bash
python my_tool.py --help
# Shows all available commands organized hierarchically

python my_tool.py process-file data.txt --output-format csv
# Processes single file

python my_tool.py --debug process-file data.txt --output-format xml
# Global debug flag affects the processing

python my_tool.py batch-operations process-directory ./data --pattern "*.json" --parallel
# Hierarchical command: batch-operations -> process-directory

# ⚡ Flexible ordering examples:
python my_tool.py --debug process-file data.txt --output-format csv
python my_tool.py process-file --debug data.txt --output-format csv  
python my_tool.py process-file data.txt --debug --output-format csv
# All three commands work identically!
```

## Key Features Demonstrated

### ✨ Automatic CLI Generation
- **Methods → Commands**: Each method becomes a CLI command
- **Inner Classes → Command Groups**: Organize related commands hierarchically
- **Type Hints → Validation**: Automatic argument type checking and conversion

### 🎯 Professional Help Generation
```bash
python my_tool.py --help
```
```
Data Processing Tool

Global Options:
  --config-file TEXT     Initialize processor with global settings (default: config.json)
  --debug               Enable debug mode (default: False)

Commands:
  process-file          Process a single data file
  list-processed        List all files processed in this session
  batch-operations      Batch processing operations for multiple files
```

### 🏗️ Hierarchical Command Structure
```bash
python my_tool.py batch-operations --help
```
```
Batch processing operations for multiple files

Sub-global Options:
  --parallel            Run operations in parallel (default: False)
  --max-workers INT     Number of parallel workers (default: 4)

Commands:
  process-directory     Process all files in directory matching pattern
```

### 🎨 Type-Safe Arguments
- **Path types**: Automatic path validation and completion
- **Enums**: Choice arguments with validation
- **Numbers**: Integer and float parsing with validation
- **Booleans**: Flag arguments (--debug/--no-debug)

### ⚡ Flexible Argument Ordering
- **Global → Command → Options**: Traditional ordering still works
- **Mixed Positioning**: Place global, sub-global, and command options anywhere
- **Natural Usage**: `my_cli --global-opt command --command-opt --another-global-opt`

### 📍 Positional Parameters
- **First Non-Default Parameter**: Automatically becomes positional argument
- **Flexible Usage**: `my_cli command <required_param> [--optional-flags]`
- **Backward Compatible**: Both positional and `--flag` versions work

## Next Steps

### 🚀 Build More CLIs
- **[Class CLI Guide →](../user-guide/class-cli.md)** - Complete patterns and advanced techniques
- **[Basic Usage →](basic-usage.md)** - Core concepts and fundamentals
- **[Type Annotations →](../features/type-annotations.md)** - Advanced type handling

### 📚 Explore Features
- **[Error Handling →](../features/error-handling.md)** - Robust error management
- **[Shell Completion →](../features/shell-completion.md)** - Tab completion for your CLIs
- **[Themes →](../features/themes.md)** - Beautiful, customizable output

### 🔧 Advanced Topics
- **[Best Practices →](../guides/best-practices.md)** - Professional CLI development
- **[Examples →](../guides/examples.md)** - Real-world applications
- **[Troubleshooting →](../guides/troubleshooting.md)** - Common issues and solutions

---

**Ready for more?** [📖 Learn the fundamentals →](basic-usage.md) or [🏗️ dive into class patterns →](../user-guide/class-cli.md)

**Examples**: [Class Example](../../examples/cls_example)