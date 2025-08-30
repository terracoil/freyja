"""CLI execution coordination service.

Handles argument parsing and command execution coordination.
Extracted from CLI class to reduce its size and improve separation of concerns.
"""
import sys
from typing import *

from ..enums.target_mode import TargetMode


class CliExecutionCoordinator:
  """Coordinates CLI argument parsing and command execution."""

  def __init__(self, target_mode: TargetMode, executors: Dict[str, Any]):
    """Initialize execution coordinator."""
    self.target_mode = target_mode
    self.executors = executors
    self.use_inner_class_pattern = False
    self.inner_class_metadata = {}
    self.discovered_commands = []

  def parse_and_execute(self, parser, args: Optional[List[str]]) -> Any:
    """Parse arguments and execute command."""
    result = None

    try:
      parsed = parser.parse_args(args)

      # Debug: Check what attributes are available
      # parsed_attrs = [attr for attr in dir(parsed) if not attr.startswith('_')]
      # print(f"DEBUG: parsed attributes: {parsed_attrs}")
      # print(f"DEBUG: parsed.__dict__: {parsed.__dict__}")

      if not hasattr(parsed, '_cli_function'):
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
      if isinstance(e, (ValueError, KeyError)) and 'parsed' not in locals():
        # Parsing errors should raise SystemExit like argparse does
        print(f"Error: {e}")
        raise SystemExit(2)
      else:
        # Other execution errors
        result = self._handle_execution_error(parsed if 'parsed' in locals() else None, e)

    return result

  def _handle_no_command(self, parser, parsed) -> int:
    """Handle case where no command was specified."""
    if hasattr(parsed, '_complete') and parsed._complete:
      return 0  # Completion mode - don't show help

    # Check for --help flag explicitly
    if hasattr(parsed, 'help') and parsed.help:
      parser.print_help()
      return 0

    # Default: show help and return success
    parser.print_help()
    return 0

  def _execute_command(self, parsed) -> Any:
    """Execute the command from parsed arguments."""
    if self.target_mode == TargetMode.MULTI_CLASS:
      return self._execute_multi_class_command(parsed)
    else:
      # Single class or module execution
      executor = self.executors.get('primary')
      if not executor:
        raise RuntimeError("No executor available for command execution")

      return executor.execute_command(
        parsed=parsed,
        target_mode=self.target_mode,
        use_inner_class_pattern=self.use_inner_class_pattern,
        inner_class_metadata=self.inner_class_metadata
      )

  def _execute_multi_class_command(self, parsed) -> Any:
    """Execute command for multi-class CLI."""
    function_name = parsed._function_name
    source_class = self._find_source_class_for_function(function_name)

    if not source_class:
      raise ValueError(f"Could not find source class for function: {function_name}")

    executor = self.executors.get(source_class)

    if not executor:
      raise ValueError(f"No executor found for class: {source_class.__name__}")

    return executor.execute_command(
      parsed=parsed,
      target_mode=TargetMode.CLASS,
      use_inner_class_pattern=self.use_inner_class_pattern,
      inner_class_metadata=self.inner_class_metadata
    )

  def _find_source_class_for_function(self, function_name: str) -> Optional[Type]:
    """Find the source class for a given function name."""
    for command in self.discovered_commands:
      # Check if this command matches the function name
      # Handle both original names and full hierarchical names
      if (command.original_name == function_name or 
          command.name == function_name or 
          command.name.endswith(f'--{function_name}')):
        source_class = command.metadata.get('source_class')
        if source_class:
          return source_class
    return None

  def _handle_execution_error(self, parsed, error: Exception) -> int:
    """Handle command execution errors."""
    if isinstance(error, KeyboardInterrupt):
      print("\nOperation cancelled by user")
      return 130  # Standard exit code for SIGINT

    print(f"Error executing command: {error}")
    
    if parsed and hasattr(parsed, '_function_name'):
      print(f"Function: {parsed._function_name}")
    
    return 1

  @staticmethod
  def check_no_color_flag(args: List[str]) -> bool:
    """Check if --no-color flag is present in arguments."""
    return '--no-color' in args or '-n' in args