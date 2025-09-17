"""Tests for OutputCapture and OutputFormatter functionality."""

import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from freyja.utils.output_capture import OutputCapture, OutputFormatter
from freyja.theme import ColorFormatter, Theme, ThemeStyle, RGB


class TestOutputCapture:
    """Test OutputCapture functionality."""

    def test_initialization(self):
        """Test OutputCapture initializes correctly."""
        capture = OutputCapture()
        assert capture.stdout_buffer is not None
        assert capture.stderr_buffer is not None
        assert capture.original_stdout is None
        assert capture.original_stderr is None
        assert capture._active is False

    def test_start_capture(self):
        """Test starting output capture."""
        capture = OutputCapture()
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        capture.start()
        
        assert capture._active is True
        assert capture.original_stdout is original_stdout
        assert capture.original_stderr is original_stderr
        assert sys.stdout is capture.stdout_buffer
        assert sys.stderr is capture.stderr_buffer

    def test_start_capture_already_active(self):
        """Test starting capture when already active raises error."""
        capture = OutputCapture()
        capture.start()
        
        with pytest.raises(RuntimeError, match="Output capture is already active"):
            capture.start()

    def test_stop_capture(self):
        """Test stopping output capture."""
        capture = OutputCapture()
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        capture.start()
        
        # Write some content
        print("test stdout")
        print("test stderr", file=sys.stderr)
        
        stdout_content, stderr_content = capture.stop()
        
        assert capture._active is False
        assert sys.stdout is original_stdout
        assert sys.stderr is original_stderr
        assert "test stdout" in stdout_content
        assert "test stderr" in stderr_content

    def test_stop_capture_not_active(self):
        """Test stopping capture when not active raises error."""
        capture = OutputCapture()
        
        with pytest.raises(RuntimeError, match="Output capture is not active"):
            capture.stop()

    def test_is_active(self):
        """Test is_active status tracking."""
        capture = OutputCapture()
        assert capture.is_active() is False
        
        capture.start()
        assert capture.is_active() is True
        
        capture.stop()
        assert capture.is_active() is False

    def test_context_manager_success(self):
        """Test context manager for successful execution."""
        capture = OutputCapture()
        original_stdout = sys.stdout
        
        with capture.capture():
            print("test output")
            assert sys.stdout is capture.stdout_buffer
            assert capture.is_active() is True
        
        assert sys.stdout is original_stdout
        assert capture.is_active() is False

    def test_context_manager_with_exception(self):
        """Test context manager handles exceptions properly."""
        capture = OutputCapture()
        original_stdout = sys.stdout
        
        with pytest.raises(ValueError):
            with capture.capture():
                print("test output")
                raise ValueError("Test error")
        
        # Should restore stdout even after exception
        assert sys.stdout is original_stdout
        assert capture.is_active() is False

    def test_capture_stdout_only(self):
        """Test capturing only stdout."""
        capture = OutputCapture()
        
        capture.start()
        print("stdout message")
        stdout_content, stderr_content = capture.stop()
        
        assert "stdout message" in stdout_content
        assert stderr_content == ""

    def test_capture_stderr_only(self):
        """Test capturing only stderr."""
        capture = OutputCapture()
        
        capture.start()
        print("stderr message", file=sys.stderr)
        stdout_content, stderr_content = capture.stop()
        
        assert stdout_content == ""
        assert "stderr message" in stderr_content

    def test_capture_both_streams(self):
        """Test capturing both stdout and stderr."""
        capture = OutputCapture()
        
        capture.start()
        print("stdout message")
        print("stderr message", file=sys.stderr)
        stdout_content, stderr_content = capture.stop()
        
        assert "stdout message" in stdout_content
        assert "stderr message" in stderr_content

    def test_multiple_captures(self):
        """Test multiple capture sessions reset buffers."""
        capture = OutputCapture()
        
        # First capture
        capture.start()
        print("first message")
        first_stdout, _ = capture.stop()
        
        # Second capture  
        capture.start()
        print("second message")
        second_stdout, _ = capture.stop()
        
        # Buffer should be reset between captures
        assert "first message" in first_stdout
        assert "second message" in second_stdout
        assert "first message" not in second_stdout


class TestOutputFormatter:
    """Test OutputFormatter functionality."""

    def test_initialization(self):
        """Test OutputFormatter initializes correctly."""
        formatter = OutputFormatter()
        assert formatter.color_formatter is None

    def test_initialization_with_color_formatter(self):
        """Test OutputFormatter with color formatter."""
        color_formatter = ColorFormatter()
        formatter = OutputFormatter(color_formatter)
        assert formatter.color_formatter is color_formatter

    def test_should_display_output_verbose_mode(self):
        """Test output display decision in verbose mode."""
        formatter = OutputFormatter()
        
        # Verbose mode should always display
        assert formatter.should_display_output(verbose=True, command_success=True) is True
        assert formatter.should_display_output(verbose=True, command_success=False) is True

    def test_should_display_output_non_verbose(self):
        """Test output display decision in non-verbose mode."""
        formatter = OutputFormatter()
        
        # Non-verbose mode only displays on failure
        assert formatter.should_display_output(verbose=False, command_success=True) is False
        assert formatter.should_display_output(verbose=False, command_success=False) is True

    @patch('builtins.print')
    def test_format_output_stdout_only(self, mock_print):
        """Test formatting output with only stdout."""
        formatter = OutputFormatter()
        
        formatter.format_output("test_command", "line1\nline2\n", "")
        
        # Should print each non-empty line with prefix
        expected_calls = [
            (("{test_command} line1",), {}),
            (("{test_command} line2",), {})
        ]
        
        assert mock_print.call_count == 2
        for call, expected in zip(mock_print.call_args_list, expected_calls):
            assert call == expected

    @patch('builtins.print')  
    def test_format_output_stderr_only(self, mock_print):
        """Test formatting output with only stderr."""
        formatter = OutputFormatter()
        
        formatter.format_output("test_command", "", "error1\nerror2\n")
        
        # Should print stderr with ERROR marker
        expected_calls = [
            (("{test_command} [ERROR] error1",), {'file': sys.stderr}),
            (("{test_command} [ERROR] error2",), {'file': sys.stderr})
        ]
        
        assert mock_print.call_count == 2
        for call, expected in zip(mock_print.call_args_list, expected_calls):
            assert call == expected

    @patch('builtins.print')
    def test_format_output_both_streams(self, mock_print):
        """Test formatting output with both stdout and stderr."""
        formatter = OutputFormatter()
        
        formatter.format_output("test_command", "stdout_line\n", "stderr_line\n")
        
        assert mock_print.call_count == 2
        # First call should be stdout
        assert mock_print.call_args_list[0] == (("{test_command} stdout_line",), {})
        # Second call should be stderr
        assert mock_print.call_args_list[1] == (("{test_command} [ERROR] stderr_line",), {'file': sys.stderr})

    @patch('builtins.print')
    def test_format_output_empty_lines_skipped(self, mock_print):
        """Test that empty lines are skipped in output formatting."""
        formatter = OutputFormatter()
        
        formatter.format_output("test_command", "line1\n\nline2\n", "")
        
        # Should only print non-empty lines
        assert mock_print.call_count == 2
        assert mock_print.call_args_list[0] == (("{test_command} line1",), {})
        assert mock_print.call_args_list[1] == (("{test_command} line2",), {})

    @patch('builtins.print')
    def test_format_output_with_color_formatter(self, mock_print):
        """Test formatting output with color styling."""
        color_formatter = Mock()
        color_formatter.apply_style.return_value = "styled_prefix"
        
        formatter = OutputFormatter(color_formatter)
        
        with patch('freyja.theme.defaults.create_default_theme') as mock_theme:
            mock_theme.return_value.command_output = "mock_style"
            
            formatter.format_output("test_command", "test_line\n", "")
            
            # Should use styled prefix
            color_formatter.apply_style.assert_called_once()
            mock_print.assert_called_once_with("styled_prefix test_line")

    @patch('builtins.print')
    def test_format_output_color_formatting_fallback(self, mock_print):
        """Test color formatting falls back to plain text on error."""
        color_formatter = Mock()
        color_formatter.apply_style.side_effect = Exception("Color error")
        
        formatter = OutputFormatter(color_formatter)
        
        formatter.format_output("test_command", "test_line\n", "")
        
        # Should fallback to plain prefix
        mock_print.assert_called_once_with("{test_command} test_line")

    @patch('builtins.print')
    def test_format_output_hierarchical_command(self, mock_print):
        """Test formatting output with hierarchical command name."""
        formatter = OutputFormatter()
        
        formatter.format_output("file-ops:process", "processing file\n", "")
        
        mock_print.assert_called_once_with("{file-ops:process} processing file")

    def test_format_output_custom_style(self):
        """Test formatting with custom style name."""
        color_formatter = Mock()
        formatter = OutputFormatter(color_formatter)
        
        with patch('builtins.print') as mock_print:
            formatter.format_output("test_command", "test\n", "", "custom_style")
            
            # Should still work even with custom style
            mock_print.assert_called_once()