![Freyja Action](https://github.com/terracoil/freyja/raw/main/docs/freyja-action.png)

# 👤 User Guide

[↑ Documentation Hub](../README.md)

Master the art of building CLIs with Freyja! This comprehensive guide covers everything from basic patterns to advanced techniques for class-based CLI development.

**⚠️ Important:** All constructor parameters MUST have default values for CLI generation to work.

## Table of Contents
* [🎯 Core Concepts](#-core-concepts)
* [📚 Key Topics Covered](#-key-topics-covered)
* [⚡ Quick Examples](#-quick-examples)
  * [Direct Methods Example](#direct-methods-example)
  * [Inner Classes Example](#inner-classes-example)
* [🚀 Next Steps](#-next-steps)

# Children

### 🏗️ Class-based CLI Patterns
* **[🏗️ Class CLI Guide](class-cli.md)** - Comprehensive guide to method-based CLIs with state management and design patterns
* **[🏢 Inner Classes Pattern](inner-classes.md)** - Advanced pattern using inner classes for organized hierarchical command structures

## 🎯 Core Concepts

### 🏗️ Class CLI Excellence
**[Complete Class CLI Guide →](class-cli.md)**

Build stateful, object-oriented command-line applications:
- **Class Architecture** - Design patterns for maintainable CLI classes
- **State Management** - Handle persistent data and configuration elegantly
- **Method Organization** - Structure your class methods for optimal CLI generation
- **Constructor Patterns** - Handle global configuration through class initialization
- **Lifecycle Management** - Control object creation and resource handling

### 🏢 Inner Classes Power Pattern
**[Inner Classes Guide →](inner-classes.md)**

Organize complex applications with hierarchical commands:
- **Hierarchical Commands** - `database migrate`, `deploy build` command patterns
- **Multi-level Arguments** - Global, sub-global, and command-specific parameters
- **Organization Strategies** - Structure large applications with clear command groups
- **Real-world Examples** - Database tools, deployment systems, and more

### 🔄 Choosing Your Pattern
**[Pattern Selection Guide →](class-cli.md)**

Decide between direct methods and inner classes:
- **Pattern Analysis** - When to use direct methods vs inner classes
- **Use Case Recommendations** - Best pattern for your application
- **Organization Strategies** - Structure your commands effectively
- **Performance Considerations** - Optimize for your specific needs

## 📚 Key Topics Covered

### 🏗️ Class CLI Mastery
- 🎛️ **Method-to-Command Mapping** - Transform class methods into CLI commands
- 💾 **State Persistence** - Maintain application state between command invocations
- ⚙️ **Constructor Integration** - Use class initialization for global configuration
- 🔒 **Visibility Control** - Control which methods become CLI commands
- 🏛️ **Instance Lifecycle** - Manage object creation and resource cleanup

### 🌟 Universal Patterns
- 🚨 **Error Handling** - Robust strategies for CLI error management
- ⚙️ **Configuration Management** - Handle settings, config files, and environment variables
- 🔧 **Resource Handling** - Manage files, connections, and external resources
- 🧪 **Testing Approaches** - Test your CLIs effectively in all scenarios
- 📖 **Documentation Practices** - Generate beautiful help text automatically

## ⚡ Quick Examples

### Direct Methods Example

**Perfect for:** Simple applications, utilities, straightforward commands

```python
# data_processor.py
from freyja import FreyjaCLI
from enum import Enum


class DataProcessor:
    """Data processing and validation utilities."""

    def __init__(self, config_file: str = "config.json", verbose: bool = False):
        """Initialize processor with configuration."""
        self.config_file = config_file
        self.verbose = verbose

    def convert_data(self, input_file: str, output_format: str = "json") -> None:
        """Convert data file between different formats.

        Args:
            input_file: Path to input data file
            output_format: Target format for conversion (json, csv, xml)
        """
        print(f"Converting {input_file} to {output_format}")
        if self.verbose:
            print("Verbose mode: showing detailed progress...")

    def validate_data(self, file_path: str, schema_file: str = None, strict: bool = True) -> None:
        """Validate data file against schema.

        Args:
            file_path: Path to data file for validation
            schema_file: Optional schema file for validation rules
            strict: Enable strict validation mode
        """
        mode = "strict" if strict else "lenient"
        schema_info = f"using {schema_file}" if schema_file else "using default schema"
        print(f"Validating {file_path} in {mode} mode ({schema_info})")


if __name__ == '__main__':
    cli = FreyjaCLI(DataProcessor, title="Data Processing Utility")
    cli.run()
```

**Usage:**
```bash
python data_processor.py convert-data --input-file data.csv --output-format xml
python data_processor.py validate-data --file-path users.json --schema-file user_schema.json
python data_processor.py --help  # Beautiful auto-generated help!
```

### Inner Classes Example

**Perfect for:** Complex applications with organized command groups

```python
# project_manager.py
from freyja import FreyjaCLI
from pathlib import Path


class ProjectManager:
    """Advanced project management CLI with hierarchical commands."""

    def __init__(self, config_file: str = "project.json", debug: bool = False):
        """Initialize project manager with global settings.

        Args:
            config_file: Path to project configuration file
            debug: Enable debug logging throughout the application
        """
        self.config_file = config_file
        self.debug = debug
        self.projects = {}  # In-memory project storage

        if debug:
            print(f"Debug mode enabled, using config: {config_file}")

    class Projects:
        """Project creation and management commands."""

        def __init__(self, workspace: str = "./projects", auto_save: bool = True):
            """Initialize project operations with sub-global settings."""
            self.workspace = workspace
            self.auto_save = auto_save

        def create(self, name: str, template: str = "basic",
                        description: str = "") -> None:
            """Create a new project from template.

            Args:
                name: Project name (must be unique)
                template: Project template to use
                description: Optional project description
            """
            print(f"Creating project '{name}' using template '{template}'")
            print(f"Workspace: {self.workspace}")
            if description:
                print(f"Description: {description}")
            if self.auto_save:
                print("Auto-saving project...")

        def deploy(self, project_name: str, environment: str = "staging",
                        force: bool = False) -> None:
            """Deploy project to target environment.

            Args:
                project_name: Name of project to deploy
                environment: Target deployment environment
                force: Force deployment even if environment is not empty
            """
            action = "Force deploying" if force else "Deploying"
            print(f"{action} '{project_name}' to {environment}")

    class Database:
        """Database operations and maintenance."""

        def migrate(self, version: str = "latest", dry_run: bool = False) -> None:
            """Run database migrations.

            Args:
                version: Target migration version
                dry_run: Preview changes without applying them
            """
            action = "Would migrate" if dry_run else "Migrating"
            print(f"{action} database to version {version}")

        def backup(self, output_path: Path, compress: bool = True) -> None:
            """Create database backup.

            Args:
                output_path: Where to save the backup
                compress: Whether to compress the backup file
            """
            compression = "compressed" if compress else "uncompressed"
            print(f"Creating {compression} backup at {output_path}")


if __name__ == '__main__':
    cli = FreyjaCLI(ProjectManager, title="Project Management Suite")
    cli.run()
```

**Usage with hierarchical commands:**
```bash
# Global + Sub-global + Command arguments
python project_manager.py --config-file prod.json --debug \
    projects create --workspace /prod/projects --auto-save \
    --name "web-app" --template "react" --description "Production web app"

python project_manager.py --config-file prod.json \
    projects deploy --project-name "web-app" --environment "production" --force

python project_manager.py database migrate --version 2.1.0 --dry-run

python project_manager.py database backup --output-path /backups/prod.sql --compress

# Each command maintains the global state set by constructor
python project_manager.py --help  # Shows all available commands hierarchically
```

## 🚀 Next Steps

### 📚 Deep Dive into Your Chosen Pattern
- **[Class CLI →](class-cli.md)** - Master object-oriented CLIs
- **[Inner Classes →](inner-classes.md)** - Advanced hierarchical command organization
- **[Pattern Selection →](class-cli.md)** - Choose between direct methods and inner classes

### 🔧 Enhance Your CLIs
- **[Features Guide →](../features/README.md)** - Type annotations, themes, completion
- **[Best Practices →](../guides/best-practices.md)** - Professional development techniques
- **[Real Examples →](../guides/examples.md)** - Production-ready applications

### 🚨 Troubleshooting & Support
- **[Troubleshooting →](../guides/troubleshooting.md)** - Solve common issues
- **[FAQ →](../faq.md)** - Quick answers to frequent questions
- **[Advanced Topics →](../advanced/README.md)** - Complex scenarios and edge cases

---

**Ready to build professional CLIs?** Choose your pattern and start creating amazing command-line tools! 🚀