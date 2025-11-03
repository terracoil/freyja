"""Command execution service for FreyjaCLI applications.

Handles the execution of different command types (direct methods, inner class methods)
by creating appropriate instances and invoking methods with parsed arguments.
"""

import inspect
import sys
import traceback
from typing import Any

from ..utils.output_capture import OutputCapture, OutputFormatter
from ..utils.spinner import CommandContext, ExecutionSpinner


class CommandExecutor:
    """Centralized service for executing FreyjaCLI commands with different patterns."""

    def __init__(
        self,
        target_class: type | None = None,
        color_formatter=None,
        verbose: bool = False,
        enable_output_capture: bool = False,
    ):
        """Initialize command executor with target information.

        :param target_class: Class containing methods to execute
        :param color_formatter: ColorFormatter instance for styling output
        :param verbose: Whether to run in verbose mode
        :param enable_output_capture: Whether to enable output capture (default: False)
        """
        self.target_class = target_class
        self.color_formatter = color_formatter
        self.verbose = verbose
        self.enable_output_capture = enable_output_capture
        self.spinner = ExecutionSpinner(color_formatter, verbose)
        self.output_capture = OutputCapture() if enable_output_capture else None
        self.output_formatter = OutputFormatter(color_formatter) if enable_output_capture else None

    def _build_command_context(self, parsed) -> CommandContext:
        """Build command context from parsed arguments for spinner display."""
        # Guard: Ensure parsed is not None
        if parsed is None:
            raise ValueError("parsed cannot be None")
        context = CommandContext()

        # Extract command path information
        if hasattr(parsed, "_command_path"):
          command_path = parsed._command_path
          if len(command_path) >= 2:
            context.namespace, context.command = command_path[0], command_path[1]
            context.subcommand = command_path[2] if len(command_path) > 2 else None
          elif len(command_path) == 1:
            context.command = command_path[0]
        elif hasattr(parsed, "_function_name"):
          context.command = parsed._function_name

        # Categorize arguments by prefix
        global_args, group_args, command_args = {}, {}, {}
        for attr_name in dir(parsed):
          if attr_name.startswith("_"):
            continue
          value = getattr(parsed, attr_name)
          if value is None:
            continue

          if attr_name.startswith("_global_"):
            global_args[attr_name[8:]] = value
          elif attr_name.startswith("_subglobal_"):
            group_args[attr_name.split("_", 2)[-1]] = value
          else:
            command_args[attr_name] = value

        context.global_args = global_args
        context.group_args = group_args
        context.command_args = command_args
        context.positional_args = []

        return context

    def _execute_inner_class_command(self, parsed) -> Any:
        """Execute command using inner class pattern (parent + inner class + method)."""
        # Guard: Ensure parsed is not None
        if parsed is None:
            raise ValueError("parsed cannot be None")
        
        # Guard: Ensure _cli_function exists
        if not hasattr(parsed, "_cli_function"):
            raise ValueError("Missing _cli_function in parsed args")
        
        # Guard: Ensure _function_name exists
        if not hasattr(parsed, "_function_name"):
            raise ValueError("Missing _function_name in parsed args")
        
        # Guard: Ensure _command_path exists
        if not hasattr(parsed, "_command_path"):
            raise ValueError("Missing _command_path in parsed args")
        qualname_parts = parsed._cli_function.__qualname__.split(".")
        if len(qualname_parts) < 2:
          raise RuntimeError(
            f"Invalid method qualname for inner class method: {parsed._cli_function.__qualname__}"
          )

        inner_class_name = qualname_parts[-2]
        if self.target_class is None or not hasattr(self.target_class, inner_class_name):
          class_name = self.target_class.__name__ if self.target_class else "None"
          raise RuntimeError(
            f"Inner class {inner_class_name} not found in {class_name}"
          )

        inner_class_obj = getattr(self.target_class, inner_class_name)
        parent = self._create_parent(parsed)
        inner_instance = self._create_inner_instance(inner_class_obj, parsed._command_path, parsed, parent)

        return self._execute_method(inner_instance, parsed._function_name, parsed)

    def _execute_direct_method_command(self, parsed) -> Any:
        """Execute command using direct method from class."""
        # Guard: Ensure parsed is not None
        if parsed is None:
            raise ValueError("parsed cannot be None")
        class_instance = self._create_parent(parsed)
        return self._execute_method(class_instance, parsed._cli_function.__name__, parsed)

    def _create_parent(self, parsed) -> Any:
        """Create parent class instance with global arguments."""
        # Guard: Ensure parsed is not None
        if parsed is None:
            raise ValueError("parsed cannot be None")
        parent_sig = inspect.signature(self.target_class.__init__)
        parent_kwargs = {
          param_name: getattr(parsed, f"_global_{param_name}")
          for param_name, param in parent_sig.parameters.items()
          if param_name != "self"
          and param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
          and hasattr(parsed, f"_global_{param_name}")
        }

        if self.target_class is None:
          raise RuntimeError("Cannot create parent instance: target_class is None")
        
        try:
          return self.target_class(**parent_kwargs)
        except TypeError as e:
          class_name = self.target_class.__name__ if self.target_class else "None"
          raise RuntimeError(
            f"Cannot instantiate {class_name} with global args: {e}"
          ) from e

    def _create_inner_instance(
      self, inner_class: type, command_name: str, parsed, parent: Any
    ) -> Any:
        """Create inner class instance with sub-global arguments."""
        # Guard: Ensure inner_class is not None
        if inner_class is None:
            raise ValueError("inner_class cannot be None")
        
        # Guard: Ensure command_name is not None
        if command_name is None:
            raise ValueError("command_name cannot be None")
        
        # Guard: Ensure parsed is not None
        if parsed is None:
            raise ValueError("parsed cannot be None")
        
        # Guard: Ensure parent is not None
        if parent is None:
            raise ValueError("parent cannot be None")
        inner_sig = inspect.signature(inner_class.__init__)
        inner_kwargs = {
          param_name: getattr(parsed, f"_subglobal_{command_name}_{param_name}")
          for param_name, param in inner_sig.parameters.items()
          if param_name != "self"
          and param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
          and hasattr(parsed, f"_subglobal_{command_name}_{param_name}")
        }

        try:
          if self._is_system_inner_class(inner_class):
            cli_instance = getattr(parsed, "_cli_instance", None)
            if "cli_instance" in inner_sig.parameters:
              inner_kwargs["cli_instance"] = cli_instance
            return inner_class(**inner_kwargs)
          else:
            return inner_class(parent, **inner_kwargs)
        except TypeError as e:
          raise RuntimeError(
            f"Cannot instantiate {inner_class.__name__} with sub-global args: {e}"
          ) from e

    def _is_system_inner_class(self, inner_class: type) -> bool:
        """Check if this is a System inner class (from freyja.cli.system)."""
        # Guard: Ensure inner_class is not None
        if inner_class is None:
            raise ValueError("inner_class cannot be None")
        
        module_name = getattr(inner_class, "__module__", "")
        return "freyja.cli.system" in module_name

    def _execute_method(self, instance: Any, method_name: str, parsed) -> Any:
        """Execute method on instance with parsed arguments."""
        # Add spinner reference to instance for augment_status functionality
        if hasattr(self.spinner, "augment_status"):
            instance._execution_spinner = self.spinner

            # Add convenience method to instance
            def augment_status(message: str):
                """Augment the execution status display."""
                self.spinner.augment_status(message)

            instance.augment_status = augment_status

        bound_method = getattr(instance, method_name)
        method_kwargs = self._extract_method_arguments(bound_method, parsed)
        return bound_method(**method_kwargs)

    def _extract_method_arguments(self, method_or_function: Any, parsed) -> dict[str, Any]:
        """Extract method/function arguments from parsed FreyjaCLI arguments."""
        # Guard: Ensure method_or_function is not None
        if method_or_function is None:
            raise ValueError("method_or_function cannot be None")
        
        # Guard: Ensure parsed is not None
        if parsed is None:
            raise ValueError("parsed cannot be None")
        
        sig = inspect.signature(method_or_function)
        return {
          param_name: getattr(parsed, param_name.replace("-", "_"))
          for param_name, param in sig.parameters.items()
          if param_name != "self"
          and param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD)
          and hasattr(parsed, param_name.replace("-", "_"))
        }

    def execute_command(self, parsed, target_mode) -> Any:
        """Main command execution dispatcher with spinner and output capture."""
        # Build command context for spinner
        command_context = self._build_command_context(parsed)

        # Start spinner
        with self.spinner.execute(command_context):
            # Make augment_status available to command implementations
            if hasattr(parsed, "_cli_instance") and parsed._cli_instance:
                # Store spinner reference for augment_status method
                parsed._cli_instance._execution_spinner = self.spinner

            success = True
            result = None

            # Get command name for output formatting (before spinner stops)
            command_name = self.spinner._format_command_name()

            # Only use output capture if explicitly enabled
            if self.enable_output_capture and self.output_capture:
                # Capture output during execution
                self.output_capture.start()
                try:
                    # Check if this is a hierarchical command with command path
                    if hasattr(parsed, "_command_path"):
                        # Execute inner class method
                        result = self._execute_inner_class_command(parsed)
                    else:
                        # Execute direct method from class
                        result = self._execute_direct_method_command(parsed)
                except Exception:
                    success = False
                    raise
                finally:
                    # Get captured output before stopping
                    stdout_content, stderr_content = self.output_capture.stop()

                # Display output conditionally
                if self.output_formatter and self.output_formatter.should_display_output(self.verbose, success):
                    self.output_formatter.format_output(
                        command_name, stdout_content, stderr_content
                    )
            else:
                # Execute commands directly without output capture - output flows naturally to user
                # Check if this is a hierarchical command with command path
                if hasattr(parsed, "_command_path"):
                    # Execute inner class method
                    result = self._execute_inner_class_command(parsed)
                else:
                    # Execute direct method from class
                    result = self._execute_direct_method_command(parsed)

        return result

    def _handle_execution_error(self, parsed, error: Exception) -> int:
        """Handle execution errors with appropriate logging and return codes."""
        # Guard: Ensure parsed is not None
        if parsed is None:
            raise ValueError("parsed cannot be None")
        
        # Guard: Ensure error is not None
        if error is None:
            raise ValueError("error cannot be None")
        
        function_name = getattr(parsed, "_function_name", "unknown")
        print(f"Error executing {function_name}: {error}", file=sys.stderr)
        if getattr(parsed, "verbose", False):
          traceback.print_exc()
        return 1
