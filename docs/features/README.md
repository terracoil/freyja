![Freyja Action](https://github.com/terracoil/freyja/raw/main/freyja-action.png)

# ⚙️ Features

[↑ Documentation Hub](../README.md)

Discover the powerful features that make Freyja a complete CLI solution. From automatic type validation to beautiful error messages, every feature is designed to accelerate your development while creating professional command-line tools.

## Table of Contents
* [🎯 Core Features](#-core-features)
* [🔥 New Features](#-new-features)
* [✨ Feature Highlights](#-feature-highlights)
* [🔧 Developer Experience](#-developer-experience)
* [🚀 Next Steps](#-next-steps)

# Children

### 🎯 Essential Features
* **[🏷️ Type Annotations](type-annotations.md)** - Complete guide to supported types including basic types, collections, enums, and custom converters
* **[🌈 Shell Completion](shell-completion.md)** - Enable tab completion for Bash, Zsh, Fish, and PowerShell with zero configuration
* **[❌ Error Handling](error-handling.md)** - Robust error management with user-friendly messages and proper exit codes

### 🔥 New Features
* **[🎯 Flexible Argument Ordering](flexible-ordering.md)** - Mix options and arguments in any order for natural command flow
* **[📍 Positional Parameters](positional-parameters.md)** - Automatic positional detection creates intuitive command interfaces

## 🎯 Core Features

### 🏷️ Type System Mastery
**[Complete Type Guide →](type-annotations.md)**

Transform Python type annotations into powerful CLI validation:
- **🔤 Basic Types** - `str`, `int`, `float`, `bool` with automatic conversion
- **📋 Collections** - `List[str]`, `Set[int]`, `Dict[str, any]` support
- **❓ Optional Types** - `Optional[str]`, `Union[str, int]` for flexible inputs
- **🎯 Enums** - Type-safe choices with automatic help generation
- **📁 Paths** - `Path`, `pathlib.Path` with existence validation
- **🔧 Custom Types** - Define your own type converters for domain objects

### 🌈 Shell Completion Excellence
**[Completion Setup Guide →](shell-completion.md)**

Enable professional tab completion with zero configuration:
- **🖥️ Universal Support** - Bash, Zsh, Fish, and PowerShell compatibility
- **⚡ Instant Setup** - One command enables completion for your CLI
- **🎯 Smart Completion** - Context-aware suggestions for arguments and values
- **🔧 Custom Logic** - Define custom completion behavior for complex types
- **🐞 Easy Debugging** - Built-in tools to troubleshoot completion issues

### ❌ Error Handling Mastery
**[Error Management Guide →](error-handling.md)**

Create user-friendly CLIs with robust error handling:
- **🎯 Clear Messages** - Descriptive errors that guide users to solutions
- **✅ Input Validation** - Automatic type checking with helpful suggestions
- **🚪 Proper Exit Codes** - Standard exit codes for shell script integration
- **🛡️ Exception Safety** - Graceful handling of unexpected errors
- **🔍 Debug Support** - Detailed error information for development

## 🔥 New Features

### 🎯 Flexible Argument Ordering
**[Complete Guide →](flexible-ordering.md)**

Experience the freedom of natural command-line interaction:
- **🔀 Any Order** - Mix options and arguments however feels natural
- **💭 Intuitive Flow** - Commands that match how users think
- **🚀 Zero Learning Curve** - Works with existing commands instantly
- **⚡ Smart Parsing** - Automatic argument reordering and validation

```python
def deploy_app(app_name: str, environment: str = "staging", 
               replicas: int = 1, wait: bool = False):
    """Deploy application with flexible argument ordering."""
    pass
```

**All of these work identically:**
```bash
# Traditional order
my-app deploy-app --app-name web-service --environment prod --replicas 3 --wait

# Natural user flow  
my-app deploy-app --environment prod --wait --app-name web-service --replicas 3

# Options first approach
my-app deploy-app --replicas 3 --wait --app-name web-service --environment prod
```

### 📍 Positional Parameters  
**[Complete Guide →](positional-parameters.md)**

Create CLIs that feel natural with automatic positional parameter detection:
- **🔍 Auto-Detection** - First parameter without default becomes positional
- **💬 Natural Commands** - `my-tool process file.txt` instead of `my-tool process --file file.txt`
- **🧠 Zero Configuration** - Works by analyzing your function signatures
- **🔧 Type Safe** - Full type validation on positional parameters

```python
def backup_database(database_name: str, output_dir: str = "./backups", 
                   compress: bool = True):
    """Backup database - database_name becomes positional automatically."""
    pass
```

**Clean, intuitive usage:**
```bash
# Natural command structure
db-tool backup-database production_db --compress --output-dir /backups

# Works with flexible ordering too
db-tool backup-database production_db --output-dir /secure/backups --compress

# Traditional explicit format still works
db-tool backup-database --database-name production_db --compress
```

## ✨ Feature Highlights

### 🚀 Zero-Configuration Magic
```python
from freyja import CLI
from enum import Enum
from pathlib import Path
from typing import List, Optional

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info" 
    WARN = "warn"
    ERROR = "error"

def process_logs(log_files: List[Path], level: LogLevel = LogLevel.INFO, 
                output_dir: Optional[Path] = None, verbose: bool = False) -> None:
    """Process log files with automatic type validation and help generation."""
    for log_file in log_files:
        print(f"Processing {log_file} at {level.value} level")
        if verbose:
            print(f"Output directory: {output_dir or 'current directory'}")

if __name__ == '__main__':
    CLI.display()
```

**Automatic CLI features:**
```bash
# All types automatically validated
python app.py process-logs --log-files logs/app.log logs/error.log --level error --verbose

# Enum choices automatically available
python app.py process-logs --help
# Shows: --level {debug,info,warn,error}

# Path validation built-in
python app.py process-logs --log-files nonexistent.log
# Error: File 'nonexistent.log' does not exist

# Tab completion works immediately
python app.py process-logs --log-files <TAB><TAB>
# Shows available log files in directory
```

### 🎨 Beautiful User Experience
- **📚 Auto-Generated Help** - Professional documentation from your docstrings
- **🌈 Colorful Output** - Beautiful themes with accessibility support
- **✅ Smart Validation** - Type checking with helpful error suggestions
- **🔍 Debug-Friendly** - Clear stack traces and diagnostic information
- **📱 Responsive Design** - Adapts to terminal width and capabilities

### 🔧 Developer-First Design
- **📝 Documentation as Code** - Help text generated from your existing docstrings
- **🎯 Type Safety** - Leverage Python's type system for CLI validation
- **🧪 Testable** - Easy unit testing of CLI functions without subprocess calls
- **🔄 Maintainable** - Clean separation between business logic and CLI layer
- **📦 Deployable** - Single file deployment with zero dependencies

## 🔧 Developer Experience

### 🛠️ Seamless Integration
Perfect compatibility with your favorite tools:

**🏗️ Build Systems**
- **Poetry** - Dependency management and packaging
- **setuptools** - Traditional Python packaging
- **Docker** - Containerized CLI applications

**🧪 Testing Frameworks**
- **pytest** - Unit test your CLI functions directly
- **unittest** - Standard library testing support  
- **hypothesis** - Property-based testing for robust validation

**⚙️ Development Tools**
- **pre-commit** - Code quality automation
- **GitHub Actions** - CI/CD pipeline integration
- **VS Code** - IntelliSense and debugging support

### 📏 Standards Compliance
- **🐧 POSIX Compatible** - Works on Linux, macOS, Windows
- **📋 GNU Conventions** - Familiar argument patterns for users
- **🌐 Unicode Ready** - Full international character support
- **🔧 Shell Scripting** - Easy integration in automation scripts
- **📊 Exit Codes** - Proper status codes for process management

### 🎯 Production Ready
- **⚡ High Performance** - Minimal startup time and memory usage
- **🛡️ Error Resilient** - Graceful handling of edge cases
- **📈 Scalable** - From simple scripts to complex applications
- **🔍 Observable** - Built-in logging and diagnostic capabilities
- **🔒 Secure** - Safe handling of user input and file operations

## 🚀 Next Steps

### 📚 Master the Features
Choose the features most important for your use case:

**🎯 Essential Skills**
- **[Type System →](type-annotations.md)** - Master all supported types and validation
- **[Shell Completion →](shell-completion.md)** - Enable professional tab completion
- **[Error Handling →](error-handling.md)** - Create user-friendly error experiences

**🔥 Latest Features**  
- **[Flexible Ordering →](flexible-ordering.md)** - Natural argument ordering for better UX
- **[Positional Parameters →](positional-parameters.md)** - Automatic positional detection

### 🔧 Advanced Implementation
Once you've mastered the basics:
- **[Best Practices →](../guides/best-practices.md)** - Professional CLI development patterns
- **[Real Examples →](../guides/examples.md)** - Production-ready applications
- **[Advanced Topics →](../advanced/README.md)** - Complex scenarios and edge cases

### ❓ Need Help?
- **[Troubleshooting →](../guides/troubleshooting.md)** - Solve common issues
- **[FAQ →](../faq.md)** - Quick answers to frequent questions
- **[API Reference →](../reference/README.md)** - Complete technical documentation

---

**Ready to unlock Freyja's full potential?** Start with the feature that matters most to your project! 🚀