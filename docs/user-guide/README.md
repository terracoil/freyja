![Freyja Action](https://github.com/terracoil/freyja/raw/main/docs/freyja-action.png)

# 👤 User Guide

[↑ Documentation Hub](../README.md)

Master the art of building CLIs with Freyja! This comprehensive guide covers everything from basic patterns to advanced techniques for both module-based and class-based approaches.

## Table of Contents
* [🎯 Core Concepts](#-core-concepts)
* [📚 Key Topics Covered](#-key-topics-covered)
* [⚡ Quick Examples](#-quick-examples)
  * [Module CLI Example](#module-cli-example)
  * [Class CLI Example](#class-cli-example)
* [🚀 Next Steps](#-next-steps)

# Children

### 🗂️ Module-based CLIs
* **[📝 Module CLI Guide](class-cli.md)** - Complete guide to function-based CLIs with patterns, organization, and best practices

### 🏗️ Class-based CLIs  
* **[🏗️ Class CLI Guide](class-cli.md)** - Comprehensive guide to method-based CLIs with state management and design patterns
* **[🏢 Inner Classes Pattern](inner-classes.md)** - Advanced pattern using inner classes for organized flat command structures

## 🎯 Core Concepts

### 🏗️ Class CLI Mastery
**[Complete Class CLI Guide →](class-cli.md)**

Transform your Python functions into powerful CLIs:
- **Function Design** - Best practices for CLI-ready functions
- **Type Annotations** - Leverage Python's type system for automatic validation  
- **Command Organization** - Structure complex applications with clear hierarchies
- **Parameter Handling** - Master defaults, optionals, and advanced types
- **Testing Strategies** - Ensure your CLIs work perfectly in production

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

Organize complex applications with hierarchical flat commands:
- **Double-dash Commands** - `database--migrate`, `deploy--build` command patterns
- **Multi-level Arguments** - Global, sub-global, and command-specific parameters
- **Organization Strategies** - Structure large applications with clear command groups
- **Real-world Examples** - Database tools, deployment systems, and more

### 🔄 Choosing Your Approach
**[Mode Comparison Guide →](class-cli.md)**

Make the right architectural decision:
- **Feature-by-feature Analysis** - Detailed comparison matrix
- **Use Case Recommendations** - When to use each approach
- **Migration Strategies** - How to switch between patterns
- **Performance Considerations** - Optimize for your specific needs

## 📚 Key Topics Covered

### 🗂️ Module CLI Expertise
- ✅ **Command Generation** - Automatic CLI creation from function signatures
- 🎯 **Type System Integration** - Leverage annotations for validation and help  
- 📋 **Parameter Management** - Handle complex argument structures
- 🔧 **Function Organization** - Structure modules for optimal CLI generation
- 🏗️ **Hierarchical Commands** - Build complex command trees with clear organization

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

### Module CLI Example

**Perfect for:** Utilities, scripts, functional programming

```python
# data_processor.py
from freyja import CLI
from enum import Enum


class OutputFormat(Enum):
    JSON = "json"
    CSV = "csv"
    XML = "xml"


def convert_data(input_file: str, output_format: OutputFormat = OutputFormat.JSON, 
                verbose: bool = False) -> None:
    """Convert data file between different formats.
    
    Args:
        input_file: Path to input data file
        output_format: Target format for conversion
        verbose: Enable detailed logging
    """
    print(f"Converting {input_file} to {output_format.value}")
    if verbose:
        print("Verbose mode: showing detailed progress...")


def validate_data(file_path: str, schema_file: str = None, strict: bool = True) -> None:
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
    CLI.display()
```

**Usage:**
```bash
python data_processor.py convert-data --input-file data.csv --output-format xml --verbose
python data_processor.py validate-data --file-path users.json --schema-file user_schema.json
python data_processor.py --help  # Beautiful auto-generated help!
```

### Class CLI Example

**Perfect for:** Stateful applications, complex workflows

```python
# project_manager.py
from freyja import CLI
from pathlib import Path


class ProjectManager:
    """Advanced project management CLI with persistent configuration."""
    
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
    
    def create_project(self, name: str, template: str = "basic", 
                      description: str = "") -> None:
        """Create a new project from template.
        
        Args:
            name: Project name (must be unique)
            template: Project template to use
            description: Optional project description
        """
        self.projects[name] = {
            "template": template,
            "description": description,
            "status": "created"
        }
        
        print(f"Created project '{name}' using template '{template}'")
        if description:
            print(f"Description: {description}")
        if self.debug:
            print(f"Project stored in memory. Total projects: {len(self.projects)}")
    
    def deploy_project(self, project_name: str, environment: str = "staging", 
                      force: bool = False) -> None:
        """Deploy project to target environment.
        
        Args:
            project_name: Name of project to deploy
            environment: Target deployment environment
            force: Force deployment even if environment is not empty
        """
        if project_name not in self.projects:
            print(f"Error: Project '{project_name}' not found")
            return
            
        action = "Force deploying" if force else "Deploying"
        print(f"{action} '{project_name}' to {environment}")
        
        # Update project status
        self.projects[project_name]["status"] = f"deployed-{environment}"
        
        if self.debug:
            print(f"Updated project status: {self.projects[project_name]}")
    
    def list_projects(self, status_filter: str = None) -> None:
        """List all projects with optional status filtering.
        
        Args:
            status_filter: Optional status to filter projects by
        """
        if not self.projects:
            print("No projects found")
            return
            
        print(f"Projects (using config: {self.config_file}):")
        for name, info in self.projects.items():
            if status_filter and info["status"] != status_filter:
                continue
                
            status = info["status"]
            template = info["template"]
            description = info.get("description", "")
            
            print(f"  • {name} [{status}] ({template})")
            if description:
                print(f"    {description}")


if __name__ == '__main__':
    CLI.display()
```

**Usage:**
```bash
# Global configuration affects all commands
python project_manager.py --config-file prod.json --debug \
    create-project --name "web-app" --template "react" --description "Production web app"

python project_manager.py --config-file prod.json \
    deploy-project --project-name "web-app" --environment "production" --force

python project_manager.py list-projects --status-filter "deployed-production"

# Each command maintains the global state set by constructor
python project_manager.py --help  # Shows all available commands
```

## 🚀 Next Steps

### 📚 Deep Dive into Your Chosen Pattern
- **[Module CLI →](class-cli.md)** - Master function-based CLIs
- **[Class CLI →](class-cli.md)** - Master object-oriented CLIs  
- **[Inner Classes →](inner-classes.md)** - Advanced hierarchical organization
- **[Mode Comparison →](class-cli.md)** - Choose the right approach

### 🔧 Enhance Your CLIs
- **[Features Guide →](../features/README.md)** - Type annotations, themes, completion
- **[Best Practices →](../guides/best-practices.md)** - Professional development techniques
- **[Real Examples →](../guides/examples.md)** - Production-ready applications

### 🚨 Troubleshooting & Support
- **[Troubleshooting →](../guides/troubleshooting.md)** - Solve common issues
- **[FAQ →](../faq.md)** - Quick answers to frequent questions  
- **[Advanced Topics →](../advanced/README.md)** - Complex scenarios and edge cases

---

**Ready to build professional CLIs?** Choose your path and start creating amazing command-line tools! 🚀