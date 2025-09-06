# Error Handling

[← Back to Features](README.md) | [↑ Documentation Hub](../README.md)

## Overview

freyja provides comprehensive error handling to ensure user-friendly error messages and proper exit codes.

## Error Types

### Type Validation Errors
When arguments don't match expected types:
```bash
$ my-cli process --count "not-a-number"
Error: Invalid value for --count: 'not-a-number' is not a valid integer
```

### Missing Required Arguments
```bash
$ my-cli process
Error: Missing required argument: input_file
```

### Invalid Enum Values
```bash
$ my-cli process --format INVALID
Error: Invalid choice for --format: 'INVALID'
Valid choices are: json, csv, xml
```

### 🔥 New Feature Error Scenarios

#### Positional Parameter Validation Errors

When positional parameters fail type validation:
```bash
$ my-cli compress-files ./docs not-a-number
Error: Invalid value for positional parameter 'compression_level': 'not-a-number' is not a valid integer

$ my-cli process-data ./nonexistent.csv
Error: Positional parameter 'input_file': Path './nonexistent.csv' does not exist
```

#### Missing Positional Parameter
```bash
$ my-cli backup-database --output-dir /backups
Error: Missing required positional argument: database_name
Usage: my-cli backup-database <database_name> [--output-dir DIR] [--compress]
```

#### Conflicting Parameter Specifications
```bash
$ my-cli process-file data.txt --input-file other.txt
Error: Parameter 'input_file' specified both as positional argument ('data.txt') and option ('--input-file other.txt')
Suggestion: Use either 'my-cli process-file data.txt' or 'my-cli process-file --input-file other.txt'
```

#### Flexible Ordering Ambiguity
```bash
$ my-cli complex-command file1.txt file2.txt --output-dir /backup
Error: Ambiguous argument order. Cannot determine if 'file2.txt' is a positional argument or belongs to '--output-dir'
Suggestion: Use explicit format: 'my-cli complex-command file1.txt --output-dir file2.txt /backup'
```

#### Hierarchical Command Argument Conflicts
```bash
$ my-cli --debug project-ops--create --workspace /proj my-project --debug
Error: Global argument '--debug' specified multiple times
Suggestion: Specify global arguments only once: 'my-cli --debug project-ops--create --workspace /proj my-project'
```

## Handling Errors in Your Code

### Return Exit Codes
```python
def process_file(file_path: str) -> None:
    """Process a file with proper error handling."""
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        return 1  # Return non-zero for error
    
    try:
        # Process file
        print(f"Processing {file_path}")
        return 0  # Success
    except Exception as e:
        print(f"Error processing file: {e}")
        return 2  # Different error code
```

### Validation in Methods
```python
class DataProcessor:
    def analyze(self, threshold: float) -> None:
        """Analyze data with validation."""
        if not 0 <= threshold <= 1:
            print("Error: Threshold must be between 0 and 1")
            return 1
        
        # Continue processing
```

### Using Exceptions
```python
class APIClient:
    def connect(self, url: str) -> None:
        """Connect to API with exception handling."""
        try:
            # Connection logic
            if not url.startswith(('http://', 'https://')):
                raise ValueError("URL must start with http:// or https://")
        except ValueError as e:
            print(f"Error: {e}")
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}")
            return 2
```

## Best Practices

### Clear Error Messages
```python
# ❌ Poor error message
print("Error!")

# ✅ Clear, actionable message
print(f"Error: Cannot read file '{filename}'. Please check the file exists and you have read permissions.")
```

### Consistent Exit Codes
```python
# Common exit code conventions
SUCCESS = 0
GENERAL_ERROR = 1
MISUSE_ERROR = 2
CANNOT_EXECUTE = 126
COMMAND_NOT_FOUND = 127
```

### Error Message Format
```python
def format_error(message: str, suggestion: str = None) -> str:
    """Format error messages consistently."""
    output = f"❌ Error: {message}"
    if suggestion:
        output += f"\n💡 Suggestion: {suggestion}"
    return output
```

### 🔥 Best Practices for New Features

#### Positional Parameter Validation
```python
def process_file(input_file: str, output_format: str = "json") -> None:
    """Process file with proper positional parameter validation."""
    # Validate positional parameter early
    if not input_file:
        print("Error: Input file cannot be empty")
        return 1
    
    if not Path(input_file).exists():
        print(f"Error: Input file '{input_file}' not found")
        print(f"💡 Suggestion: Check the file path and try again")
        return 1
    
    # Continue processing...
```

#### Clear Positional Error Messages
```python
def backup_database(database_name: str, backup_location: str = "./backups") -> None:
    """Backup database with clear validation."""
    if not database_name.strip():
        print("Error: Database name cannot be empty")
        print("💡 Usage: backup-database <database_name> [--backup-location DIR]")
        return 1
        
    # Validate database name format
    if not re.match(r'^[a-zA-Z0-9_]+$', database_name):
        print(f"Error: Invalid database name '{database_name}'")
        print("💡 Database names can only contain letters, numbers, and underscores")
        return 1
```

#### Handle Flexible Ordering Edge Cases
```python
def complex_operation(primary_file: str, secondary_file: str = None,
                     output_dir: str = "./output") -> None:
    """Handle potential conflicts in flexible ordering."""
    # Clear validation for ambiguous cases
    if secondary_file and primary_file == secondary_file:
        print("Error: Primary and secondary files cannot be the same")
        print("💡 Suggestion: Specify different files or omit --secondary-file")
        return 1
        
    # Validate paths exist
    for file_path in [f for f in [primary_file, secondary_file] if f]:
        if not Path(file_path).exists():
            print(f"Error: File not found: {file_path}")
            return 1
```

## Debugging

### Enable Debug Mode
```python
class DebugCLI:
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def process(self, file: str) -> None:
        try:
            # Processing logic
            pass
        except Exception as e:
            if self.debug:
                import traceback
                traceback.print_exc()
            else:
                print(f"Error: {e}")
```

### Verbose Error Output
```bash
# Set environment variable for debugging
export FREYA_DEBUG=1
python my_cli.py command --args
```

## User-Friendly Features

### Suggestions for Typos
freyja can suggest correct commands for typos:
```bash
$ my-cli porcess
Error: Unknown command 'porcess'
Did you mean 'process'?
```

### Help on Error
Show help when commands fail:
```bash
$ my-cli process
Error: Missing required argument: input_file

Usage: my-cli process --input-file FILE [OPTIONS]

Run 'my-cli process --help' for more information.
```

## See Also

**🔥 Related New Features**
- **[Flexible Argument Ordering](flexible-ordering.md)** - Error scenarios for flexible ordering
- **[Positional Parameters](positional-parameters.md)** - Positional parameter validation

**📚 Error Management**
- **[Type Annotations](type-annotations.md)** - Type validation and errors  
- **[Troubleshooting](../guides/troubleshooting.md)** - Common errors and solutions
- **[Best Practices](../guides/best-practices.md)** - Professional error handling patterns

---

**Navigation**: [← Shell Completion](shell-completion.md) | [Features Index →](README.md)