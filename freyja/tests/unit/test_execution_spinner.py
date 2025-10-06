"""Tests for ExecutionSpinner functionality."""

import time
from unittest.mock import Mock, patch

import pytest

from freyja.theme import ColorFormatter
from freyja.utils.spinner import CommandContext, ExecutionSpinner


class TestCommandContext:
    """Test CommandContext dataclass functionality."""

    def test_command_context_initialization(self):
        """Test CommandContext can be initialized with default values."""
        context = CommandContext()
        assert context.namespace is None
        assert context.command == ""  # Default is empty string, not None
        assert context.subcommand is None
        assert context.global_args == {}
        assert context.group_args == {}
        assert context.command_args == {}
        assert context.positional_args == []
        assert context.custom_status is None

    def test_command_context_with_values(self):
        """Test CommandContext with provided values."""
        context = CommandContext(
            namespace="system",
            command="completion",
            subcommand="install",
            global_args={"config": "test.json"},
            group_args={"workspace": "/tmp"},
            command_args={"shell": "bash"},
            positional_args=["arg1", "arg2"],
        )

        assert context.namespace == "system"
        assert context.command == "completion"
        assert context.subcommand == "install"
        assert context.global_args == {"config": "test.json"}
        assert context.group_args == {"workspace": "/tmp"}
        assert context.command_args == {"shell": "bash"}
        assert context.positional_args == ["arg1", "arg2"]


class TestExecutionSpinner:
    """Test ExecutionSpinner functionality."""

    def test_spinner_initialization(self):
        """Test spinner initializes correctly."""
        spinner = ExecutionSpinner()
        assert spinner.color_formatter is None
        assert spinner.verbose is False
        assert spinner.thread is None
        assert spinner.running is False
        assert spinner.command_context is None

    def test_spinner_with_color_formatter(self):
        """Test spinner initialization with color formatter."""
        color_formatter = ColorFormatter()
        spinner = ExecutionSpinner(color_formatter, verbose=True)
        assert spinner.color_formatter is color_formatter
        assert spinner.verbose is True

    def test_format_command_name_simple(self):
        """Test command name formatting for simple commands."""
        spinner = ExecutionSpinner()
        context = CommandContext(command="test_command")
        spinner.command_context = context

        result = spinner._format_command_name()
        assert result == "test_command"

    def test_format_command_name_hierarchical(self):
        """Test command name formatting for hierarchical commands."""
        spinner = ExecutionSpinner()
        context = CommandContext(namespace="file-ops", command="process")
        spinner.command_context = context

        result = spinner._format_command_name()
        assert result == "file-ops:process"

    def test_format_command_name_full_hierarchy(self):
        """Test command name formatting for full hierarchical commands."""
        spinner = ExecutionSpinner()
        context = CommandContext(namespace="system", command="completion", subcommand="install")
        spinner.command_context = context

        result = spinner._format_command_name()
        assert result == "system:completion:install"

    def test_format_options_global_only(self):
        """Test option formatting with only global arguments."""
        spinner = ExecutionSpinner()
        context = CommandContext(
            command="test_command", global_args={"config": "test.json", "debug": True}
        )
        spinner.command_context = context

        result = spinner._format_options()
        # Should contain both options
        assert "global:config:test.json" in result
        assert "global:debug:True" in result

    def test_format_options_all_types(self):
        """Test option formatting with all argument types."""
        spinner = ExecutionSpinner()
        context = CommandContext(
            command="test_command",
            global_args={"config": "test.json"},
            group_args={"workspace": "/tmp"},
            command_args={"format": "json"},
            positional_args=["input.txt"],
        )
        spinner.command_context = context

        result = spinner._format_options()
        assert "positional:0:input.txt" in result  # Positional first
        assert "global:config:test.json" in result
        assert "group:workspace:/tmp" in result
        assert "test_command:format:json" in result

    def test_format_options_ordering(self):
        """Test that options are formatted in correct order: positional, global, group, command."""
        spinner = ExecutionSpinner()
        context = CommandContext(
            command="test_command",
            global_args={"config": "test.json"},
            group_args={"workspace": "/tmp"},
            command_args={"format": "json"},
            positional_args=["input.txt", "output.txt"],
        )
        spinner.command_context = context

        result = spinner._format_options()

        # First parts should be positional
        assert result[0] == "positional:0:input.txt"
        assert result[1] == "positional:1:output.txt"
        # Should contain the type prefixes in order
        assert any("global:" in part for part in result)
        assert any("group:" in part for part in result)
        assert any("test_command:" in part for part in result)

    def test_augment_status_without_thread(self):
        """Test augment_status when spinner thread is not active."""
        spinner = ExecutionSpinner()
        context = CommandContext()
        spinner.command_context = context

        # Should not raise an exception
        spinner.augment_status("Test message")
        assert spinner.command_context.custom_status == "Test message"

    def test_augment_status_with_thread(self):
        """Test augment_status updates status correctly."""
        spinner = ExecutionSpinner()
        context = CommandContext()
        spinner.command_context = context
        spinner.running = True

        spinner.augment_status("Custom status")
        assert spinner.command_context.custom_status == "Custom status"

    @patch("threading.Thread")
    def test_start_creates_thread(self, mock_thread):
        """Test that start creates and starts a spinner thread."""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        spinner = ExecutionSpinner()
        context = CommandContext(command="test_command")

        spinner.start(context)

        # Verify thread was created and started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
        assert spinner.running is True
        assert spinner.command_context is context

    def test_stop_sets_flags(self):
        """Test that stop sets the appropriate flags."""
        spinner = ExecutionSpinner()
        spinner.running = True
        mock_thread = Mock()
        mock_thread.join = Mock()
        spinner.thread = mock_thread

        spinner.stop(success=True)

        assert spinner.running is False
        mock_thread.join.assert_called_once_with(timeout=0.5)

    def test_context_manager_success(self):
        """Test spinner context manager with successful execution."""
        spinner = ExecutionSpinner()
        context = CommandContext(command="test_command")

        with (
            patch.object(spinner, "start") as mock_start,
            patch.object(spinner, "stop") as mock_stop,
        ):

            with spinner.execute(context):
                pass

            mock_start.assert_called_once_with(context)
            mock_stop.assert_called_once_with(True)

    def test_context_manager_exception(self):
        """Test spinner context manager with exception."""
        spinner = ExecutionSpinner()
        context = CommandContext(command="test_command")

        with (
            patch.object(spinner, "start") as mock_start,
            patch.object(spinner, "stop") as mock_stop,
        ):

            with pytest.raises(ValueError):
                with spinner.execute(context):
                    raise ValueError("Test error")

            mock_start.assert_called_once_with(context)
            mock_stop.assert_called_once_with(False)

    @patch("sys.stdout.write")
    @patch("sys.stdout.flush")
    def test_spinner_animation(self, mock_flush, mock_write):
        """Test that spinner animation writes to stdout."""
        spinner = ExecutionSpinner()
        context = CommandContext(command="test_command")

        # Start spinner briefly
        spinner.start(context)
        time.sleep(0.1)  # Let it spin briefly
        spinner.stop()

        # Should have written some output
        assert mock_write.called
        assert mock_flush.called

    @patch("builtins.print")
    @patch("sys.stdout.write")
    @patch("sys.stdout.flush")
    def test_spinner_final_status_success(self, mock_flush, mock_write, mock_print):
        """Test that spinner shows checkmark on successful completion."""
        spinner = ExecutionSpinner(verbose=False)  # Non-verbose mode to trigger final status
        context = CommandContext(command="test_command")

        # Mock the status line
        spinner.status_line = "Executing test_command"

        # Stop with success
        spinner.stop(success=True)

        # Should print final status with checkmark
        mock_print.assert_called_once()
        printed_message = mock_print.call_args[0][0]
        assert "✓" in printed_message
        assert "Executing test_command" in printed_message

    @patch("builtins.print")
    @patch("sys.stdout.write")
    @patch("sys.stdout.flush")
    def test_spinner_final_status_failure(self, mock_flush, mock_write, mock_print):
        """Test that spinner shows X mark on failed completion."""
        spinner = ExecutionSpinner(verbose=False)  # Non-verbose mode to trigger final status
        context = CommandContext(command="test_command")

        # Mock the status line
        spinner.status_line = "Executing test_command"

        # Stop with failure
        spinner.stop(success=False)

        # Should print final status with X mark
        mock_print.assert_called_once()
        printed_message = mock_print.call_args[0][0]
        assert "✗" in printed_message
        assert "Executing test_command" in printed_message

    @patch("builtins.print")
    @patch("sys.stdout.write")
    @patch("sys.stdout.flush")
    def test_spinner_verbose_mode_no_final_status(self, mock_flush, mock_write, mock_print):
        """Test that spinner doesn't show final status in verbose mode."""
        spinner = ExecutionSpinner(verbose=True)  # Verbose mode
        context = CommandContext(command="test_command")

        # Mock the status line
        spinner.status_line = "Executing test_command"

        # Stop with success
        spinner.stop(success=True)

        # Should not print any final status in verbose mode
        mock_print.assert_not_called()

    @patch("builtins.print")
    @patch("sys.stdout.write")
    @patch("sys.stdout.flush")
    def test_spinner_final_status_with_color_formatter(self, mock_flush, mock_write, mock_print):
        """Test that spinner applies color formatting to final status."""
        # Create a mock color formatter
        mock_color_formatter = Mock()
        mock_color_formatter.apply_style.return_value = "STYLED: ✓ Executing test_command"

        spinner = ExecutionSpinner(color_formatter=mock_color_formatter, verbose=False)
        context = CommandContext(command="test_command")

        # Mock the status line
        spinner.status_line = "Executing test_command"

        # Stop with success
        spinner.stop(success=True)

        # Should print styled final status
        mock_print.assert_called_once()
        printed_message = mock_print.call_args[0][0]
        assert "STYLED: ✓ Executing test_command" == printed_message

        # Color formatter should have been called
        mock_color_formatter.apply_style.assert_called_once()

    def test_spinner_with_color_formatting(self):
        """Test spinner uses color formatter when available."""
        color_formatter = ColorFormatter()

        spinner = ExecutionSpinner(color_formatter, verbose=False)
        context = CommandContext(command="test_command")

        # Test that the color formatter is stored
        assert spinner.color_formatter is color_formatter

    def test_status_line_updated(self):
        """Test that status line is updated when context changes."""
        spinner = ExecutionSpinner()
        context = CommandContext(command="test_command")

        spinner.start(context)
        spinner.stop()

        # Should have executed without error
        assert spinner.command_context is context
