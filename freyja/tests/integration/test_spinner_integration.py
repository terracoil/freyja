"""Integration tests for spinner functionality with CLI execution."""

import sys
import time
from unittest.mock import patch

import pytest

from freyja import FreyjaCLI


class TestSpinnerIntegration:
    """Test spinner integration with FreyjaCLI execution."""

    def test_simple_command_with_spinner(self, capsys):
        """Test simple command execution shows spinner."""

        class SimpleClass:
            """Test helper class for simple CLI operations."""
            def __init__(self, config: str = "default.json"):
                self.config = config

            def test_method(self, name: str) -> str:
                """Test method."""
                return f"Processed {name}"

        cli = FreyjaCLI(SimpleClass, title="Test CLI")

        # Mock sys.argv to simulate command execution
        with patch.object(sys, "argv", ["test_cli", "test-method", "testfile"]):
            result = cli.run()

        assert result == "Processed testfile"

    def test_hierarchical_command_with_spinner(self):
        """Test hierarchical command execution with spinner."""

        class DataProcessor:
            """Test helper class for data processing operations."""
            def __init__(self, config: str = "default.json"):
                self.config = config

            class FileOps:
                """Inner class for file operations."""
                def __init__(self, parent, workspace: str = "./data"):
                    self.parent = parent
                    self.workspace = workspace

                def process(self, filename: str) -> str:
                    """Process a file."""
                    return f"Processed {filename} in {self.workspace}"

        cli = FreyjaCLI(DataProcessor, title="Data Processor CLI")

        with patch.object(sys, "argv", ["data_cli", "file-ops", "process", "data.csv"]):
            result = cli.run()

        assert result == "Processed data.csv in ./data"

    def test_command_with_augment_status(self):
        """Test command that uses augment_status functionality."""

        class TestClass:
            """Test helper class for status updates."""
            def __init__(self, config: str = "default.json"):
                self.config = config

            def process_with_status(self, name: str) -> str:
                """Process with status updates."""
                if hasattr(self, "augment_status"):
                    self.augment_status("Loading configuration")
                    time.sleep(0.01)  # Brief pause to show status
                    self.augment_status("Processing data")
                    time.sleep(0.01)
                    self.augment_status("Finalizing")
                    time.sleep(0.01)

                return f"Completed processing {name}"

        cli = FreyjaCLI(TestClass, title="Test CLI")

        with patch.object(sys, "argv", ["test_cli", "process-with-status", "testfile"]):
            result = cli.run()

        assert result == "Completed processing testfile"

    def test_command_with_verbose_output(self, capsys):
        """Test command execution with verbose output capture."""

        class TestClass:
            """Test helper class for verbose output testing."""
            def __init__(self, verbose: bool = False):
                self.verbose = verbose

            def chatty_method(self, name: str) -> str:
                """Method that produces output."""
                print(f"Starting processing of {name}")
                print(f"Step 1: Loading {name}")
                print(f"Step 2: Validating {name}")
                print(f"Step 3: Processing {name}")
                print(f"Completed processing of {name}")
                return f"Done with {name}"

        cli = FreyjaCLI(TestClass, title="Test CLI")

        # Test with verbose flag
        with patch.object(sys, "argv", ["test_cli", "--verbose", "chatty-method", "testfile"]):
            result = cli.run()

        assert result == "Done with testfile"

    def test_command_with_error_output(self):
        """Test command that produces stderr output."""

        class TestClass:
            """Test helper class for stderr output testing."""
            def __init__(self, config: str = "default.json"):
                self.config = config

            def method_with_warnings(self, name: str) -> str:
                """Method that produces warnings."""
                print(f"Warning: Processing {name} with default config", file=sys.stderr)
                print(f"Info: Using config {self.config}", file=sys.stderr)
                return f"Processed {name}"

        cli = FreyjaCLI(TestClass, title="Test CLI")

        with patch.object(sys, "argv", ["test_cli", "method-with-warnings", "testfile"]):
            result = cli.run()

        assert result == "Processed testfile"

    def test_command_context_extraction_simple(self):
        """Test command context is extracted correctly for simple commands."""

        class TestClass:
            """Test helper class for command context extraction."""
            def __init__(self, global_param: str = "global_value", debug: bool = False):
                self.global_param = global_param
                self.debug = debug

            def test_method(self, cmd_param: str, optional_param: str = "default") -> None:
                """Test method with parameters."""
                # We can't directly test the CommandContext extraction here,
                # but we ensure the command executes successfully with spinner
                pass

        cli = FreyjaCLI(TestClass, title="Test CLI")

        with patch.object(
            sys,
            "argv",
            [
                "test_cli",
                "--global-param",
                "test_global",
                "--debug",
                "test-method",
                "required_value",
                "--optional-param",
                "test_optional",
            ],
        ):
            result = cli.run()

        assert result is None  # Method returns None

    def test_command_context_extraction_hierarchical(self):
        """Test command context extraction for hierarchical commands."""

        class DataProcessor:
            """Test helper class for hierarchical command context extraction."""
            def __init__(self, config: str = "default.json", verbose: bool = False):
                self.config = config
                self.verbose = verbose

            class Operations:
                """Inner class for operations."""
                def __init__(self, parent, workspace: str = "./data", backup: bool = True):
                    self.parent = parent
                    self.workspace = workspace
                    self.backup = backup

                def process_file(self, filename: str, format_type: str = "csv") -> None:
                    """Process file with all parameter types."""
                    pass

        cli = FreyjaCLI(DataProcessor, title="Data Processor CLI")

        # Test with all parameter types: global, sub-global, command
        with patch.object(
            sys,
            "argv",
            [
                "data_cli",
                "--config",
                "prod.json",
                "--verbose",
                "operations",
                "--workspace",
                "/tmp/data",  # noqa: S108 # acceptable in tests
                "--backup",
                "process-file",
                "data.csv",
                "--format-type",
                "json",
            ],
        ):
            result = cli.run()

        assert result is None

    def test_spinner_with_theme_integration(self):
        """Test spinner works with theme system."""

        class TestClass:
            """Test helper class for theme integration."""
            def __init__(self, config: str = "default.json"):
                self.config = config

            def themed_method(self, name: str) -> str:
                """Method to test with theme."""
                return f"Themed processing of {name}"

        # Test with theme
        from freyja.theme.defaults import create_default_theme

        theme = create_default_theme()

        cli = FreyjaCLI(TestClass, title="Test CLI", theme=theme)

        with patch.object(sys, "argv", ["test_cli", "themed-method", "testfile"]):
            result = cli.run()

        assert result == "Themed processing of testfile"

    def test_spinner_handles_command_exceptions(self):
        """Test spinner handles command execution errors gracefully."""

        class TestClass:
            """Test helper class for exception handling."""
            def __init__(self, config: str = "default.json"):
                self.config = config

            def failing_method(self, name: str) -> None:
                """Method that raises an exception."""
                raise ValueError(f"Failed to process {name}")

        cli = FreyjaCLI(TestClass, title="Test CLI")

        with patch.object(sys, "argv", ["test_cli", "failing-method", "testfile"]):
            # Should not crash, but return error code
            result = cli.run()

        assert result == 1  # Error code

    def test_multiple_command_executions(self):
        """Test multiple command executions work independently."""

        class TestClass:
            """Test helper class for multiple command executions."""
            def __init__(self, config: str = "default.json"):
                self.config = config

            def method_one(self, name: str) -> str:
                """First test method."""
                return f"Method one: {name}"

            def method_two(self, name: str) -> str:
                """Second test method."""
                return f"Method two: {name}"

        cli = FreyjaCLI(TestClass, title="Test CLI")

        # First execution
        with patch.object(sys, "argv", ["test_cli", "method-one", "test1"]):
            result1 = cli.run()

        # Second execution
        with patch.object(sys, "argv", ["test_cli", "method-two", "test2"]):
            result2 = cli.run()

        assert result1 == "Method one: test1"
        assert result2 == "Method two: test2"

    def test_spinner_respects_no_color_flag(self):
        """Test spinner respects --no-color flag."""

        class TestClass:
            """Test helper class for no-color flag testing."""
            def __init__(self, config: str = "default.json"):
                self.config = config

            def test_method(self, name: str) -> str:
                """Test method."""
                return f"Processed {name}"

        cli = FreyjaCLI(TestClass, title="Test CLI")

        with patch.object(sys, "argv", ["test_cli", "--no-color", "test-method", "testfile"]):
            result = cli.run()

        assert result == "Processed testfile"

    def test_completion_mode_bypasses_spinner(self):
        """Test that completion mode doesn't trigger spinner."""

        class TestClass:
            """Test helper class for completion mode testing."""
            def __init__(self, config: str = "default.json"):
                self.config = config

            def test_method(self, name: str) -> str:
                """Test method."""
                return f"Processed {name}"

        cli = FreyjaCLI(TestClass, title="Test CLI")

        # Mock completion environment
        with (
            patch.dict("os.environ", {"_FREYJA_COMPLETE": "bash"}),
            patch.object(sys, "argv", ["test_cli", "test-method"]),
        ):

            # Should handle completion request without error
            with pytest.raises(SystemExit):
                cli.run()

    def test_sub_global_arguments_integration(self):
        """Test that sub-global arguments work correctly with spinner."""

        class ProjectManager:
            """Test helper class for sub-global arguments integration."""
            def __init__(self, config: str = "config.json"):
                self.config = config

            class FileOps:
                """Inner class for file operations."""
                def __init__(self, parent, workspace: str = "./files", backup: bool = False):
                    self.parent = parent
                    self.workspace = workspace
                    self.backup = backup

                def process(self, filename: str, format_type: str = "txt") -> str:
                    """Process file with sub-global parameters."""
                    result = f"Processed {filename} ({format_type}) in {self.workspace}"
                    if self.backup:
                        result += " with backup"
                    return result

        cli = FreyjaCLI(ProjectManager, title="Project Manager CLI")

        # Test with sub-global parameters
        with patch.object(
            sys,
            "argv",
            [
                "proj_cli",
                "--config",
                "prod.json",
                "file-ops",
                "--workspace",
                "/tmp/files",  # noqa: S108 # acceptable in tests
                "--backup",
                "process",
                "data.txt",
                "--format-type",
                "csv",
            ],
        ):
            result = cli.run()

        assert result == "Processed data.txt (csv) in /tmp/files with backup"
