"""Regression tests for output capture and display functionality."""

import sys
from unittest.mock import patch

from freyja import FreyjaCLI


class TestOutputRegression:
    """Test cases to prevent regression of output capture issues."""

    def test_command_output_is_displayed_correctly(self, capsys):
        """
        Regression test: Ensure command output is displayed to users.

        This test prevents regression of the issue where spinner and output capture
        would interfere with displaying the actual command output to users.
        """

        class SimpleClass:
            def __init__(self, config: str = "default.json"):
                self.config = config

            def print_message(self, message: str) -> str:
                """Print a message and return it."""
                print(f"Message: {message}")
                print(f"Config: {self.config}")
                return f"Processed: {message}"

        cli = FreyjaCLI(SimpleClass, title="Test CLI")

        # Mock sys.argv to simulate command execution
        with patch.object(sys, "argv", ["test_cli", "print-message", "hello_world"]):
            result = cli.run()

        # Command should execute successfully
        assert result == "Processed: hello_world"

        # Capture what was actually printed to stdout
        captured = capsys.readouterr()

        # The actual command output should be visible (not just spinner)
        assert "Message: hello_world" in captured.out
        assert "Config: default.json" in captured.out

    def test_hierarchical_command_output_displayed(self, capsys):
        """
        Regression test: Ensure hierarchical command output is displayed correctly.

        Tests that inner class methods also display their output properly.
        """

        class DataProcessor:
            def __init__(self, config: str = "default.json"):
                self.config = config

            class FileOps:
                def __init__(self, parent, workspace: str = "./data"):
                    self.parent = parent
                    self.workspace = workspace

                def process_file(self, filename: str) -> str:
                    """Process a file and show output."""
                    print(f"Processing file: {filename}")
                    print(f"Workspace: {self.workspace}")
                    print(f"Config: {self.parent.config}")
                    return f"Processed {filename}"

        cli = FreyjaCLI(DataProcessor, title="Data Processor CLI")

        with patch.object(sys, "argv", ["data_cli", "file-ops", "process-file", "test.txt"]):
            result = cli.run()

        assert result == "Processed test.txt"

        captured = capsys.readouterr()

        # Verify the actual command output is displayed
        assert "Processing file: test.txt" in captured.out
        assert "Workspace: ./data" in captured.out
        assert "Config: default.json" in captured.out

    def test_stderr_output_displayed(self, capsys):
        """
        Regression test: Ensure stderr output is also displayed correctly.
        """

        class TestClass:
            def __init__(self, config: str = "default.json"):
                self.config = config

            def method_with_warnings(self, name: str) -> str:
                """Method that produces both stdout and stderr."""
                print(f"Processing {name}")
                print(f"Warning: Using default config for {name}", file=sys.stderr)
                return f"Done with {name}"

        cli = FreyjaCLI(TestClass, title="Test CLI")

        with patch.object(sys, "argv", ["test_cli", "method-with-warnings", "testfile"]):
            result = cli.run()

        assert result == "Done with testfile"

        captured = capsys.readouterr()

        # Both stdout and stderr should be visible
        assert "Processing testfile" in captured.out
        assert "Warning: Using default config for testfile" in captured.err

    def test_no_output_capture_interference(self, capsys):
        """
        Regression test: Ensure output capture doesn't interfere with normal output.

        This specifically tests that the output capture system doesn't
        'swallow' or hide the actual command output from users.
        """

        class VerboseClass:
            def __init__(self, verbose: bool = False):
                self.verbose = verbose

            def chatty_method(self, name: str) -> str:
                """Method that produces multiple lines of output."""
                print(f"Starting processing of {name}")
                if self.verbose:
                    print("Verbose: Loading configuration")
                    print("Verbose: Initializing components")
                print(f"Step 1: Analyzing {name}")
                print(f"Step 2: Processing {name}")
                print(f"Step 3: Finalizing {name}")
                print(f"Completed processing of {name}")
                return f"Result: {name} processed"

        cli = FreyjaCLI(VerboseClass, title="Verbose CLI")

        # Test with verbose flag
        with patch.object(sys, "argv", ["test_cli", "--verbose", "chatty-method", "testfile"]):
            result = cli.run()

        assert result == "Result: testfile processed"

        captured = capsys.readouterr()

        # All output lines should be visible
        expected_lines = [
            "Starting processing of testfile",
            "Verbose: Loading configuration",
            "Verbose: Initializing components",
            "Step 1: Analyzing testfile",
            "Step 2: Processing testfile",
            "Step 3: Finalizing testfile",
            "Completed processing of testfile",
        ]

        for line in expected_lines:
            assert (
                line in captured.out
            ), f"Expected line '{line}' not found in output: {captured.out}"

    def test_return_value_with_print_statements(self, capsys):
        """
        Regression test: Ensure return values work correctly alongside print statements.
        """

        class MixedOutputClass:
            def __init__(self, config: str = "test.conf"):
                self.config = config

            def mixed_output_method(self, input_value: str) -> dict:
                """Method that both prints and returns structured data."""
                print(f"Input received: {input_value}")
                print(f"Using config: {self.config}")

                result = {"input": input_value, "config": self.config, "status": "success"}

                print("Processing complete")
                return result

        cli = FreyjaCLI(MixedOutputClass, title="Mixed Output CLI")

        with patch.object(sys, "argv", ["test_cli", "mixed-output-method", "test123"]):
            result = cli.run()

        # Return value should be preserved
        expected_result = {"input": "test123", "config": "test.conf", "status": "success"}
        assert result == expected_result

        captured = capsys.readouterr()

        # Print statements should also be visible
        assert "Input received: test123" in captured.out
        assert "Using config: test.conf" in captured.out
        assert "Processing complete" in captured.out

    def test_output_timing_with_spinner(self, capsys):
        """
        Regression test: Ensure output timing works correctly with spinner.

        This tests that output appears at the right time and isn't delayed
        or interfered with by the spinner animation.
        """

        class TimingClass:
            def __init__(self, delay: bool = False):
                self.delay = delay

            def immediate_output(self, message: str) -> str:
                """Method that should show output immediately."""
                print(f"Immediate: {message}")
                return f"Done: {message}"

        cli = FreyjaCLI(TimingClass, title="Timing Test CLI")

        with patch.object(sys, "argv", ["test_cli", "immediate-output", "test_message"]):
            result = cli.run()

        assert result == "Done: test_message"

        captured = capsys.readouterr()

        # Output should be present and not delayed
        assert "Immediate: test_message" in captured.out
