**→ [Back to Features](README.md) | [Home](../README.md)**

# 📍 Positional Parameters
<img src="https://github.com/terracoil/freyja/raw/main/docs/freyja-github.jpg" alt="Freyja" title="Freyja" height="200"/>

## Overview
**[Freyja](https://pypi.org/project/freyja/)** automatically converts the **first parameter without a default value** into a positional argument, creating more natural and intuitive command-line interfaces. This eliminates the need for verbose `--parameter value` syntax for primary inputs that users expect to provide.

**Key Benefits:**
- **Natural Commands**: `my_cli process data.txt` instead of `my_cli process --filename data.txt`
- **Reduced Typing**: Fewer characters for common operations
- **Intuitive UX**: Matches user expectations from standard CLI tools
- **Automatic Detection**: No configuration required - works by analyzing function signatures

## How Positional Detection Works
**[Freyja](https://pypi.org/project/freyja/)** analyzes function signatures and automatically identifies positional parameters using this rule:

> **The first parameter without a default value becomes positional**

### Detection Examples

```python
def simple_case(filename: str, format: str = "json"):
    """Process file - filename becomes positional."""
    pass
# Usage: my_cli simple-case data.txt --format xml

def multiple_required(source: str, dest: str, options: str = "default"):  
    """Copy files - source becomes positional."""
    pass
# Usage: my_cli multiple-required file.txt --dest backup/ --options fast

def all_optional(format: str = "json", verbose: bool = False):
    """No positional parameters - all have defaults."""
    pass  
# Usage: my_cli all-optional --format xml --verbose

def no_params():
    """No parameters at all."""
    pass
# Usage: my_cli no-params
```

## Class-Based CLI Examples

### File Processing Tool

```python
from freyja import FreyjaCLI

class ArchiveTools:
    """Archive compression and extraction utilities."""
    
    def __init__(self, working_dir: str = ".", verbose: bool = False):
        """Initialize archive tools."""
        self.working_dir = working_dir
        self.verbose = verbose

    def compress_file(self, filename: str, algorithm: str = "gzip", 
                     output_dir: str = "./compressed", keep_original: bool = True):
        """Compress file using specified algorithm."""
        print(f"Compressing {filename} with {algorithm}")
        print(f"Output directory: {output_dir}")
        print(f"Keep original: {keep_original}")

    def extract_archive(self, archive_path: str, destination: str = "./extracted",
                       overwrite: bool = False):
        """Extract archive to destination."""
        pass

if __name__ == '__main__':
    cli = FreyjaCLI(ArchiveTools, title="Archive Tools")  
    cli.run()
```

**Natural Usage:**
```bash
# Positional filename, optional parameters  
archive-tools compress-file document.pdf --algorithm zip --keep-original
archive-tools compress-file presentation.pptx --output-dir /backup

# Extract with positional archive path
archive-tools extract-archive backup.tar.gz --destination /restore --overwrite
archive-tools extract-archive data.zip  # Uses default destination
```

### Database Management

```python
def backup_database(database_name: str, output_file: str = None, 
                   compress: bool = True, exclude_tables: list = None):
    """Backup database to file."""
    output_file = output_file or f"{database_name}_backup.sql"
    print(f"Backing up {database_name} to {output_file}")

def restore_database(backup_file: str, target_database: str = None,
                    force: bool = False):
    """Restore database from backup."""
    target_database = target_database or "restored_db"
    pass
```

**Clean Command Interface:**
```bash
# Natural database commands
db-tool backup-database production_db --compress --output-file prod_backup.sql
db-tool backup-database staging_db  # Uses defaults

db-tool restore-database prod_backup.sql --target-database new_prod --force  
db-tool restore-database backup.sql  # Uses default target name
```

## Class-Based CLI Examples

### Direct Methods

```python
class FileManager:
    def __init__(self, base_directory: str = "./files", debug: bool = False):
        """Initialize file manager."""
        self.base_directory = base_directory
        self.debug = debug

    def copy_file(self, source_file: str, destination: str = None, 
                  preserve_permissions: bool = True):
        """Copy file to destination."""
        destination = destination or f"{self.base_directory}/copy_of_{source_file}"
        pass

    def delete_file(self, filename: str, confirm: bool = False):
        """Delete file with optional confirmation."""
        pass
```

**Usage with Global + Positional:**
```bash
# Global settings + positional file parameter
file-mgr --base-directory /data --debug copy-file document.pdf --destination backup/
file-mgr copy-file important.txt --preserve-permissions

file-mgr delete-file old_file.txt --confirm
```

### Inner Classes (Hierarchical Structure)

```python
class ProjectManager:
    def __init__(self, workspace: str = "./projects", verbose: bool = False):
        """Global project settings."""
        self.workspace = workspace
        self.verbose = verbose

    class Repository:
        def __init__(self, remote_url: str = "origin", branch: str = "main"):
            """Repository operations settings."""
            self.remote_url = remote_url  
            self.branch = branch

        def clone_repo(self, repository_url: str, directory_name: str = None,
                      shallow: bool = False):
            """Clone repository - repository_url is positional."""
            pass

        def push_changes(self, commit_message: str, force: bool = False):
            """Push changes - commit_message is positional."""
            pass

    class Database:
        def __init__(self, connection_timeout: int = 30):
            """Database operations settings."""
            self.timeout = connection_timeout

        def migrate_schema(self, migration_file: str, dry_run: bool = False):
            """Apply migration - migration_file is positional."""
            pass
```

**Complex Hierarchical Commands:**
```bash
# Global + Sub-global + Positional + Optional
project-mgr --workspace /projects --verbose repository clone-repo https://github.com/terracoil/freyja.git --directory-name my-project --shallow --remote-url upstream

# Natural commit commands
project-mgr repository push-changes "Add new feature" --force

# Database migrations with positional file
project-mgr database migrate-schema 001_initial.sql --dry-run --connection-timeout 60
```

## Advanced Positional Patterns

### Mixed Positional and Optional

When the first parameter is positional, remaining parameters follow normal optional rules:

```python
def process_logs(log_file: str, output_format: str = "summary",
                lines_to_process: int = 1000, include_debug: bool = False):
    """Process log file with options."""
    pass
```

**Usage Flexibility:**
```bash
# Positional first, then options in any order
log-processor process-logs application.log --include-debug --lines-to-process 500 --output-format detailed

# Same result, different order  
log-processor process-logs application.log --output-format json --lines-to-process 2000
```

### Multiple Required Parameters

Only the **first** parameter without a default becomes positional:

```python
def transfer_data(source_file: str, destination_file: str, 
                 chunk_size: int = 1024, verify: bool = True):
    """Transfer data between files."""
    # source_file is positional
    # destination_file requires --destination-file flag
    pass
```

**Usage:**
```bash
# First parameter positional, second requires flag
data-transfer transfer-data input.csv --destination-file output.csv --chunk-size 2048 --verify

# This would be an error (missing required destination-file):  
# data-transfer transfer-data input.csv output.csv  # Wrong!
```

### Type Validation with Positional

All type annotations work seamlessly with positional parameters:

```python
from enum import Enum
from pathlib import Path

class CompressionLevel(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"

def compress_image(image_file: Path, quality: CompressionLevel = CompressionLevel.MEDIUM,
                  output_width: int = 800, preserve_metadata: bool = True):
    """Compress image file."""
    pass
```

**Type-Safe Usage:**
```bash
# Path and enum validation on positional parameter
image-tool compress-image /photos/vacation.jpg --quality high --output-width 1024
image-tool compress-image ./portrait.png --preserve-metadata  # Uses defaults
```

## Integration with Other Features

### Works with Flexible Ordering

Positional parameters work seamlessly with flexible argument ordering:

```python
def deploy_app(app_name: str, environment: str = "staging", 
              replicas: int = 1, wait_for_ready: bool = False):
    """Deploy application."""
    pass
```

**Flexible Usage:**
```bash
# All of these work - positional first, options in any order
deploy my-web-app --environment production --replicas 3 --wait-for-ready
deploy my-web-app --wait-for-ready --replicas 5 --environment dev
deploy my-web-app --replicas 2  # Uses default environment
```

### Works with Class Hierarchies

Positional parameters respect the argument hierarchy:

```python
class CloudManager:
    def __init__(self, region: str = "us-west-2", profile: str = "default"):
        """Global cloud settings."""
        pass

    class Compute:
        def __init__(self, instance_type: str = "t2.micro"):
            """Compute settings."""  
            pass

        def launch_instance(self, ami_id: str, key_pair: str = "default-key",
                           security_groups: list = None):
            """Launch EC2 instance."""
            pass
```

**Hierarchical + Positional:**
```bash
# Global + Sub-global + Positional + Optional
cloud --region us-east-1 --profile prod compute--launch-instance ami-12345 --instance-type t3.large --key-pair prod-key --security-groups web,db
```

## Best Practices

### For Function Design

1. **Primary Input First**: Put the most important parameter first without a default
2. **Descriptive Names**: Use clear names that indicate the parameter's purpose  
3. **Logical Defaults**: Provide sensible defaults for optional parameters
4. **Type Annotations**: Always include type hints for validation

```python
# Excellent design - clear primary input
def analyze_data(dataset_file: str, analysis_type: str = "basic", 
                output_format: str = "json", verbose: bool = False):
    """Analyze dataset file."""
    pass

# Good design - file operation
def backup_directory(source_directory: str, backup_location: str = "./backups",
                    compress: bool = True, exclude_patterns: list = None):
    """Backup directory."""
    pass
```

### For User Experience

1. **Consistent Patterns**: Use similar positional patterns across related commands
2. **Clear Documentation**: Show examples in help text and documentation
3. **Logical Grouping**: Group related optional parameters together
4. **Validation Messages**: Provide helpful error messages for invalid inputs

### Command Naming Conventions

Make positional parameter purpose clear from command names:

```python
# Good: Command name indicates what the positional parameter should be
def process_file(filename: str, ...):        # Clear: file processing
def backup_database(db_name: str, ...):     # Clear: database operations  
def deploy_service(service_name: str, ...): # Clear: service deployment

# Less clear: Ambiguous what positional parameter represents
def execute(target: str, ...):              # What is target?
def run(item: str, ...):                    # What kind of item?
```

## Error Handling

### Missing Positional Parameters

```bash
# Error: Missing required positional parameter
$ my_tool process-file --format json
Error: Missing required positional argument: filename
Usage: my_tool process-file <filename> [--format FORMAT] [--verbose]
```

### Type Validation Errors

```bash
# Error: Wrong type for positional parameter  
$ my_tool set-timeout "not-a-number" --units seconds
Error: Invalid value for 'timeout_seconds': 'not-a-number' is not a valid integer
```

### Conflicting Specifications

```bash
# Error: Positional parameter specified both ways
$ my_tool process data.txt --filename other.txt  
Error: Conflict: 'filename' specified both as positional argument ('data.txt') and flag ('--filename other.txt')
Suggestion: Use either 'my_tool process data.txt' or 'my_tool process --filename other.txt'
```

## Troubleshooting

### Common Issues

**Issue**: "Expected positional parameter not found"
- **Cause**: Function signature changed, removing the first non-default parameter
- **Solution**: Update function signature or add required parameter

**Issue**: "Too many positional arguments"  
- **Cause**: Providing more positional args than expected
- **Solution**: Use explicit `--parameter value` format for additional arguments

**Issue**: "Positional parameter after optional arguments"
- **Cause**: Complex argument ordering with multiple required parameters
- **Solution**: Review function design - consider making additional required parameters optional with good defaults

### Debugging

Enable debug mode to see positional parameter detection:

```python
cli = CLI(MyClass, debug=True)
# Shows: "Detected positional parameter: 'filename' (type: str)"
```

### Function Analysis

Check how Freyja interprets your functions:

```bash
my_tool --help
# Shows parameter types and which ones are positional in the usage line
```

## Examples in Practice

### File Processing Pipeline

```python
def convert_format(input_file: str, target_format: str = "pdf", 
                  output_directory: str = "./converted", quality: str = "high"):
    """Convert file format."""
    pass

def batch_convert(directory_path: str, file_pattern: str = "*.docx",
                 target_format: str = "pdf", parallel: bool = True):
    """Batch convert files in directory."""  
    pass
```

**Natural Usage:**
```bash
# Single file conversion
converter convert-format document.docx --target-format pdf --quality medium

# Batch processing 
converter batch-convert /documents --file-pattern "*.ppt" --target-format png --parallel
```

### API Testing Tool

```python
def test_endpoint(endpoint_url: str, method: str = "GET", 
                 headers: dict = None, timeout: int = 30):
    """Test API endpoint."""
    pass

def load_test(base_url: str, concurrent_users: int = 10,
             duration: int = 60, ramp_up: int = 5):
    """Load test API."""
    pass
```

**API Testing Commands:**
```bash
# Simple endpoint tests
api-tester test-endpoint https://httpbin.org/get --method POST --timeout 45

# Load testing  
api-tester load-test https://httpbin.org --concurrent-users 50 --duration 120
```

## Related Documentation

- **[🎯 Flexible Ordering](flexible-ordering.md)** - Mix positional and optional arguments freely
- **[🏷️ Type Annotations](type-annotations.md)** - Type validation for positional parameters
- **[📘 Class CLI Guide](../user-guide/class-cli.md)** - Class-based positional usage  
- **[🏗️ Class CLI Guide](../user-guide/class-cli.md)** - Class-based positional patterns
- **[⚠️ Error Handling](error-handling.md)** - Error messages and validation

---

*📍 **Next Steps**: Learn about [Flexible Argument Ordering](flexible-ordering.md) to combine positional parameters with flexible option ordering, or explore [Type Annotations](type-annotations.md) for advanced parameter validation.*
