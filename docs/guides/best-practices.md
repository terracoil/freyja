![Freyja Thumb](https://github.com/terracoil/freyja/raw/main/docs/freyja-thumb.png)
# Best Practices

[← Back to Guides](README.md) | [↑ Documentation Hub](../README.md)

## CLI Design Principles

### 1. Clear Command Names
Use descriptive, action-oriented command names:
```python
# ✅ Good
def compress_files(source: str, destination: str) -> None:
    pass

def validate_config(config_file: str) -> None:
    pass

# ❌ Avoid
def proc(s: str, d: str) -> None:
    pass

def check(f: str) -> None:
    pass
```

### 2. Consistent Parameter Naming
Follow consistent naming conventions:
```python
# ✅ Consistent style
def process_data(
    input_file: str,
    output_file: str,
    log_level: str = "INFO"
) -> None:
    pass

# ❌ Inconsistent
def process_data(
    inputFile: str,
    output_file: str,
    log_lvl: str = "INFO"
) -> None:
    pass
```

### 3. Meaningful Defaults
Provide sensible default values:
```python
# ✅ Good defaults
def backup_database(
    database: str,
    output_dir: str = "./backups",
    compression: bool = True,
    retention_days: int = 30
) -> None:
    pass

# ❌ Poor defaults
def backup_database(
    database: str,
    output_dir: str = "/tmp/x",
    compression: bool = False,
    retention_days: int = 9999
) -> None:
    pass
```

## Documentation Best Practices

### 1. Comprehensive Docstrings
Write clear, helpful docstrings:
```python
def analyze_logs(
    log_file: str,
    pattern: str,
    output_format: str = "json",
    case_sensitive: bool = False
) -> None:
    """
    Analyze log files for specific patterns.
    
    Searches through log files to find entries matching the given
    pattern and outputs results in the requested format.
    
    Args:
        log_file: Path to the log file to analyze
        pattern: Regular expression pattern to search for
        output_format: Output format (json, csv, or table)
        case_sensitive: Whether to perform case-sensitive matching
        
    Examples:
        Analyze error logs:
        $ tool analyze-logs server.log --pattern "ERROR.*timeout"
        
        Case-insensitive search with CSV output:
        $ tool analyze-logs app.log --pattern "warning" --output-format csv
    """
    pass
```

### 2. Parameter Documentation
Document all parameters clearly:
```python
# ✅ Good parameter docs
def deploy_application(
    environment: str,
    version: str = "latest",
    dry_run: bool = False
) -> None:
    """
    Deploy application to specified environment.
    
    Args:
        environment: Target environment (dev, staging, or prod)
        version: Version tag or 'latest' for most recent
        dry_run: Simulate deployment without making changes
    """
    pass
```

## Error Handling Best Practices

### 1. User-Friendly Error Messages
```python
def process_file(file_path: str) -> None:
    """Process a file with clear error messages."""
    path = Path(file_path)
    
    # ✅ Clear, actionable error messages
    if not path.exists():
        print(f"❌ Error: File '{file_path}' not found.")
        print(f"💡 Please check the file path and try again.")
        return 1
    
    if not path.suffix in ['.csv', '.json', '.xml']:
        print(f"❌ Error: Unsupported file type '{path.suffix}'.")
        print(f"💡 Supported formats: CSV, JSON, XML")
        return 1
```

### 2. Graceful Degradation
```python
def fetch_data(url: str, timeout: int = 30, retries: int = 3) -> None:
    """Fetch data with graceful error handling."""
    for attempt in range(retries):
        try:
            # Attempt to fetch data
            print(f"Fetching from {url} (attempt {attempt + 1}/{retries})")
            # ... fetch logic ...
            return 0
        except TimeoutError:
            if attempt < retries - 1:
                print(f"⏱️ Timeout, retrying...")
                continue
            print(f"❌ Failed after {retries} attempts")
            return 1
```

## Performance Best Practices

### 1. Lazy Imports
```python
def analyze_dataframe(csv_file: str) -> None:
    """Analyze CSV with pandas (imported only when needed)."""
    # Import heavy dependencies only when function is called
    import pandas as pd
    
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} rows")
```

### 2. Progress Feedback
```python
def process_files(directory: str, pattern: str = "*.txt") -> None:
    """Process files with progress feedback."""
    files = list(Path(directory).glob(pattern))
    total = len(files)
    
    print(f"Processing {total} files...")
    
    for i, file in enumerate(files, 1):
        print(f"[{i}/{total}] Processing {file.name}...")
        # Process file
    
    print(f"✅ Completed processing {total} files")
```

## Testing Best Practices

### 1. Test Functions Directly
```python
# test_cli.py
def test_compress_files():
    """Test compression function directly."""
    # Create test files
    test_input = "test_input.txt"
    test_output = "test_output.gz"
    
    # Test the function
    result = compress_files(test_input, test_output)
    assert result == 0
    assert Path(test_output).exists()
```

### 2. Mock External Dependencies
```python
from unittest.mock import patch

def test_api_call():
    """Test API calls with mocking."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"status": "ok"}
        
        result = check_api_status("https://api.example.com")
        assert result == 0
```

## Organization Best Practices

### 1. Logical Command Grouping
Use inner classes to group related commands into hierarchical subcommands:
```python
class AdminTool:
    """Administrative utility."""

    def __init__(self):
        pass

    class Database:
        """Database operations."""

        def backup(self, database: str, output: str = "backup.sql") -> None:
            """Backup database."""
            pass

        def restore(self, database: str, backup_file: str) -> None:
            """Restore database from backup."""
            pass

    class User:
        """User operations."""

        def create(self, username: str, email: str) -> None:
            """Create new user."""
            pass

        def delete(self, username: str, force: bool = False) -> None:
            """Delete user."""
            pass
```

Usage:
```bash
admin-tool database backup --database prod --output prod.sql
admin-tool user create --username alice --email alice@example.com
```

### 2. Consistent State Management
For class-based CLIs:
```python
class ApplicationCLI:
    """Application Freyja with consistent state management."""
    
    def __init__(self, config_file: str = "app.config"):
        self.config = self._load_config(config_file)
        self.connection = None
    
    def connect(self, host: str, port: int = 5432) -> None:
        """Establish connection."""
        self.connection = f"{host}:{port}"
        print(f"✅ Connected to {self.connection}")
    
    def disconnect(self) -> None:
        """Close connection."""
        if self.connection:
            print(f"Disconnecting from {self.connection}")
            self.connection = None
        else:
            print("⚠️ Not connected")
```

## Security Best Practices

### 1. Validate Input
```python
def execute_query(query: str, safe_mode: bool = True) -> None:
    """Execute query with safety checks."""
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE']
    
    if safe_mode:
        for keyword in dangerous_keywords:
            if keyword in query.upper():
                print(f"❌ Error: Dangerous operation '{keyword}' blocked in safe mode")
                print("💡 Use --no-safe-mode to allow dangerous operations")
                return 1
```

### 2. Secure Defaults
```python
def create_backup(
    source: str,
    destination: str = "./backups",
    encrypt: bool = True,  # Secure by default
    compression: str = "high"
) -> None:
    """Create backup with secure defaults."""
    pass
```

## See Also

- [Troubleshooting](troubleshooting.md) - Common issues
- [Examples](examples.md) - Real-world patterns
- [Basic Usage](../getting-started/basic-usage.md) - Testing fundamentals

---

**Navigation**: [← Troubleshooting](troubleshooting.md) | [Examples →](examples.md)