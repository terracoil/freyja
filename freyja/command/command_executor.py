"""Command execution service for FreyjaCLI applications.

Handles the execution of different command types (direct methods, inner class methods)
by creating appropriate instances and invoking methods with parsed arguments.
"""

import inspect
import sys
from typing import Any

from ..utils.spinner import ExecutionSpinner, CommandContext
from ..utils.output_capture import OutputCapture, OutputFormatter


class CommandExecutor:
  """Centralized service for executing FreyjaCLI commands with different patterns."""

  def __init__(self, target_class: type | None = None, color_formatter=None, verbose: bool = False):
    """Initialize command executor with target information.

    :param target_class: Class containing methods to execute
    :param color_formatter: ColorFormatter instance for styling output
    :param verbose: Whether to run in verbose mode
    """
    self.target_class = target_class
    self.color_formatter = color_formatter
    self.verbose = verbose
    self.spinner = ExecutionSpinner(color_formatter, verbose)
    self.output_capture = OutputCapture()
    self.output_formatter = OutputFormatter(color_formatter)

  def _build_command_context(self, parsed) -> CommandContext:
    """Build command context from parsed arguments for spinner display.
    
    :param parsed: Parsed arguments object
    :return: CommandContext for spinner display
    """
    context = CommandContext()
    
    # Extract command information
    if hasattr(parsed, '_command_path'):
      # Hierarchical command
      command_path = parsed._command_path
      if len(command_path) >= 2:
        context.namespace = command_path[0]
        context.command = command_path[1]
        if len(command_path) > 2:
          context.subcommand = command_path[2]
      elif len(command_path) == 1:
        context.command = command_path[0]
    elif hasattr(parsed, '_function_name'):
      # Direct method command
      context.command = parsed._function_name
    
    # Extract arguments by type
    global_args = {}
    group_args = {}  
    command_args = {}
    positional_args = []
    
    for attr_name in dir(parsed):
      if attr_name.startswith('_'):
        continue
        
      value = getattr(parsed, attr_name)
      if value is None:
        continue
        
      # Categorize arguments
      if attr_name.startswith('_global_'):
        param_name = attr_name[8:]  # Remove '_global_' prefix
        global_args[param_name] = value
      elif attr_name.startswith('_subglobal_'):
        param_name = attr_name.split('_', 2)[-1]  # Get parameter name after prefix
        group_args[param_name] = value
      else:
        # Check if this might be a positional argument or regular command argument
        # For now, treat non-prefixed as command arguments
        command_args[attr_name] = value
    
    context.global_args = global_args
    context.group_args = group_args  
    context.command_args = command_args
    context.positional_args = positional_args  # TODO: Extract positional args properly
    
    return context

  def _execute_inner_class_command(self, parsed) -> Any:
    """Execute command using inner class pattern.

    Creates main class instance, inner class instance, then invokes method.
    """
    method = parsed._cli_function
    original_name = parsed._function_name
    command_path = parsed._command_path

    # Extract inner class information from the method object
    # The method qualname can be:
    # - "OuterClass.InnerClass.method_name" (normal case, 3 parts)
    # - "InnerClass.method_name" (System class case, 2 parts)
    qualname_parts = method.__qualname__.split('.')
    if len(qualname_parts) < 2:
      raise RuntimeError(f"Invalid method qualname for inner class method: {method.__qualname__}")

    # For both cases, the inner class name is the second-to-last part
    inner_class_name = qualname_parts[-2]  # Get the inner class name

    # Find the actual inner class object from the main target class
    if not hasattr(self.target_class, inner_class_name):
      raise RuntimeError(f"Inner class {inner_class_name} not found in {self.target_class.__name__}")

    inner_class_obj = getattr(self.target_class, inner_class_name)

    # 1. Create main class instance with global arguments
    main = self._create_main(parsed)

    # 2. Create inner class instance with sub-global arguments
    inner_instance = self._create_inner_instance(inner_class_obj, command_path, parsed, main)

    # 3. Execute method with command arguments
    return self._execute_method(inner_instance, original_name, parsed)

  def _execute_direct_method_command(self, parsed) -> Any:
    """Execute command using direct method from class.

    Creates class instance with global arguments, then invokes method.
    """
    method = parsed._cli_function

    # Create class instance with global arguments
    class_instance = self._create_main(parsed)

    # Execute method with arguments
    return self._execute_method(class_instance, method.__name__, parsed)


  def _create_main(self, parsed) -> Any:
    """Create main class instance with global arguments."""
    main_kwargs = {}
    main_sig = inspect.signature(self.target_class.__init__)

    for param_name, param in main_sig.parameters.items():
      if param_name == 'self':
        continue
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue

      # Look for global argument
      global_attr = f'_global_{param_name}'
      if hasattr(parsed, global_attr):
        value = getattr(parsed, global_attr)
        main_kwargs[param_name] = value

    try:
      return self.target_class(**main_kwargs)
    except TypeError as e:
      raise RuntimeError(f"Cannot instantiate {self.target_class.__name__} with global args: {e}") from e

  def _create_inner_instance(self, inner_class: type, command_name: str, parsed, main: Any) -> Any:
    """Create inner class instance with sub-global arguments."""
    inner_kwargs = {}
    inner_sig = inspect.signature(inner_class.__init__)

    for param_name, param in inner_sig.parameters.items():
      if param_name == 'self':
        continue
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue

      # Look for sub-global argument
      subglobal_attr = f'_subglobal_{command_name}_{param_name}'
      if hasattr(parsed, subglobal_attr):
        value = getattr(parsed, subglobal_attr)
        inner_kwargs[param_name] = value

    try:
      # Special handling for System commands - they need CLI instance, not main class instance
      if self._is_system_inner_class(inner_class):
        # For System inner classes, pass CLI instance if available
        cli_instance = getattr(parsed, '_cli_instance', None)
        if 'cli_instance' in inner_sig.parameters:
          inner_kwargs['cli_instance'] = cli_instance
        return inner_class(**inner_kwargs)
      else:
        # Regular inner class - pass main class instance as first argument
        return inner_class(main, **inner_kwargs)
    except TypeError as e:
      raise RuntimeError(f"Cannot instantiate {inner_class.__name__} with sub-global args: {e}") from e

  def _is_system_inner_class(self, inner_class: type) -> bool:
    """Check if this is a System inner class."""
    # Check if the module path indicates this is a system command
    module_name = getattr(inner_class, '__module__', '')
    return 'freyja.cli.system' in module_name

  def _execute_method(self, instance: Any, method_name: str, parsed) -> Any:
    """Execute method on instance with parsed arguments."""
    # Add spinner reference to instance for augment_status functionality
    if hasattr(self.spinner, 'augment_status'):
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
    sig = inspect.signature(method_or_function)
    kwargs = {}

    for param_name, param in sig.parameters.items():
      if param_name == 'self':
        continue
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue

      # Look for method argument (no prefix, just the parameter name)
      attr_name = param_name.replace('-', '_')
      if hasattr(parsed, attr_name):
        value = getattr(parsed, attr_name)
        kwargs[param_name] = value

    return kwargs

  def execute_command(self, parsed, target_mode) -> Any:
    """Main command execution dispatcher with spinner and output capture."""
    # Build command context for spinner
    command_context = self._build_command_context(parsed)
    
    # Start spinner
    with self.spinner.execute(command_context):
      # Make augment_status available to command implementations
      if hasattr(parsed, '_cli_instance') and parsed._cli_instance:
        # Store spinner reference for augment_status method
        parsed._cli_instance._execution_spinner = self.spinner
      
      success = True
      result = None
      
      # Get command name for output formatting (before spinner stops)
      command_name = self.spinner._format_command_name()
      
      # Capture output during execution
      self.output_capture.start()
      try:
        # Check if this is a hierarchical command with command path
        if hasattr(parsed, '_command_path'):
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
      if self.output_formatter.should_display_output(self.verbose, success):
        self.output_formatter.format_output(command_name, stdout_content, stderr_content)
    
    return result

  def _handle_execution_error(self, parsed, error: Exception) -> int:
    """Handle execution errors with appropriate logging and return codes."""
    import traceback

    function_name = getattr(parsed, '_function_name', 'unknown')
    print(f"Error executing {function_name}: {error}", file=sys.stderr)

    if getattr(parsed, 'verbose', False):
      traceback.print_exc()

    return 1
