"""FreyjaCLI execution coordination service.

Handles argument parsing and command execution coordination.
Extracted from FreyjaCLI class to reduce its size and improve separation of concerns.
"""

import os
from typing import Any

from freyja.utils.output_capture import OutputCapture, OutputCaptureConfig

from freyja.cli.target_mode_enum import TargetModeEnum


class ExecutionCoordinator:
    """Coordinates FreyjaCLI argument parsing and command execution."""

    def __init__(
        self,
        target_mode: TargetModeEnum,
        executors: dict[str | type, Any],
        output_capture_config: OutputCaptureConfig | None = None,
    ):
        """Initialize execution coordinator."""
        # Guard: Ensure target_mode is not None
        if target_mode is None:
            raise ValueError("target_mode cannot be None")

        # Guard: Ensure executors is not None
        if executors is None:
            raise ValueError("executors cannot be None")

        self.target_mode = target_mode
        self.executors = executors
        self.command_tree = None
        self.cli_instance = None

        # Initialize output capture configuration
        self.output_capture_config = output_capture_config or OutputCaptureConfig()
        self.output_capture: OutputCapture | None = None

        # Initialize output capture if enabled
        if self.output_capture_config.enabled:
            self._initialize_output_capture()

    def _initialize_output_capture(self) -> None:
        """Initialize OutputCapture based on config."""
        self.output_capture = OutputCapture(
            capture_stdout=self.output_capture_config.capture_stdout,
            capture_stderr=self.output_capture_config.capture_stderr,
            capture_stdin=self.output_capture_config.capture_stdin,
            buffer_size=self.output_capture_config.buffer_size,
            encoding=self.output_capture_config.encoding,
            errors=self.output_capture_config.errors,
        )

    def enable_output_capture(self, **kwargs) -> None:
        """Enable output capture dynamically."""
        self.output_capture_config = OutputCaptureConfig.from_kwargs(enabled=True, **kwargs)
        self._initialize_output_capture()

    def disable_output_capture(self) -> None:
        """Disable output capture and cleanup."""
        if self.output_capture and self.output_capture._active:
            self.output_capture.stop()
        self.output_capture = None
        self.output_capture_config.enabled = False

    def has_output_capture(self) -> bool:
        """Check if output capture is enabled."""
        return self.output_capture is not None

    def get_output_config(self) -> OutputCaptureConfig:
        """Get current output capture configuration."""
        return self.output_capture_config

    def set_output_config(self, config: OutputCaptureConfig) -> None:
        """Set output capture configuration."""
        was_enabled = self.has_output_capture()
        if was_enabled:
            self.disable_output_capture()

        self.output_capture_config = config
        if config.enabled:
            self._initialize_output_capture()

    def parse_and_execute(self, parser, args: list[str] | None) -> Any:
        """
        Parse arguments and execute command.

        This method should only be called for normal execution, not completion.
        Completion should be handled by the main CLI before reaching this point.
        """
        result = None

        # Get actual args (convert None to sys.argv[1:] like argparse does)
        import sys

        actual_args = args if args is not None else sys.argv[1:]

        # Sanity check: if we detect completion here, it's a bug
        completion_indicators = ["--_complete"]
        completion_vars = ["_FREYJA_COMPLETE", "_FREYJA_COMPLETE_ZSH", "_FREYJA_COMPLETE_BASH"]

        if any(indicator in actual_args for indicator in completion_indicators):
            raise RuntimeError("Completion request reached normal execution path - this is a bug")

        if any(os.getenv(var) for var in completion_vars):
            raise RuntimeError(
                "Completion environment detected in normal execution - this is a bug"
            )

        # NEW: Preprocess arguments for flexible ordering (unless this is a help request)
        if self.command_tree and actual_args and not self._is_help_request(actual_args):
            try:
                from freyja.parser.argument_preprocessor import ArgumentPreprocessor

                # Get target class from executors
                target_class = self._get_target_class_for_preprocessing()

                preprocessor = ArgumentPreprocessor(
                    command_tree=self.command_tree, target_class=target_class
                )

                # Validate arguments first
                is_valid, validation_errors = preprocessor.validate_arguments(actual_args)

                if not is_valid:
                    # Print validation errors and exit
                    for error in validation_errors:
                        print(f"Error: {error}")
                    raise SystemExit(2)

                # Preprocess arguments
                original_args = actual_args.copy()
                actual_args = preprocessor.preprocess_args(actual_args)

                # DEBUG: Show preprocessing results (disabled for cleaner output)
                # if actual_args != original_args:
                #   print(f"DEBUG: Original args: {original_args}")
                #   print(f"DEBUG: Preprocessed args: {actual_args}")

            except ImportError:
                # Preprocessor not available, continue with original args
                pass
            except Exception as e:
                # If preprocessing fails, continue with original args but show warning
                print(f"Warning: Argument preprocessing failed: {e}", file=sys.stderr)

        # Check if this is a hierarchical command that needs subgroup help
        if actual_args and self._should_show_subgroup_help(parser, actual_args):
            result = self._show_subgroup_help(parser, actual_args)
        else:
            try:
                parsed = parser.parse_args(actual_args)

                if not hasattr(parsed, "_cli_function"):
                    # No command specified, show help
                    result = self._handle_no_command(parser, parsed)
                else:
                    # Execute command
                    result = self._execute_command(parsed)

            except SystemExit:
                # Let argparse handle its own exits (help, errors, etc.)
                raise

            except Exception as e:
                # Handle execution errors - for argparse-like errors, raise SystemExit
                if isinstance(e, ValueError | KeyError) and "parsed" not in locals():
                    # Parsing errors should raise SystemExit like argparse does
                    print(f"Error: {e}")
                    raise SystemExit(2) from e
                else:
                    # Other execution errors
                    result = self._handle_execution_error(parsed if "parsed" in locals() else None, e)

        return result

    def _handle_no_command(self, parser, parsed) -> int:
        """Handle case where no command was specified."""
        if hasattr(parsed, "_complete") and parsed._complete:
            return 0  # Completion mode - don't show help

        # Check for --help flag explicitly
        if hasattr(parsed, "help") and parsed.help:
            parser.print_help()
            return 0

        # Default: show help and return success
        parser.print_help()
        return 0

    def _execute_command(self, parsed) -> Any:
        """Execute the command from parsed arguments."""
        # Inject CLI instance for system commands
        self._inject_cli_instance(parsed)

        # Detect verbose flag from parsed arguments
        verbose = getattr(parsed, "verbose", False) or getattr(parsed, "_global_verbose", False)

        # Execute with conditional output capture
        if self.output_capture:
            with self.output_capture.capture_output():
                result = self._execute_internal(parsed, verbose)
        else:
            result = self._execute_internal(parsed, verbose)

        return result

    def _execute_internal(self, parsed, verbose: bool) -> Any:
        """Internal method to execute command (used by both capture and non-capture paths)."""
        # Check if we have multiple classes (multiple executors)
        if len(self.executors) > 1 and "primary" not in self.executors:
            result = self._execute_multi_class_command(parsed, verbose)
        else:
            # Single class execution
            executor = self.executors.get("primary")
            if not executor:
                raise RuntimeError("No executor available for command execution")

            # Update executor verbose setting
            executor.verbose = verbose

            result = executor.execute_command(parsed=parsed, target_mode=self.target_mode)

        return result

    def _inject_cli_instance(self, parsed) -> None:
        """Inject CLI instance into parsed arguments for system commands."""
        # Check if this is a system command that needs CLI instance
        if hasattr(parsed, "_command_path") and getattr(parsed, "_command_path", "").startswith(
            "system"
        ):
            # Inject CLI instance
            if self.cli_instance:
                parsed._cli_instance = self.cli_instance

    def _execute_multi_class_command(self, parsed, verbose: bool = False) -> Any:
        """Execute command for multiple-class FreyjaCLI."""
        function_name = parsed._function_name
        source_class = self._find_source_class_for_function(function_name)

        if not source_class:
            raise ValueError(f"Could not find source class for function: {function_name}")

        executor = self.executors.get(source_class)

        if not executor:
            raise ValueError(f"No executor found for class: {source_class.__name__}")

        # Update executor verbose setting
        executor.verbose = verbose

        return executor.execute_command(parsed=parsed, target_mode=TargetModeEnum.CLASS)

    def _find_source_class_for_function(self, function_name: str) -> type | None:
        """Find the source class for a given function name."""
        result = None
        if self.command_tree:
            result = self.command_tree.find_source_class(function_name)
        return result

    def _handle_execution_error(self, parsed, error: Exception) -> int:
        """Handle command execution errors."""
        if isinstance(error, KeyboardInterrupt):
            print("\nOperation cancelled by user")
            result = 130  # Standard exit code for SIGINT
        else:
            print(f"Error executing command: {error}")

            if parsed and hasattr(parsed, "_function_name"):
                print(f"Function: {parsed._function_name}")

            result = 1

        return result

    def _should_show_subgroup_help(self, parser, args: list[str]) -> bool:
        """Check if args represent a hierarchical command that needs subgroup help."""
        result = False

        # Don't interfere with explicit help requests
        if "--help" in args or "-h" in args:
            result = False
        else:
            # Check if we have a hierarchical path that exists but needs a final command
            try:
                parsed = parser.parse_args(args)
                # Check if parsing succeeded but we landed on a subgroup that has subcommands
                # but no final command was chosen (no _cli_function attribute)
                if not hasattr(parsed, "_cli_function"):
                    result = self._is_hierarchical_path(parser, args)
                else:
                    result = False  # Has _cli_function, so it's a complete command
            except SystemExit as e:
                # Help-related SystemExits (exit code 0) should check hierarchical path
                if e.code == 0:
                    result = self._is_hierarchical_path(parser, args)
                # SystemExit(2) likely means unprocessed arguments - not a help request
                elif e.code == 2:
                    result = False
                else:
                    # Other SystemExit codes, let them propagate
                    raise

        return result

    def _is_hierarchical_path(self, parser, args: list[str]) -> bool:
        """Check if args represent a valid hierarchical path to a subgroup."""
        if not args:
            return False

        # Walk through the parser structure to see if this path exists
        current_parser = parser
        for i, arg in enumerate(args):
            if not hasattr(current_parser, "_subparsers"):
                return False

            subparsers_action = None
            for action in current_parser._actions:
                if hasattr(action, "choices") and action.choices and arg in action.choices:
                    subparsers_action = action
                    break

            if not subparsers_action:
                return False

            # Get the subparser for this command
            subparser = subparsers_action.choices[arg]

            # If this is the last argument and the subparser has its own subparsers,
            # then this is a hierarchical path that needs help
            if i == len(args) - 1:
                return self._parser_has_subcommands(subparser)

            current_parser = subparser

        return False

    def _parser_has_subcommands(self, parser) -> bool:
        """Check if a parser has subcommands."""
        for action in parser._actions:
            if hasattr(action, "choices"):
                return True
        return False

    def _show_subgroup_help(self, parser, args: list[str]) -> int:
        """Show help for a specific subgroup by invoking subparser help."""
        # Navigate to the subparser and show its help
        current_parser = parser

        for arg in args:
            for action in current_parser._actions:
                if hasattr(action, "choices") and action.choices and arg in action.choices:
                    current_parser = action.choices[arg]
                    break

        # Show help for the final subparser
        current_parser.print_help()
        return 0

    def handle_completion_request(self):
        """
        Handle shell completion requests with complete isolation.

        This method handles completion generation and ensures it never
        interferes with normal command execution.
        """
        import os
        import sys

        # Determine which shell type is requesting (try multiple variables)
        shell_type = (
            os.environ.get("_FREYJA_COMPLETE")
            or os.environ.get("_FREYJA_COMPLETE_ZSH")
            and "zsh"
            or os.environ.get("_FREYJA_COMPLETE_BASH")
            and "bash"
            or os.environ.get("_FREYJA_COMPLETE_FISH")
            and "fish"
            or os.environ.get("_FREYJA_COMPLETE_POWERSHELL")
            and "powershell"
            or ""
        )

        if not shell_type:
            # No completion environment set - this should not be called
            # Return immediately to avoid any interference
            return 0

        # Verify we have the required command tree
        if not self.command_tree:
            # No command tree available - return empty completion
            return 0

        # Get completion words from environment
        words_str = os.environ.get("COMP_WORDS_STR", "")
        cword_num = int(os.environ.get("COMP_CWORD_NUM", "0"))

        words = words_str.split() if words_str else []

        # Create completion context
        from freyja.completion.base import CompletionContext

        # Parse the current word being completed
        current_word = ""
        if words and cword_num > 0 and cword_num <= len(words):
            current_word = words[cword_num - 1] if cword_num <= len(words) else ""

        # Extract command group path (exclude the current word being completed)
        command_group_path = []
        if len(words) > 1:
            # Only include words up to but not including the current word being completed
            for i in range(1, min(cword_num - 1, len(words))):
                word = words[i]
                if not word.startswith("-"):
                    command_group_path.append(word)

        # Create parser for context
        parser = self.cli_instance.create_parser(no_color=True) if self.cli_instance else None

        # Create completion context
        context = CompletionContext(
            words=words,
            current_word=current_word,
            cursor_position=0,
            command_group_path=command_group_path,
            parser=parser,
            cli=self.cli_instance,
        )

        # Import the appropriate completion handler
        if shell_type == "zsh":
            from freyja.completion.zsh import ZshCompletionHandler

            handler = ZshCompletionHandler(self.cli_instance)
        else:
            # Use bash handler as fallback
            from freyja.completion.bash import BashCompletionHandler

            handler = BashCompletionHandler(self.cli_instance)

        # Get completions and output them
        try:
            completions = handler.get_completions(context)

            # Output completions to stdout (one per line for shell parsing)
            for completion in completions:
                print(completion)

            # Flush output to ensure completions are sent immediately
            sys.stdout.flush()

            return 0

        except Exception as e:
            # If completion generation fails, don't crash but return empty
            print(f"Completion generation error: {e}", file=sys.stderr)
            return 1

    def _is_help_request(self, args: list[str]) -> bool:
        """Check if the arguments represent a help request."""
        return "--help" in args or "-h" in args

    def _get_target_class_for_preprocessing(self) -> type | None:
        """Get the target class for option discovery from executors."""
        # If we have a primary executor, get its target class
        if "primary" in self.executors:
            executor = self.executors["primary"]
            if hasattr(executor, "target_class"):
                return executor.target_class

        # For multi-class mode, try to get the last class (primary class)
        if len(self.executors) > 1:
            # The last executor in the list is typically the primary one
            executor_items = list(self.executors.items())
            if executor_items:
                last_executor = executor_items[-1][1]
                if hasattr(last_executor, "target_class"):
                    return last_executor.target_class

        return None

    @staticmethod
    def check_no_color_flag(args: list[str]) -> bool:
        """Check if --no-color flag is present in arguments."""
        return "--no-color" in args or "-n" in args
