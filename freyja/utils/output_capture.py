"""Output capture utilities for command execution."""

import sys
from contextlib import contextmanager
from io import StringIO
from typing import Tuple, Optional


class OutputCapture:
    """Captures stdout and stderr during command execution."""
    
    def __init__(self):
        """Initialize output capture."""
        self.stdout_buffer = StringIO()
        self.stderr_buffer = StringIO()
        self.original_stdout: Optional[object] = None
        self.original_stderr: Optional[object] = None
        self._active = False
    
    def start(self):
        """Start capturing output.
        
        :raises RuntimeError: If capture is already active
        """
        if self._active:
            raise RuntimeError("Output capture is already active")
        
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Replace stdout and stderr with our buffers
        sys.stdout = self.stdout_buffer
        sys.stderr = self.stderr_buffer
        
        self._active = True
    
    def stop(self) -> Tuple[str, str]:
        """Stop capturing and return captured output.
        
        :return: Tuple of (stdout_content, stderr_content)
        :raises RuntimeError: If capture is not active
        """
        if not self._active:
            raise RuntimeError("Output capture is not active")
        
        # Restore original stdout/stderr
        if self.original_stdout:
            sys.stdout = self.original_stdout
        if self.original_stderr:
            sys.stderr = self.original_stderr
        
        # Get captured content
        stdout_content = self.stdout_buffer.getvalue()
        stderr_content = self.stderr_buffer.getvalue()
        
        # Reset buffers for next use
        self.stdout_buffer = StringIO()
        self.stderr_buffer = StringIO()
        
        self._active = False
        self.original_stdout = None
        self.original_stderr = None
        
        return stdout_content, stderr_content
    
    def is_active(self) -> bool:
        """Check if capture is currently active.
        
        :return: True if capture is active
        """
        return self._active
    
    @contextmanager
    def capture(self):
        """Context manager for output capture.
        
        Usage:
            capture = OutputCapture()
            with capture.capture():
                print("This will be captured")
            stdout, stderr = capture.stop()
        """
        self.start()
        try:
            yield self
        finally:
            if self._active:  # Only stop if still active
                self.stop()


class OutputFormatter:
    """Formats captured output with command prefixes."""
    
    def __init__(self, color_formatter=None):
        """Initialize output formatter.
        
        :param color_formatter: ColorFormatter instance for styling
        """
        self.color_formatter = color_formatter
    
    def format_output(self, command_name: str, stdout: str, stderr: str, 
                     style_name: str = 'command_output') -> None:
        """Format and print captured output with command prefix.
        
        :param command_name: Name of the command that generated the output
        :param stdout: Captured stdout content
        :param stderr: Captured stderr content  
        :param style_name: Name of the style to apply to prefixes
        """
        prefix = f"{{{command_name}}}"
        
        # Apply styling to prefix if color formatter is available
        if self.color_formatter and hasattr(self.color_formatter, 'apply_style'):
            try:
                from ..theme.defaults import create_default_theme
                theme = create_default_theme()
                styled_prefix = self.color_formatter.apply_style(prefix, getattr(theme, style_name, theme.command_output))
            except Exception:
                # Fall back to plain prefix if styling fails
                styled_prefix = prefix
        else:
            styled_prefix = prefix
        
        # Display stdout with prefix
        if stdout:
            for line in stdout.splitlines():
                if line.strip():  # Skip empty lines
                    print(f"{styled_prefix} {line}")
        
        # Display stderr with prefix and error marker
        if stderr:
            error_prefix = f"{styled_prefix} [ERROR]"
            for line in stderr.splitlines():
                if line.strip():  # Skip empty lines
                    print(error_prefix + f" {line}", file=sys.stderr)
    
    def should_display_output(self, verbose: bool, command_success: bool) -> bool:
        """Determine if output should be displayed.
        
        :param verbose: Whether verbose mode is enabled
        :param command_success: Whether the command succeeded
        :return: True if output should be displayed
        """
        # In verbose mode, always show output
        # In non-verbose mode, only show output on failure
        return verbose or not command_success