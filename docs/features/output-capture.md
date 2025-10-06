# 📝 Output Capture

[↑ Documentation Hub](../README.md) | [← Features](README.md)

Control and capture command output programmatically with Freyja's built-in OutputCapture system. Perfect for testing, logging, processing command results, or building CLIs that need to intercept and manipulate their own output.

## Table of Contents
* [🎯 Overview](#-overview)
* [🚀 Quick Start](#-quick-start)
* [⚙️ Configuration](#️-configuration)
* [🔧 API Reference](#-api-reference)
* [💡 Use Cases](#-use-cases)
* [🧪 Testing Integration](#-testing-integration)
* [⚠️ Performance Notes](#️-performance-notes)

## 🎯 Overview

OutputCapture is an **opt-in** feature that allows your Freyja CLI to intercept and capture stdout, stderr, and stdin streams during command execution. This enables powerful scenarios like:

- **Testing CLI output** without subprocess calls
- **Processing command results** programmatically
- **Logging and monitoring** command execution
- **Building meta-CLIs** that analyze other command output

### Key Features

- **🔒 Opt-in Design** - Disabled by default for zero performance overhead
- **🎛️ Selective Streams** - Capture stdout, stderr, stdin individually or together
- **🧠 Smart Context** - Temporary capture with context managers
- **📊 Full Access** - Complete API for enable/disable/clear operations
- **⚡ Zero Overhead** - No performance impact when disabled

## 🚀 Quick Start

### Basic Output Capture

```python
from freyja import FreyjaCLI

class LogProcessor:
    """Process log files with output capture."""
    
    def process_logs(self, input_file: str, verbose: bool = False) -> None:
        """Process log file and print results."""
        print(f"Processing {input_file}")
        print(f"Found 42 errors")
        if verbose:
            print("Detailed processing complete")

# Enable output capture at initialization
cli = FreyjaCLI(LogProcessor, capture_output=True)

# Run command and access captured output
cli.run(["process-logs", "app.log", "--verbose"])
captured = cli.get_captured_output()
print(f"Captured: {captured}")
# Output: "Processing app.log\nFound 42 errors\nDetailed processing complete\n"
```

### Context Manager for Temporary Capture

```python
# Capture disabled by default
cli = FreyjaCLI(LogProcessor)

# Temporarily enable capture for specific commands
with cli.capture_output():
    cli.run(["process-logs", "error.log"])
    captured = cli.get_captured_output()
    print(f"Temporary capture: {captured}")

# Output capture automatically disabled after context
```

### Dynamic Control

```python
cli = FreyjaCLI(LogProcessor)  # Starts disabled

# Enable when needed
cli.enable_output_capture(capture_stderr=True)
cli.run(["process-logs", "debug.log"])

# Access and clear
stdout_content = cli.get_captured_output('stdout')
stderr_content = cli.get_captured_output('stderr')
cli.clear_captured_output()

# Disable when done
cli.disable_output_capture()
```

## ⚙️ Configuration

### Initialization Options

```python
# Enable with default settings (stdout only)
cli = FreyjaCLI(MyClass, capture_output=True)

# Capture multiple streams
cli = FreyjaCLI(MyClass, 
                capture_output=True,
                capture_stdout=True,
                capture_stderr=True,
                capture_stdin=False)  # default

# Advanced configuration
cli = FreyjaCLI(MyClass,
                capture_output=True,
                output_capture_config={
                    'buffer_size': 2048,      # 2KB buffer
                    'encoding': 'utf-8',      # text encoding
                    'errors': 'replace'       # encoding error handling
                })
```

### Dynamic Configuration

```python
# Enable with custom settings
cli.enable_output_capture(
    capture_stdout=True,
    capture_stderr=True,
    capture_stdin=False
)

# Context manager with custom settings
with cli.capture_output(capture_stderr=True, buffer_size=4096):
    cli.run(["my-command"])
    result = cli.get_captured_output()
```

### Stream-Specific Capture

```python
# Capture only stderr for error analysis
cli = FreyjaCLI(MyClass, 
                capture_output=True,
                capture_stdout=False,
                capture_stderr=True)

cli.run(["error-prone-command"])
errors = cli.get_captured_output('stderr')
if errors:
    print(f"Command errors: {errors}")
```

## 🔧 API Reference

### Properties

#### `cli.output_capture`
Returns the current `OutputCapture` instance or `None` if disabled.

```python
if cli.output_capture:
    print("Output capture is enabled")
    print(f"Capturing stdout: {cli.output_capture.capture_stdout}")
    print(f"Capturing stderr: {cli.output_capture.capture_stderr}")
```

### Methods

#### `enable_output_capture(**kwargs)`
Enable output capture with optional configuration.

```python
cli.enable_output_capture()  # Default settings
cli.enable_output_capture(capture_stderr=True, buffer_size=2048)
```

#### `disable_output_capture()`
Disable output capture and cleanup resources.

```python
cli.disable_output_capture()
```

#### `get_captured_output(stream='stdout')`
Get captured content for a specific stream.

```python
stdout_content = cli.get_captured_output()         # defaults to 'stdout'
stderr_content = cli.get_captured_output('stderr')
stdin_content = cli.get_captured_output('stdin')
```

**Returns:** `str` content or `None` if stream not captured.

#### `get_all_captured_output()`
Get all captured content as a dictionary.

```python
all_output = cli.get_all_captured_output()
# Returns: {'stdout': '...', 'stderr': '...', 'stdin': None}
```

#### `clear_captured_output()`
Clear all captured content buffers.

```python
cli.clear_captured_output()  # Resets all buffers to empty
```

#### `capture_output(**kwargs)` [Context Manager]
Temporarily enable output capture.

```python
with cli.capture_output() as capture:
    cli.run(["my-command"])
    result = cli.get_captured_output()
# Automatically restores previous capture state
```

## 💡 Use Cases

### 1. CLI Testing

```python
import pytest

def test_log_processing():
    """Test log processing output without subprocess."""
    cli = FreyjaCLI(LogProcessor, capture_output=True)
    
    # Test normal processing
    cli.run(["process-logs", "test.log"])
    output = cli.get_captured_output()
    
    assert "Processing test.log" in output
    assert "Found" in output and "errors" in output

def test_error_handling():
    """Test error output capture."""
    cli = FreyjaCLI(LogProcessor, capture_output=True, capture_stderr=True)
    
    # Test error case
    with pytest.raises(SystemExit):
        cli.run(["process-logs", "nonexistent.log"])
    
    errors = cli.get_captured_output('stderr')
    assert "File not found" in errors
```

### 2. Command Result Processing

```python
class DataPipeline:
    """Process data with result analysis."""
    
    def analyze_data(self, dataset: str) -> None:
        """Analyze dataset and print statistics."""
        # Your analysis logic here
        print(f"Dataset: {dataset}")
        print(f"Records: 1000")
        print(f"Columns: 5")
        print(f"Quality Score: 0.95")

# Capture and parse results
cli = FreyjaCLI(DataPipeline, capture_output=True)
cli.run(["analyze-data", "sales.csv"])

output = cli.get_captured_output()
lines = output.strip().split('\n')
stats = {}
for line in lines[1:]:  # Skip first line
    key, value = line.split(': ')
    stats[key] = value

print(f"Analysis complete: {stats}")
# Output: Analysis complete: {'Records': '1000', 'Columns': '5', 'Quality Score': '0.95'}
```

### 3. Meta-CLI Development

```python
class CLIAnalyzer:
    """Analyze other CLI tools."""
    
    def run_tool(self, tool_name: str, *args) -> None:
        """Run external tool and analyze output."""
        # Simulate running external tool
        print(f"Running {tool_name} with args: {args}")
        print("Tool output would be here...")

# Build CLI that analyzes other CLIs
cli = FreyjaCLI(CLIAnalyzer)

# Capture output from specific commands
with cli.capture_output() as capture:
    cli.run(["run-tool", "mytool", "--verbose"])
    tool_output = cli.get_captured_output()
    
    # Analyze the output
    if "error" in tool_output.lower():
        print("Tool reported errors")
    else:
        print("Tool executed successfully")
```

### 4. Logging and Monitoring

```python
import logging

class MonitoredCLI:
    """CLI with built-in monitoring."""
    
    def deploy_app(self, app_name: str, environment: str = "staging") -> None:
        """Deploy application with monitoring."""
        print(f"Deploying {app_name} to {environment}")
        print("Deployment successful")

# Setup with monitoring
cli = FreyjaCLI(MonitoredCLI, capture_output=True)

# Run command with monitoring
cli.run(["deploy-app", "web-service", "--environment", "production"])

# Log the output
output = cli.get_captured_output()
logging.info(f"Deployment output: {output}")

# Clear for next command
cli.clear_captured_output()
```

## 🧪 Testing Integration

### Pytest Integration

```python
import pytest
from freyja import FreyjaCLI

class TestCommandOutput:
    """Test suite with output capture."""
    
    @pytest.fixture
    def cli_with_capture(self):
        """Fixture providing CLI with output capture enabled."""
        return FreyjaCLI(MyClass, capture_output=True, capture_stderr=True)
    
    def test_successful_command(self, cli_with_capture):
        """Test successful command output."""
        cli_with_capture.run(["process-data", "input.txt"])
        
        output = cli_with_capture.get_captured_output()
        assert "Processing complete" in output
        
        # No errors should be captured
        errors = cli_with_capture.get_captured_output('stderr')
        assert errors == ""
    
    def test_error_command(self, cli_with_capture):
        """Test error command output."""
        with pytest.raises(SystemExit):
            cli_with_capture.run(["invalid-command"])
        
        errors = cli_with_capture.get_captured_output('stderr')
        assert "Error:" in errors
    
    def test_verbose_output(self, cli_with_capture):
        """Test verbose mode output."""
        cli_with_capture.run(["process-data", "input.txt", "--verbose"])
        
        output = cli_with_capture.get_captured_output()
        assert "Detailed processing" in output
        assert "Debug information" in output
```

### Unittest Integration

```python
import unittest
from freyja import FreyjaCLI

class TestCLIOutput(unittest.TestCase):
    """Test CLI output capture with unittest."""
    
    def setUp(self):
        """Setup CLI with output capture."""
        self.cli = FreyjaCLI(MyClass, capture_output=True)
    
    def tearDown(self):
        """Cleanup after each test."""
        if self.cli.output_capture:
            self.cli.clear_captured_output()
    
    def test_command_output(self):
        """Test command produces expected output."""
        self.cli.run(["hello", "--name", "World"])
        
        output = self.cli.get_captured_output()
        self.assertIn("Hello, World!", output)
    
    def test_multiple_commands(self):
        """Test multiple commands accumulate output."""
        self.cli.run(["hello", "--name", "Alice"])
        self.cli.run(["hello", "--name", "Bob"])
        
        output = self.cli.get_captured_output()
        self.assertIn("Hello, Alice!", output)
        self.assertIn("Hello, Bob!", output)
```

## ⚠️ Performance Notes

### Zero-Overhead Design

Output capture is designed with performance in mind:

- **Default Disabled**: No performance impact when `capture_output=False`
- **Lazy Initialization**: Capture objects created only when needed
- **Minimal Memory**: Efficient buffer management with configurable sizes
- **Quick Enable/Disable**: Fast switching between capture modes

### Memory Management

```python
# Configure buffer size for memory-conscious applications
cli = FreyjaCLI(MyClass,
                capture_output=True,
                output_capture_config={
                    'buffer_size': 1024  # 1KB buffer instead of default 1MB
                })

# Clear buffers regularly for long-running applications
for i in range(1000):
    cli.run(["process-item", str(i)])
    if i % 100 == 0:  # Clear every 100 items
        result = cli.get_captured_output()
        process_result(result)
        cli.clear_captured_output()
```

### Best Practices

1. **Use Context Managers** for temporary capture to ensure cleanup
2. **Clear Buffers Regularly** in long-running applications
3. **Capture Only What You Need** - don't capture stderr if you only need stdout
4. **Configure Buffer Sizes** appropriately for your use case
5. **Disable When Done** to free resources immediately

---

**🎯 Ready to capture your CLI output?** Start with the [Quick Start](#-quick-start) examples and explore the powerful testing and monitoring capabilities!