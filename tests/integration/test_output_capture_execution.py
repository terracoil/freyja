#!/usr/bin/env python3
"""Test OutputCapture with actual command execution."""

from freyja import FreyjaCLI


class SampleOutputClass:
    """Test class with methods that produce output."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def say_hello(self, name: str = "World") -> None:
        """Say hello to someone."""
        print(f"Hello, {name}!")
        if self.verbose:
            print("Verbose mode is enabled")


def test_capture_execution():
    """Test capturing output during command execution."""
    cli = FreyjaCLI(SampleOutputClass, capture_output=True)

    # Execute a command - this should capture the output
    cli.run(["say-hello", "--name", "Freyja"])

    # Get captured output
    captured = cli.get_captured_output()
    print(f"Captured output: '{captured}'")

    # Should contain the expected output
    assert captured is not None
    assert "Hello, Freyja!" in captured

    print("✅ Output capture during execution works")


def test_no_capture_execution():
    """Test that no capture happens when disabled."""
    cli = FreyjaCLI(SampleOutputClass, capture_output=False)

    # Execute a command - this should NOT capture output
    cli.run(["say-hello", "--name", "Test"])

    # Should be no captured output
    captured = cli.get_captured_output()
    assert captured is None

    print("✅ No capture when disabled works")


def test_context_manager_capture():
    """Test context manager capture with execution."""
    cli = FreyjaCLI(SampleOutputClass)

    # Start with no capture
    assert cli.get_captured_output() is None

    # Use context manager for temporary capture
    with cli.capture_output():
        cli.run(["say-hello", "--name", "Context"])
        captured = cli.get_captured_output()
        assert captured is not None
        assert "Hello, Context!" in captured
        print(f"Context captured: '{captured}'")

    # Should be no capture after context
    assert cli.get_captured_output() is None

    print("✅ Context manager capture works")


if __name__ == "__main__":
    print("Testing OutputCapture with command execution...")

    test_capture_execution()
    test_no_capture_execution()
    test_context_manager_capture()

    print("\n🎉 All execution tests passed!")
