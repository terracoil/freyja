"""Output capture utilities for command execution."""

import sys
from contextlib import contextmanager
from dataclasses import dataclass
from io import StringIO


@dataclass
class OutputCaptureConfig:
    """Configuration for output capture behavior."""

    enabled: bool = False
    capture_stdout: bool = True
    capture_stderr: bool = False
    capture_stdin: bool = False
    buffer_size: int = 1024 * 1024  # 1MB default
    encoding: str = "utf-8"
    errors: str = "replace"

    @classmethod
    def from_kwargs(cls, **kwargs) -> "OutputCaptureConfig":
        """Create config from FreyjaCLI kwargs."""
        output_capture_config = kwargs.get("output_capture_config") or {}
        return cls(
            enabled=kwargs.get("capture_output", False),
            capture_stdout=kwargs.get("capture_stdout", True),
            capture_stderr=kwargs.get("capture_stderr", False),
            capture_stdin=kwargs.get("capture_stdin", False),
            **output_capture_config,
        )


class OutputCapture:
    """Captures stdout and stderr during command execution."""

    def __init__(
        self,
        capture_stdout: bool = True,
        capture_stderr: bool = False,
        capture_stdin: bool = False,
        buffer_size: int = 1024 * 1024,
        encoding: str = "utf-8",
        errors: str = "replace",
    ):
        """Initialize output capture with configurable streams.

        :param capture_stdout: Whether to capture stdout
        :param capture_stderr: Whether to capture stderr
        :param capture_stdin: Whether to capture stdin
        :param buffer_size: Buffer size for captured streams
        :param encoding: Text encoding for buffers
        :param errors: Error handling for encoding
        """
        self.capture_stdout = capture_stdout
        self.capture_stderr = capture_stderr
        self.capture_stdin = capture_stdin
        self.buffer_size = buffer_size
        self.encoding = encoding
        self.errors = errors

        # Create buffers only for streams we're capturing
        self.stdout_buffer = StringIO() if capture_stdout else None
        self.stderr_buffer = StringIO() if capture_stderr else None
        self.stdin_buffer = StringIO() if capture_stdin else None

        # Original streams
        self.original_stdout: object | None = None
        self.original_stderr: object | None = None
        self.original_stdin: object | None = None
        self._active = False

    def start(self):
        """Start capturing output.

        :raises RuntimeError: If capture is already active
        """
        if self._active:
            raise RuntimeError("Output capture is already active")

        # Store original streams and replace with buffers if capturing
        if self.capture_stdout:
            self.original_stdout = sys.stdout
            sys.stdout = self.stdout_buffer

        if self.capture_stderr:
            self.original_stderr = sys.stderr
            sys.stderr = self.stderr_buffer

        if self.capture_stdin:
            self.original_stdin = sys.stdin
            sys.stdin = self.stdin_buffer

        self._active = True

    def stop(self) -> tuple[str, str]:
        """Stop capturing and return captured output.

        :return: Tuple of (stdout_content, stderr_content)
        :raises RuntimeError: If capture is not active
        """
        if not self._active:
            raise RuntimeError("Output capture is not active")

        # Get captured content before restoring streams
        stdout_content = self.stdout_buffer.getvalue() if self.stdout_buffer else ""
        stderr_content = self.stderr_buffer.getvalue() if self.stderr_buffer else ""

        # Restore original streams
        if self.original_stdout:
            sys.stdout = self.original_stdout
        if self.original_stderr:
            sys.stderr = self.original_stderr
        if self.original_stdin:
            sys.stdin = self.original_stdin

        self._active = False
        self.original_stdout = None
        self.original_stderr = None
        self.original_stdin = None

        # Note: We DON'T reset buffers here so captured content remains available
        # Users can call clear() if they want to reset

        return stdout_content, stderr_content

    def is_active(self) -> bool:
        """Check if capture is currently active.

        :return: True if capture is active
        """
        return self._active

    @contextmanager
    def capture_output(self):
        """Context manager for output capture.

        Usage:
            capture = OutputCapture()
            with capture.capture_output():
                print("This will be captured")
            stdout, stderr = capture.stop()
        """
        self.start()
        try:
            yield self
        finally:
            if self._active:  # Only stop if still active
                self.stop()

    def get_output(self, stream: str = "stdout") -> str | None:
        """Get captured output for specific stream.

        :param stream: Stream name ('stdout', 'stderr', 'stdin')
        :return: Captured content or None if stream not captured
        """
        buffer_map = {
            "stdout": self.stdout_buffer,
            "stderr": self.stderr_buffer,
            "stdin": self.stdin_buffer,
        }
        buffer = buffer_map.get(stream)
        if buffer:
            return buffer.getvalue()
        return None

    def get_all_output(self) -> dict[str, str | None]:
        """Get all captured output.

        :return: Dictionary with captured content for each stream
        """
        return {
            "stdout": self.get_output("stdout"),
            "stderr": self.get_output("stderr"),
            "stdin": self.get_output("stdin"),
        }

    def clear(self) -> None:
        """Clear all capture buffers."""
        if self.stdout_buffer:
            self.stdout_buffer.seek(0)
            self.stdout_buffer.truncate(0)
        if self.stderr_buffer:
            self.stderr_buffer.seek(0)
            self.stderr_buffer.truncate(0)
        if self.stdin_buffer:
            self.stdin_buffer.seek(0)
            self.stdin_buffer.truncate(0)


class OutputFormatter:
    """Formats captured output with command prefixes."""

    def __init__(self, color_formatter=None):
        """Initialize output formatter.

        :param color_formatter: ColorFormatter instance for styling
        """
        self.color_formatter = color_formatter

    def format_output(
        self, command_name: str, stdout: str, stderr: str, style_name: str = "command_output"
    ) -> None:
        """Format and print captured output with command prefix.

        :param command_name: Name of the command that generated the output
        :param stdout: Captured stdout content
        :param stderr: Captured stderr content
        :param style_name: Name of the style to apply to prefixes
        """
        prefix = f"{{{command_name}}}"

        # Apply styling to prefix if color formatter is available
        if self.color_formatter and hasattr(self.color_formatter, "apply_style"):
            try:
                from ..theme.defaults import create_default_theme

                theme = create_default_theme()
                styled_prefix = self.color_formatter.apply_style(
                    prefix, getattr(theme, style_name, theme.command_output)
                )
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
        # ALWAYS show command output - users expect to see the results of their commands
        # This was the core issue: output was being hidden except in verbose mode or on failure
        return True
