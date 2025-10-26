#!/usr/bin/env python3
"""Simple test of OutputCapture functionality."""

from freyja.utils.output_capture import OutputCapture


def test_basic_capture():
    """Test basic OutputCapture functionality."""
    capture = OutputCapture(capture_stdout=True)

    with capture.capture_output():
        print("This should be captured")

    # Get output after context manager
    output = capture.get_output("stdout")
    print(f"Captured: '{output}'")
    assert "This should be captured" in output
    print("✅ Basic capture works")


def test_context_manager_preserves_output():
    """Test that context manager preserves output for later access."""
    capture = OutputCapture(capture_stdout=True)

    # Use context manager
    with capture.capture_output():
        print("Test message")

    # Output should still be available after context
    output = capture.get_output("stdout")
    print(f"After context: '{output}'")
    assert output is not None
    assert "Test message" in output
    print("✅ Context manager preserves output")


if __name__ == "__main__":
    print("Testing basic OutputCapture...")
    test_basic_capture()
    test_context_manager_preserves_output()
    print("🎉 Basic tests passed!")
