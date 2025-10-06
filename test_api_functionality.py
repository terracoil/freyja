#!/usr/bin/env python3
"""Test the public API functionality of OutputCapture."""

from freyja import FreyjaCLI

class TestClass:
    """Test class for API testing."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def simple_method(self, message: str = "test") -> None:
        """Simple method for testing."""
        print(f"Message: {message}")

def test_api_methods():
    """Test all the public API methods."""
    print("Testing public API methods...")
    
    # Test 1: Default state (disabled)
    cli = FreyjaCLI(TestClass)
    assert cli.output_capture is None
    assert cli.get_captured_output() is None
    assert cli.get_all_captured_output() == {'stdout': None, 'stderr': None, 'stdin': None}
    print("✅ Default disabled state works")
    
    # Test 2: Opt-in enabled
    cli = FreyjaCLI(TestClass, capture_output=True)
    assert cli.output_capture is not None
    print("✅ Opt-in enabled works")
    
    # Test 3: Stream-specific configuration
    cli = FreyjaCLI(TestClass, capture_output=True, capture_stderr=True)
    assert cli.output_capture is not None
    assert cli.output_capture.capture_stdout == True  # default
    assert cli.output_capture.capture_stderr == True  # explicitly set
    print("✅ Stream-specific configuration works")
    
    # Test 4: Dynamic enable/disable
    cli = FreyjaCLI(TestClass)
    assert cli.output_capture is None
    
    cli.enable_output_capture()
    assert cli.output_capture is not None
    
    cli.disable_output_capture()
    assert cli.output_capture is None
    print("✅ Dynamic enable/disable works")
    
    # Test 5: Manual capture and access
    cli = FreyjaCLI(TestClass, capture_output=True)
    
    # Manually capture some output
    with cli.output_capture.capture_output():
        print("Test message")
    
    captured = cli.get_captured_output()
    assert captured is not None
    assert "Test message" in captured
    print("✅ Manual capture and access works")
    
    # Test 6: Clear functionality
    cli.clear_captured_output()
    captured_after_clear = cli.get_captured_output()
    assert captured_after_clear == ""  # Empty but not None since capture is enabled
    print("✅ Clear functionality works")
    
    # Test 7: Context manager
    cli = FreyjaCLI(TestClass)
    assert cli.output_capture is None
    
    with cli.capture_output():
        # Context manager enables capture temporarily
        assert cli.output_capture is not None
        
        # Manually capture output within context
        with cli.output_capture.capture_output():
            print("Context test")
        
        temp_captured = cli.get_captured_output()
        assert "Context test" in temp_captured
    
    # Should be disabled again after context
    assert cli.output_capture is None
    print("✅ Context manager works")

def test_configuration_options():
    """Test various configuration options."""
    print("\nTesting configuration options...")
    
    # Test buffer size and encoding
    cli = FreyjaCLI(
        TestClass, 
        capture_output=True,
        output_capture_config={
            'buffer_size': 2048,
            'encoding': 'utf-8'
        }
    )
    
    assert cli.output_capture is not None
    # Debug: print actual buffer_size
    print(f"Expected: 2048, Actual: {cli.output_capture.buffer_size}")
    assert cli.output_capture.buffer_size == 2048
    assert cli.output_capture.encoding == 'utf-8'
    print("✅ Advanced configuration works")

if __name__ == "__main__":
    test_api_methods()
    test_configuration_options()
    
    print("\n🎉 All API tests passed! OutputCapture public API is working correctly.")