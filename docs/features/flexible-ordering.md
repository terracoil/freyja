![Freyja Thumb](https://github.com/terracoil/freyja/raw/main/docs/freyja-thumb.png)
# 🎯 Flexible Argument Ordering

*→ [Back to Features](README.md) | [Home](../README.md)*

## Overview

Freyja provides **flexible argument ordering**, allowing users to specify command-line arguments and options in any order they prefer. This natural approach eliminates the rigid position requirements found in traditional CLI tools, making your applications more user-friendly and intuitive.

**Key Benefits:**
- **Natural Usage**: Users can organize arguments the way they think
- **Error Reduction**: Less chance of mistakes due to position requirements
- **Improved UX**: Commands feel more conversational and flexible
- **Backward Compatible**: Existing commands continue to work unchanged

## How It Works

Freyja's argument preprocessing system automatically reorders arguments before parsing, ensuring that options (flags with `--`) and positional arguments are processed correctly regardless of their input order.

### Basic Example

```python
def process_file(filename: str, format: str = "json", verbose: bool = False):
    """Process a file with optional format and verbosity."""
    print(f"Processing {filename} as {format} (verbose: {verbose})")
```

**All These Commands Work:**
```bash
# Traditional order
my_cli process-file --filename data.txt --format xml --verbose

# Mixed order  
my_cli process-file --verbose --filename data.txt --format xml

# Options first
my_cli process-file --format xml --verbose --filename data.txt

# With positional parameter (see Positional Parameters guide)
my_cli process-file data.txt --format xml --verbose
```

## Module-Based CLI Behavior

For module-based CLIs using `CLI()`, flexible ordering works seamlessly across all functions:

```python
def backup_database(database_name: str, output_dir: str = "./backups", 
                   compress: bool = True, encrypt: bool = False):
    """Backup database with options."""
    pass

def restore_database(backup_file: str, target_db: str, 
                    force: bool = False, verify: bool = True):
    """Restore database from backup."""
    pass

if __name__ == '__main__':
    cli = CLI(sys.modules[__name__], title="Database Tools")
    cli.display()
```

**Flexible Usage Examples:**
```bash
# Any order for backup
my_tool backup-database --database-name prod --compress --output-dir /backups
my_tool backup-database --compress --output-dir /backups --database-name prod
my_tool backup-database prod /backups --compress  # With positional args

# Any order for restore  
my_tool restore-database --backup-file backup.sql --target-db dev --force
my_tool restore-database --force --backup-file backup.sql --target-db dev
my_tool restore-database backup.sql dev --force  # With positional args
```

## Class-Based CLI Behavior

For class-based CLIs, flexible ordering applies to all argument levels:

### Direct Methods

```python
class FileManager:
    def __init__(self, base_path: str = "./files", debug: bool = False):
        """Initialize with global settings."""
        self.base_path = base_path
        self.debug = debug

    def copy_file(self, source: str, destination: str, 
                  overwrite: bool = False, preserve_attrs: bool = True):
        """Copy file with options."""
        pass
```

**All These Work:**
```bash
# Different global argument orders
my_tool --base-path /data --debug copy-file --source file.txt --destination backup/
my_tool --debug --base-path /data copy-file --source file.txt --destination backup/

# Different command argument orders  
my_tool copy-file --overwrite --source file.txt --destination backup/ --preserve-attrs
my_tool copy-file --source file.txt --overwrite --destination backup/
```

### Inner Classes (Hierarchical Commands)

```python
class ProjectManager:
    def __init__(self, config_file: str = "config.json", debug: bool = False):
        """Global settings."""
        self.config_file = config_file
        self.debug = debug

    class ProjectOps:
        def __init__(self, workspace: str = "./projects", auto_save: bool = True):
            """Sub-global settings."""
            self.workspace = workspace
            self.auto_save = auto_save

        def create(self, name: str, description: str = "", template: str = "default"):
            """Create new project."""
            pass
```

**Complex Flexible Ordering:**
```bash
# Global + Sub-global + Command - any order!
my_cli --debug project-ops--create --name "web-app" --workspace /projects --auto-save --description "Web application"

# Rearranged - same result
my_cli project-ops--create --workspace /projects --debug --name "web-app" --description "Web application" --auto-save

# With positional parameter
my_cli --debug project-ops--create "web-app" --workspace /projects --auto-save
```

## Advanced Scenarios

### Mixed Argument Types

When you have global, sub-global, and command arguments, Freyja intelligently sorts them:

```python
class DatabaseAdmin:
    def __init__(self, host: str = "localhost", port: int = 5432):
        """Global connection settings."""
        pass

    class QueryOps:
        def __init__(self, timeout: int = 30, max_rows: int = 1000):
            """Query-specific settings."""
            pass

        def execute(self, sql: str, output_format: str = "table", 
                   save_to_file: str = None):
            """Execute SQL query."""
            pass
```

**Complex Command - Any Order:**
```bash
# All mixed up - still works perfectly
db_cli --port 3306 query-ops--execute --save-to-file results.csv --host db-server --sql "SELECT * FROM users" --timeout 60 --output-format json --max-rows 500

# Equivalent reorganized command
db_cli --host db-server --port 3306 query-ops--execute --timeout 60 --max-rows 500 --sql "SELECT * FROM users" --output-format json --save-to-file results.csv
```

### Positional + Optional Mix

Combining positional parameters with flexible ordering:

```python
def deploy_service(service_name: str, environment: str = "staging", 
                  replicas: int = 1, wait: bool = False):
    """Deploy service to environment."""
    pass
```

**Natural Command Patterns:**
```bash
# Positional first, options in any order
deploy my-service --environment prod --wait --replicas 3

# Options first, then positional (if no conflicts)
deploy --environment prod --replicas 3 my-service --wait

# Mixed throughout (where unambiguous)
deploy --environment prod my-service --replicas 3 --wait
```

## Error Handling and Validation

Freyja provides clear error messages when flexible ordering creates ambiguity:

### Ambiguous Cases

```bash
# If both 'source' and 'destination' are positional parameters
my_tool copy-file file1.txt file2.txt --overwrite  # Clear

# But this might be ambiguous:
my_tool copy-file --overwrite file1.txt file2.txt  # May need clarification
```

**Freyja's Smart Resolution:**
1. **Clear Cases**: Processed automatically without errors
2. **Ambiguous Cases**: Clear error message with suggestions
3. **Best Practice**: Use explicit `--parameter value` format for clarity

### Common Error Messages

```bash
# Example error for ambiguous positional arguments
Error: Ambiguous argument order. Could not determine if 'file2.txt' is the destination or an additional parameter.
Suggestion: Use explicit format: --destination file2.txt

# Example for conflicting parameter names
Error: Parameter 'output' specified both as positional and optional argument.
Suggestion: Use either 'my_tool process output.txt' or 'my_tool process --output output.txt'
```

## Best Practices

### For CLI Authors

1. **Clear Parameter Names**: Use descriptive names that reduce ambiguity
2. **Consistent Patterns**: Maintain similar ordering logic across commands
3. **Document Examples**: Show various ordering options in help text
4. **Test Edge Cases**: Verify behavior with complex argument combinations

```python
# Good: Clear parameter names
def process_data(input_file: str, output_dir: str = "./output", 
                format_type: str = "json"):
    pass

# Less ideal: Ambiguous names
def process_data(file1: str, file2: str = "./output", type: str = "json"):
    pass
```

### For CLI Users

1. **Use Explicit Flags**: When in doubt, use `--parameter value` format
2. **Consistent Ordering**: Develop personal patterns for muscle memory  
3. **Leverage Positional**: Use positional parameters for primary inputs
4. **Read Help Text**: Check `--help` for recommended usage patterns

## Integration with Other Features

### Works With Positional Parameters

```python
def analyze_log(log_file: str, pattern: str = "ERROR", 
               lines: int = 100, context: bool = False):
    """Analyze log file (log_file is automatically positional)."""
    pass
```

```bash
# Flexible ordering + positional parameter
my_tool analyze-log app.log --context --pattern "WARN" --lines 50
my_tool analyze-log --lines 50 app.log --pattern "WARN" --context
```

### Works With Type Annotations

All type validations work regardless of argument order:

```python
def create_user(username: str, age: int = 25, active: bool = True):
    """Create user with validation."""
    pass
```

```bash
# Type validation applies regardless of order
my_tool create-user --age 30 alice --active
my_tool create-user alice --active --age 30  # Same validation
```

### Works With Enums and Choices

```python
from enum import Enum

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info" 
    WARN = "warn"
    ERROR = "error"

def set_logging(level: LogLevel = LogLevel.INFO, output: str = "console"):
    """Configure logging."""
    pass
```

```bash
# Enum validation with flexible ordering
my_tool set-logging --output file.log --level error
my_tool set-logging --level debug --output console
```

## Performance Considerations

Flexible ordering has minimal performance impact:

- **Preprocessing**: Lightweight argument reordering before parsing
- **Memory**: No significant memory overhead
- **Speed**: Negligible impact on command execution time
- **Scalability**: Works efficiently with any number of parameters

## Troubleshooting

### Common Issues

**Issue**: "Parameter specified multiple times"
```bash
my_tool process --input file.txt input.txt  # Conflict
```
**Solution**: Use either positional OR explicit format, not both

**Issue**: "Could not determine parameter assignment"
```bash
my_tool process file1 file2 --overwrite  # Multiple positional ambiguity
```
**Solution**: Use explicit parameter names for clarity

**Issue**: "Unknown parameter order"
```bash  
my_tool --global-option inner-class--method --sub-option --command-option
```
**Solution**: Check help text for proper argument hierarchy

### Debug Mode

Enable debug logging to see how arguments are being processed:

```python
cli = CLI(MyClass, debug=True)
```

This will show the argument preprocessing steps in the output.

## Related Documentation

- **[📍 Positional Parameters](positional-parameters.md)** - Automatic positional argument detection
- **[🏷️ Type Annotations](type-annotations.md)** - Type system integration
- **[⚠️ Error Handling](error-handling.md)** - Error messages and validation
- **[📘 Module CLI Guide](../user-guide/module-cli.md)** - Module-specific usage
- **[🏗️ Class CLI Guide](../user-guide/class-cli.md)** - Class-based patterns

---

*🎯 **Next Steps**: Explore [Positional Parameters](positional-parameters.md) to learn about automatic positional argument detection, or return to [Features Overview](README.md) for more capabilities.*