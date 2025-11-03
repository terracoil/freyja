# Refactored FreyjaCLI class - Simplified coordinator role only
from __future__ import annotations

import os
import sys
from collections.abc import Callable, Sequence
from contextlib import contextmanager
from typing import Any

from freyja.command import CommandDiscovery, CommandExecutor, CommandParser, ClassHandler, ExecutionCoordinator
from freyja.utils import OutputCapture, OutputCaptureConfig

Target = type[Any] | Sequence[type[Any]]


class FreyjaCLI:
    """
    Simplified FreyjaCLI coordinator that orchestrates command discovery, parsing, and execution.
    """

    def __init__(
        self,
        target: Target,
        title: str | None = None,
        method_filter: Callable | None = None,
        theme=None,
        alphabetize: bool = True,
        completion: bool = True,
        theme_tuner=False,
        # Output capture parameters
        capture_output: bool = False,
        capture_stdout: bool = True,
        capture_stderr: bool = False,
        capture_stdin: bool = False,
        output_capture_config: dict[str, Any] | None = None,
    ):
        """
        Initialize FreyjaCLI with target and configuration.

        :param target: Class or list of classes to generate FreyjaCLI from
        :param title: FreyjaCLI application title
        :param method_filter: Optional filter for methods (class mode)
        :param theme: Optional theme for colored output
        :param alphabetize: Whether to sort cmd_tree and options alphabetically
        :param completion: Whether to enable shell completion
        :param capture_output: Enable output capture (opt-in, default: False)
        :param capture_stdout: Capture stdout when output capture is enabled
        :param capture_stderr: Capture stderr when output capture is enabled
        :param capture_stdin: Capture stdin when output capture is enabled
        :param output_capture_config: Advanced OutputCapture configuration
        """

        # Initialize discovery service (replaces TargetAnalyzer)
        self.discovery = CommandDiscovery(
            target=target,
            method_filter=method_filter,
            completion=completion,
            theme_tuner=theme_tuner,
        )

        # Get target mode and validation from discovery
        self.target_mode = self.discovery.mode

        # Validate class mode for command collisions when multiple classes are present
        if self.discovery.target_classes and len(self.discovery.target_classes) > 1:
            handler = ClassHandler()
            handler.validate_classes(self.discovery.target_classes)

        # Set title based on target
        self.title = title or self.discovery.generate_title()

        # Store only essential config
        self.theme = theme
        self.enable_completion = completion

        # Create output capture configuration
        self.output_capture_config = OutputCaptureConfig.from_kwargs(
            capture_output=capture_output,
            capture_stdout=capture_stdout,
            capture_stderr=capture_stderr,
            capture_stdin=capture_stdin,
            output_capture_config=output_capture_config,
        )

        # Discover cmd_tree
        # self.discovery.cmd_tree = discovery.cmd_tree

        # Initialize command executors
        executors = self._initialize_executors()

        # Initialize execution coordinator
        self.execution_coordinator = ExecutionCoordinator(
            self.target_mode, executors, self.output_capture_config
        )
        # Pass command tree and CLI instance for completion
        self.execution_coordinator.command_tree = self.discovery.cmd_tree
        self.execution_coordinator.cli_instance = self

        # Initialize parser service
        self.parser_service = CommandParser(
            title=self.title, theme=theme, alphabetize=alphabetize, enable_completion=completion
        )

        # Set target_class and target_classes properties for compatibility
        self.target_class = self.discovery.primary_class
        self.target_classes = self.discovery.target_classes

        # Get command structure from discovery (no need to build separately)
        self.commands = self.discovery.cmd_tree.to_dict()

        # Essential compatibility properties only
        # Note: target_module removed - class-based CLI only

    def run(self, args: list[str] | None = None) -> Any:
        """
        Parse arguments and execute the appropriate command.

        :param args: Optional command line arguments (uses sys.argv if None)
        :return: Command execution result
        """
        result = None

        # Handle completion requests early
        if self.enable_completion and self._is_completion_request():
            self._handle_completion()
        else:
            # Check for no-color flag
            no_color = ExecutionCoordinator.check_no_color_flag(args or [])

            # Create parser and parse arguments
            parser = self.create_parser(no_color=no_color)

            # Parse and execute with context
            result = self._execute_with_context(parser, args)

        return result

    # Output Capture Public API
    @property
    def output_capture(self) -> OutputCapture | None:
        """Access the OutputCapture instance if enabled."""
        return self.execution_coordinator.output_capture

    def get_captured_output(self, stream: str = "stdout") -> str | None:
        """Get captured output if capture is enabled.

        :param stream: Stream name ('stdout', 'stderr', 'stdin')
        :return: Captured content or None if capture disabled
        """
        result = None
        if self.output_capture:
            result = self.output_capture.get_output(stream)
        return result

    def get_all_captured_output(self) -> dict[str, str | None]:
        """Get all captured output if capture is enabled.

        :return: Dictionary with captured content for each stream
        """
        result = {"stdout": None, "stderr": None, "stdin": None}
        if self.output_capture:
            result = self.output_capture.get_all_output()
        return result

    def clear_captured_output(self) -> None:
        """Clear captured output buffer."""
        if self.output_capture:
            self.output_capture.clear()

    def enable_output_capture(self, **kwargs) -> None:
        """Enable output capture dynamically.

        :param kwargs: OutputCaptureConfig parameters (capture_stdout, capture_stderr, etc.)
        """
        self.execution_coordinator.enable_output_capture(**kwargs)

    def disable_output_capture(self) -> None:
        """Disable output capture dynamically."""
        self.execution_coordinator.disable_output_capture()

    @contextmanager
    def capture_output(self, **kwargs):
        """Context manager for temporary output capture.

        :param kwargs: OutputCaptureConfig parameters
        """
        was_enabled = self.execution_coordinator.has_output_capture()
        old_config = None

        if was_enabled:
            old_config = self.execution_coordinator.get_output_config()

        try:
            self.enable_output_capture(**kwargs)
            yield self.output_capture
        finally:
            if was_enabled and old_config:
                self.execution_coordinator.set_output_config(old_config)
            elif not was_enabled:
                self.disable_output_capture()

    def _execute_with_context(self, parser, args) -> Any:
        """Execute command with FreyjaCLI context."""
        # Add context information to the execution coordinator
        self.execution_coordinator.command_tree = self.discovery.cmd_tree
        self.execution_coordinator.cli_instance = self

        return self.execution_coordinator.parse_and_execute(parser, args)

    def _initialize_executors(self) -> dict:
        """Initialize command executors based on target mode."""
        # Create color formatter from theme
        color_formatter = None
        theme = self.theme
        if not theme:
            from freyja.theme.defaults import create_default_theme

            theme = create_default_theme()

        if theme:
            from freyja.theme import ColorFormatter

            color_formatter = ColorFormatter()

        # Determine executors based on class count
        if self.discovery.target_classes and len(self.discovery.target_classes) > 1:
            # Multiple classes: create executor for each class
            executors = {
                target_class: CommandExecutor(
                    target_class=target_class,
                    color_formatter=color_formatter,
                    verbose=False,  # Will be updated during execution
                )
                for target_class in self.discovery.target_classes
            }
        else:
            # Single class: create single primary executor
            executors = {
                "primary": CommandExecutor(
                    target_class=self.discovery.primary_class,
                    color_formatter=color_formatter,
                    verbose=False,  # Will be updated during execution
                )
            }

        return executors

    def _is_completion_request(self) -> bool:
        """
        Check if this is a shell completion request.

        Uses multiple indicators to ensure we only enter completion mode
        when explicitly requested by shell completion systems.
        """
        result = False

        # Check for main completion environment variable
        if os.getenv("_FREYJA_COMPLETE") is not None:
            result = True
        else:
            # Check for shell-specific completion variables
            completion_vars = [
                "_FREYJA_COMPLETE_ZSH",
                "_FREYJA_COMPLETE_BASH",
                "_FREYJA_COMPLETE_FISH",
                "_FREYJA_COMPLETE_POWERSHELL",
            ]

            if any(os.getenv(var) is not None for var in completion_vars):
                result = True
            elif "--_complete" in sys.argv:
                # Check for --_complete flag (legacy support)
                result = True

        return result

    def _handle_completion(self):
        """
        Handle shell completion request.

        Ensures completion mode is completely isolated from normal execution.
        """
        try:
            # Use the execution coordinator's completion handler
            result = self.execution_coordinator.handle_completion_request()

            # Explicitly exit after completion to prevent any further processing
            sys.exit(0 if result == 0 else 1)

        except Exception as e:
            # In case of completion errors, fail gracefully
            print(f"Completion error: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            # Ensure we exit - completion should never continue to normal execution
            sys.exit(0)

    def create_parser(self, no_color: bool = False):
        """Create argument parser using pre-built command tree."""
        return self.parser_service.create_parser(
            command_tree=self.commands,
            target_mode=self.target_mode.value,
            target_class=self.target_class,
            no_color=no_color,
        )
