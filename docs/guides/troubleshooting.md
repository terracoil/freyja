# Troubleshooting Guide

[← Back to Help](../help.md) | [🔧 Basic Usage](../getting-started/basic-usage.md)

## Table of Contents
- [Common Error Messages](#common-error-messages)
- [Type Annotation Issues](#type-annotation-issues)
- [Import and Module Problems](#import-and-module-problems)
- [Command Line Argument Issues](#command-line-argument-issues)
- [Performance Issues](#performance-issues)
- [Theme and Display Problems](#theme-and-display-problems)
- [Shell Completion Issues](#shell-completion-issues)
- [Debugging Tips](#debugging-tips)
- [Getting Help](#getting-help)

## Common Error Messages

### "TypeError: missing required argument"

**Error Example:**
```
TypeError: process_file() missing 1 required positional argument: 'input_file'
```

**Cause:** Required parameter not provided on command line.

**Solutions:**
```python
# ✅ Fix 1: Provide the required argument
python script.py process-file --input-file data.txt

# ✅ Fix 2: Make parameter optional with default
def process_file(input_file: str = "default.txt") -> None:
    pass

# ✅ Fix 3: Check your function signature matches usage
def process_file(input_file: str, output_dir: str = "./output") -> None:
    # input_file is required, output_dir is optional
    pass
```

### "AttributeError: 'module' has no attribute..."

**Error Example:**
```
AttributeError: 'module' object has no attribute 'some_function'
```

**Cause:** Function not found in module or marked as private.

**Solutions:**
```python
# ❌ Problem: Private function (starts with _)
def _private_function():
    pass

# ✅ Fix: Make function public
def public_function():
    pass

# ❌ Problem: Function not defined when CLI.from_module() called
if __name__ == '__main__':
    def my_function():  # Defined inside main block
        pass
    cli = CLI.from_module(sys.modules[__name__])

# ✅ Fix: Define function at module level
def my_function():
    pass

if __name__ == '__main__':
    cli = CLI.from_module(sys.modules[__name__])
```

### "ValueError: invalid literal for int()"

**Error Example:**
```
ValueError: invalid literal for int() with base 10: 'abc'
```

**Cause:** Invalid type conversion from command line input.

**Solutions:**
```bash
# ❌ Problem: Passing non-numeric value to int parameter
python script.py process --count abc

# ✅ Fix: Use valid integer
python script.py process --count 10

# ✅ Fix: Check parameter types in function definition
def process(count: int) -> None:  # Expects integer
    pass

# ✅ Fix: Add input validation in function
def process(count: int) -> None:
    if count < 0:
        print("Count must be positive")
        return
    # Process with valid count
```

## Type Annotation Issues

### Missing Type Annotations

**Problem:**
```python
# ❌ No type annotations - will cause errors
def process_data(filename, verbose=False):
    pass
```

**Solution:**
```python
# ✅ Add required type annotations
def process_data(filename: str, verbose: bool = False) -> None:
    pass
```

### Import Errors for Type Hints

**Problem:**
```python
# ❌ List not imported
def process_files(files: List[str]) -> None:
    pass
```

**Solution:**
```python
# ✅ Import required types
from typing import List

def process_files(files: List[str]) -> None:
    pass

# ✅ Python 3.9+ can use built-in list
def process_files(files: list[str]) -> None:  # Python 3.9+
    pass
```

### Optional Type Confusion

**Problem:**
```python
# ❌ Confusing optional parameter handling
def connect(host: Optional[str]) -> None:  # No default value
    pass
```

**Solution:**
```python
# ✅ Proper optional parameter with default
from typing import Optional

def connect(host: Optional[str] = None) -> None:
    if host is None:
        host = "localhost"
    # Connect to host
```

### Complex Type Annotations

**Problem:**
```python
# ❌ Too complex for CLI auto-generation
def process(callback: Callable[[str, int], bool]) -> None:
    pass
```

**Solution:**
```python
# ✅ Simplify to basic types
def process(callback_name: str) -> None:
    """Use callback name to look up function internally."""
    callbacks = {
        'validate': validate_callback,
        'transform': transform_callback
    }
    callback = callbacks.get(callback_name)
    if not callback:
        print(f"Unknown callback: {callback_name}")
        return
    # Use callback
```

## Import and Module Problems

### Module Not Found

**Problem:**
```python
# ❌ Relative import in main script
from .utils import helper_function  # ModuleNotFoundError
```

**Solution:**
```python
# ✅ Use absolute imports or local imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from utils import helper_function

# ✅ Or handle imports inside functions
def process_data(filename: str) -> None:
    from utils import helper_function
    helper_function(filename)
```

### Circular Import Issues

**Problem:**
```
ImportError: cannot import name 'CLI' from partially initialized module
```

**Solution:**
```python
# ✅ Move CLI setup to separate file or use delayed import
def create_cli():
    from auto_cli import CLI
    import sys
    return CLI.from_module(sys.modules[__name__])

if __name__ == '__main__':
    cli = create_cli()
    cli.display()
```

### Auto-CLI-Py Not Installed

**Problem:**
```
ModuleNotFoundError: No module named 'auto_cli'
```

**Solution:**
```bash
# ✅ Install auto-cli-py
pip install auto-cli-py

# ✅ Or install from source
git clone https://github.com/tangledpath/auto-cli-py.git
cd auto-cli-py
pip install -e .
```

## Command Line Argument Issues

### Kebab-Case Conversion Confusion

**Problem:**
```python
def process_data_file(input_file: str) -> None:  # Function name
    pass

# User tries: python script.py process_data_file  # ❌ Won't work
```

**Solution:**
```bash
# ✅ Use kebab-case for command names
python script.py process-data-file --input-file data.txt

# Function parameter names also convert:
# input_file -> --input-file
# max_count -> --max-count
# output_dir -> --output-dir
```

### Boolean Flag Confusion

**Problem:**
```python
def backup(compress: bool = True) -> None:
    pass

# User confusion: How to disable compression?
```

**Solution:**
```bash
# ✅ For bool parameters with True default, use --no-* flag
python script.py backup --no-compress

# ✅ For bool parameters with False default, use flag to enable
def backup(compress: bool = False) -> None:
    pass

# Usage:
python script.py backup --compress  # Enable compression
python script.py backup            # No compression (default)
```

### List Parameter Issues

**Problem:**
```bash
# ❌ User passes single argument expecting list behavior
python script.py process --files "file1.txt file2.txt"  # Treated as one filename
```

**Solution:**
```bash
# ✅ Pass multiple arguments for List parameters
python script.py process --files file1.txt file2.txt file3.txt

# ✅ Each item is a separate argument
python script.py process --files "file with spaces.txt" file2.txt
```

## Performance Issues

### Slow CLI Startup

**Problem:** CLI takes a long time to start up.

**Cause:** Expensive imports or initialization in module.

**Solution:**
```python
# ❌ Expensive operations at module level
import heavy_library
expensive_data = heavy_library.load_large_dataset()

def process(data: str) -> None:
    # Use expensive_data
    pass

# ✅ Lazy loading inside functions
def process(data: str) -> None:
    import heavy_library  # Import only when needed
    expensive_data = heavy_library.load_large_dataset()
    # Use expensive_data
```

### Memory Usage with Large Default Values

**Problem:**
```python
# ❌ Large default values loaded at import time
LARGE_CONFIG = load_huge_configuration()  # Loaded even if not used

def process(config: str = LARGE_CONFIG) -> None:
    pass
```

**Solution:**
```python
# ✅ Use None and lazy loading
def process(config: str = None) -> None:
    if config is None:
        config = load_huge_configuration()  # Only when needed
    # Use config
```

## Theme and Display Problems

### Colors Not Working

**Problem:** CLI output appears without colors.

**Solutions:**
```python
# ✅ Check if colors are explicitly disabled
cli = CLI.from_module(module, no_color=False)  # Ensure colors enabled

# ✅ Check terminal support
# Some terminals don't support colors - test in different terminal

# ✅ Force colors for testing
import os
os.environ['FORCE_COLOR'] = '1'  # Force color output
```

### Text Wrapping Issues

**Problem:** Help text doesn't wrap properly.

**Solutions:**
```python
# ✅ Keep docstrings reasonable length
def my_function(param: str) -> None:
    """
    Short description that fits on one line.
    
    Longer description can span multiple lines but should
    be formatted nicely with proper line breaks.
    """
    pass

# ✅ Check terminal width
# Auto-CLI-Py respects terminal width - try resizing terminal
```

### Unicode/Encoding Issues

**Problem:** Special characters display incorrectly.

**Solutions:**
```python
# ✅ Set proper encoding
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

# ✅ Use ASCII alternatives for broader compatibility
def process(status: str = "✓") -> None:  # ❌ Might cause issues
    pass

def process(status: str = "OK") -> None:  # ✅ Safer
    pass
```

## Shell Completion Issues

### Completion Not Working

**Problem:** Shell completion doesn't work after installation.

**Solutions:**
```bash
# ✅ Reinstall completion
python my_script.py --install-completion

# ✅ Manual setup for bash
python my_script.py --show-completion >> ~/.bashrc
source ~/.bashrc

# ✅ Check shell type
echo $0  # Make sure you're using supported shell (bash, zsh, fish)

# ✅ Check completion script location
# Completion files should be in shell's completion directory
```

### Completion Shows Wrong Options

**Problem:** Completion suggests incorrect or outdated options.

**Solutions:**
```bash
# ✅ Clear completion cache (bash)
hash -r

# ✅ Restart shell
exec $SHELL

# ✅ Reinstall completion
python my_script.py --install-completion --force
```

## Debugging Tips

### Debug CLI Generation

```python
# ✅ Enable verbose output to see what CLI finds
import logging
logging.basicConfig(level=logging.DEBUG)

from auto_cli import CLI
import sys

cli = CLI.from_module(sys.modules[__name__])
print("Found functions:", [name for name in dir(sys.modules[__name__]) 
                          if callable(getattr(sys.modules[__name__], name))])
```

### Test Functions Independently

```python
# ✅ Test your functions directly before adding CLI
def my_function(param: str, count: int = 5) -> None:
    print(f"Param: {param}, Count: {count}")

if __name__ == '__main__':
    # Test function directly first
    my_function("test", 3)  # Direct call works?
    
    # Then test CLI
    from auto_cli import CLI
    import sys
    cli = CLI.from_module(sys.modules[__name__])
    cli.display()
```

### Check Function Signatures

```python
import inspect

def debug_function_signatures(module):
    """Debug helper to check function signatures."""
    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and not name.startswith('_'):
            try:
                sig = inspect.signature(obj)
                print(f"{name}: {sig}")
                for param_name, param in sig.parameters.items():
                    print(f"  {param_name}: {param.annotation}")
            except Exception as e:
                print(f"Error with {name}: {e}")

if __name__ == '__main__':
    import sys
    debug_function_signatures(sys.modules[__name__])
```

### Minimal Reproduction

When reporting issues, create a minimal example:

```python
# minimal_example.py
from auto_cli import CLI
import sys

def simple_function(text: str) -> None:
    """Simple function for testing."""
    print(f"Text: {text}")

if __name__ == '__main__':
    cli = CLI.from_module(sys.modules[__name__])
    cli.display()
```

## Getting Help

### Check Version

```bash
python -c "import auto_cli; print(auto_cli.__version__)"
```

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(levelname)s: %(message)s')
```

### Report Issues

When reporting issues, include:

1. **Auto-CLI-Py version**
2. **Python version** (`python --version`)
3. **Operating system**
4. **Minimal code example** that reproduces the issue
5. **Complete error message** with traceback
6. **Expected vs actual behavior**

### Community Resources

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Latest guides and API reference
- **Examples**: Check `mod_example.py` and `cls_example.py`

## See Also

- **[Type Annotations](../features/type-annotations.md)** - Detailed type system guide
- **[Basic Usage](../getting-started/basic-usage.md)** - Core concepts and patterns  
- **[API Reference](../reference/api.md)** - Complete method reference
- **[FAQ](../faq.md)** - Frequently asked questions

---

**Navigation**: [← Help Hub](../help.md) | [Basic Usage →](../getting-started/basic-usage.md)  
**Examples**: [Module Example](../../mod_example.py) | [Class Example](../../cls_example.py)