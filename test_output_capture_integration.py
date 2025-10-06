#!/usr/bin/env python3
"""Quick integration test for OutputCapture opt-in functionality."""

from freyja import FreyjaCLI

class TestClass:
    """Simple test class for output capture testing."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def say_hello(self, name: str = "World") -> None:
        """Say hello to someone."""
        print(f"Hello, {name}!")
        if self.verbose:
            print("Verbose mode is enabled")

def test_disabled_by_default():
    """Test that output capture is disabled by default."""
    cli = FreyjaCLI(TestClass)
    
    # Should be disabled by default
    assert cli.output_capture is None
    assert cli.get_captured_output() is None
    print("✅ Output capture disabled by default")

def test_opt_in_enabled():
    """Test explicit opt-in functionality."""
    cli = FreyjaCLI(TestClass, capture_output=True)
    
    # Should be enabled when explicitly requested
    assert cli.output_capture is not None
    print("✅ Output capture enabled when opt-in")

def test_dynamic_control():
    """Test dynamic enable/disable functionality."""
    cli = FreyjaCLI(TestClass)
    
    # Start disabled
    assert cli.output_capture is None
    
    # Enable dynamically
    cli.enable_output_capture()
    assert cli.output_capture is not None
    
    # Disable dynamically
    cli.disable_output_capture()
    assert cli.output_capture is None
    
    print("✅ Dynamic control works")

def test_context_manager():
    """Test context manager functionality."""
    cli = FreyjaCLI(TestClass)
    
    # Should start disabled
    assert cli.output_capture is None
    
    # Use context manager
    with cli.capture_output() as capture:
        assert capture is not None
    
    # Should be disabled again after context
    assert cli.output_capture is None
    
    print("✅ Context manager works")

if __name__ == "__main__":
    print("Testing OutputCapture opt-in functionality...")
    
    test_disabled_by_default()
    test_opt_in_enabled()
    test_dynamic_control()
    test_context_manager()
    
    print("\n🎉 All tests passed! OutputCapture opt-in functionality is working correctly.")