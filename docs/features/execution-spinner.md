**→ [Back to Features](README.md) | [Home](../README.md)**

# 🔄 Execution Spinner
<img src="https://github.com/terracoil/freyja/raw/main/docs/freyja-github.jpg" alt="Freyja" title="Freyja" height="200"/>

## Overview
The ExecutionSpinner provides visual feedback during command execution, displaying a spinning animation with detailed status information about the currently running command. This feature enhances user experience by showing that the CLI is actively processing commands, especially for long-running operations.

**Key Benefits:**
- **Visual Feedback**: Animated spinner shows the CLI is working
- **Command Context**: Displays the command being executed with its arguments
- **Verbose Mode Support**: Adapts behavior based on verbosity settings
- **Thread-Safe**: Properly handles concurrent updates
- **Customizable Status**: Commands can augment status with custom messages

## How It Works

The ExecutionSpinner operates in two modes:

### Standard Mode (Non-Verbose)
- Displays an animated spinner character that rotates through: `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`
- Shows the executing command name and its arguments
- Updates in place without scrolling the terminal
- Automatically cleans up when command completes

### Verbose Mode
- Prints the execution status once without animation
- Preserves all output for debugging and logging
- Applies theme styling when available

## Usage Examples

### Basic Command Execution

When you run a Freyja command, the spinner automatically displays:

```bash
# Running a command shows the spinner
python my_cli.py process-data input.csv --format json

# Spinner displays:
⠹ Executing process-data [positional:0:input.csv, format:json]
```

### Hierarchical Commands

For inner class commands, the spinner shows the full command path:

```bash
# Running an inner class command
python project_manager.py database migrate --target-version 2.0

# Spinner displays:
⠸ Executing database:migrate [target-version:2.0]
```

### With Global and Sub-Global Arguments

The spinner intelligently categorizes and displays different argument types:

```bash
# Complex command with multiple argument types
python project_manager.py --debug --config prod.json \
  database migrate --connection-timeout 60 \
  --target-version 2.0 --dry-run

# Spinner displays:
⠼ Executing database:migrate [global:debug:True, global:config:prod.json, database:connection-timeout:60, ... +2 more]
```

## Custom Status Messages

Commands can augment the spinner with custom status messages using the `augment_status` method:

```python
class DataProcessor:
    def process_large_file(self, filename: str, chunk_size: int = 1024):
        """Process a large file in chunks."""
        # The spinner context is available during execution
        spinner = self._get_spinner()  # Implementation detail
        
        total_chunks = calculate_chunks(filename, chunk_size)
        for i, chunk in enumerate(read_chunks(filename, chunk_size)):
            # Update spinner with progress
            spinner.augment_status(f"Processing chunk {i+1}/{total_chunks}")
            process_chunk(chunk)
```

This results in:
```
⠧ Executing process-large-file [positional:0:data.csv, chunk-size:1024] → Processing chunk 42/100
```

## Implementation Details

### CommandContext Structure

The spinner uses a `CommandContext` dataclass to organize execution information:

```python
@dataclass
class CommandContext:
    """Context for command execution display."""
    namespace: str | None = None          # For namespaced commands
    command: str = ""                      # Main command name
    subcommand: str | None = None         # For hierarchical commands
    global_args: dict[str, Any]           # Global CLI arguments
    group_args: dict[str, Any]            # Sub-global arguments
    command_args: dict[str, Any]          # Command-specific arguments
    positional_args: list[Any]            # Positional arguments
    custom_status: str | None = None      # Custom status message
```

### Display Format

Arguments are formatted with their context:
- **Positional**: `positional:index:value`
- **Global**: `global:name:value`
- **Group**: `groupname:name:value`
- **Command**: `commandname:name:value`

### Thread Safety

The spinner runs in a separate thread to avoid blocking command execution:
- Uses threading locks for safe status updates
- Properly cleans up on command completion or interruption
- Handles terminal cleanup to prevent display artifacts

## Configuration

### Enabling/Disabling

The spinner is automatically enabled for all Freyja commands. Control its behavior through:

```python
cli = FreyjaCLI(
    MyClass,
    verbose=True  # Disables animation, shows static status
)
```

### Styling

The spinner respects the current theme's `command_output` style:

```python
# In verbose mode, output is styled according to theme
theme.command_output = TextStyle(
    color="blue",
    bold=True
)
```

## Best Practices

1. **Long-Running Operations**: The spinner is especially valuable for commands that take more than a second to complete

2. **Progress Updates**: Use `augment_status()` to provide meaningful progress information:
   ```python
   spinner.augment_status(f"Processed {count}/{total} records")
   ```

3. **Error Handling**: The spinner automatically cleans up on errors, ensuring the terminal remains usable

4. **Testing**: In automated tests, use verbose mode to capture all output:
   ```bash
   python my_cli.py --verbose command
   ```

## Limitations

- **Terminal Support**: Requires a terminal that supports ANSI escape codes
- **Windows**: May require Windows Terminal or similar modern terminal emulator
- **CI/CD**: Automatically detects non-interactive environments and adjusts behavior

## See Also

- **[🎨 Themes](themes.md)** - Customize spinner appearance with themes
- **[⚠️ Error Handling](error-handling.md)** - How errors interact with the spinner
- **[📤 Output Capture](output-capture.md)** - Capturing output with spinner active
- **[🔧 CLI Reference](../reference/api.md)** - Technical API documentation

---

**Navigation**: [← Output Capture](output-capture.md) | [Themes →](themes.md)
