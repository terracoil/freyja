"""FreyjaCLI execution coordination service.

Handles argument parsing and command execution coordination.
Extracted from FreyjaCLI class to reduce its size and improve separation of concerns.
"""
from typing import *

from .enums import TargetMode


class ExecutionCoordinator:
  """Coordinates FreyjaCLI argument parsing and command execution."""

  def __init__(self, target_mode: TargetMode, executors: Dict[str, Any]):
    """Initialize execution coordinator."""
    self.target_mode = target_mode
    self.executors = executors
    self.command_tree = None
    self.cli_instance = None

  def parse_and_execute(self, parser, args: Optional[List[str]]) -> Any:
    """Parse arguments and execute command."""
    result = None

    # Get actual args (convert None to sys.argv[1:] like argparse does)
    import sys
    actual_args = args if args is not None else sys.argv[1:]

    # Check for completion request first
    if '--_complete' in actual_args:
      return self._handle_completion_request()

    # Check if this is a hierarchical command that needs subgroup help
    if actual_args and self._should_show_subgroup_help(parser, actual_args):
      return self._show_subgroup_help(parser, actual_args)

    try:
      parsed = parser.parse_args(args)

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
    # Inject CLI instance for system commands
    self._inject_cli_instance(parsed)
    
    # Check if we have multiple classes (multiple executors)
    if len(self.executors) > 1 and 'primary' not in self.executors:
      return self._execute_multi_class_command(parsed)
    else:
      # Single class or module execution
      executor = self.executors.get('primary')
      if not executor:
        raise RuntimeError("No executor available for command execution")

      return executor.execute_command(
        parsed=parsed,
        target_mode=self.target_mode
      )

  def _inject_cli_instance(self, parsed) -> None:
    """Inject CLI instance into parsed arguments for system commands."""
    # Check if this is a system command that needs CLI instance
    if hasattr(parsed, '_command_path') and getattr(parsed, '_command_path', '').startswith('system'):
      # Inject CLI instance
      if self.cli_instance:
        parsed._cli_instance = self.cli_instance

  def _execute_multi_class_command(self, parsed) -> Any:
    """Execute command for multiple-class FreyjaCLI."""
    function_name = parsed._function_name
    source_class = self._find_source_class_for_function(function_name)

    if not source_class:
      raise ValueError(f"Could not find source class for function: {function_name}")

    executor = self.executors.get(source_class)

    if not executor:
      raise ValueError(f"No executor found for class: {source_class.__name__}")

    return executor.execute_command(
      parsed=parsed,
      target_mode=TargetMode.CLASS
    )

  def _find_source_class_for_function(self, function_name: str) -> Optional[Type]:
    """Find the source class for a given function name."""
    if self.command_tree:
      return self.command_tree.find_source_class(function_name)
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

  def _should_show_subgroup_help(self, parser, args: List[str]) -> bool:
    """Check if args represent a hierarchical command that needs subgroup help."""
    # Don't interfere with explicit help requests
    if '--help' in args or '-h' in args:
      return False
    
    # Check if we have a hierarchical path that exists but needs a final command
    try:
      parsed = parser.parse_args(args)
      # Check if parsing succeeded but we landed on a subgroup that has subcommands
      # but no final command was chosen (no _cli_function attribute)
      if not hasattr(parsed, '_cli_function'):
        return self._is_hierarchical_path(parser, args)
      return False  # Has _cli_function, so it's a complete command
    except SystemExit:
      # If parsing failed, this might still be a hierarchical path issue
      return self._is_hierarchical_path(parser, args)

  def _is_hierarchical_path(self, parser, args: List[str]) -> bool:
    """Check if args represent a valid hierarchical path to a subgroup."""
    if not args:
      return False
      
    # Walk through the parser structure to see if this path exists
    current_parser = parser
    for i, arg in enumerate(args):
      if not hasattr(current_parser, '_subparsers'):
        return False
        
      subparsers_action = None
      for action in current_parser._actions:
        if hasattr(action, 'choices') and action.choices and arg in action.choices:
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
      if hasattr(action, 'choices'):
        return True
    return False

  def _show_subgroup_help(self, parser, args: List[str]) -> int:
    """Show help for a specific subgroup by invoking subparser help."""
    # Navigate to the subparser and show its help
    current_parser = parser
    
    for arg in args:
      for action in current_parser._actions:
        if hasattr(action, 'choices') and action.choices and arg in action.choices:
          current_parser = action.choices[arg]
          break
    
    # Show help for the final subparser
    current_parser.print_help()
    return 0

  def _handle_completion_request(self):
    """Handle shell completion requests."""
    import os
    import sys
    from pathlib import Path
    
    # Determine which shell type is requesting
    shell_type = os.environ.get('_FREYJA_COMPLETE', '')
    
    if not shell_type:
      # No completion environment set, just return
      return 0
    
    # Get the command tree for dynamic completion
    if not self.command_tree:
      return 0
    
    # Get completion words from environment
    words_str = os.environ.get('COMP_WORDS_STR', '')
    cword_num = int(os.environ.get('COMP_CWORD_NUM', '0'))
    
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
        if not word.startswith('-'):
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
      cli=self.cli_instance
    )
    
    # Import the appropriate completion handler
    if shell_type == 'zsh':
      from freyja.completion.zsh import ZshCompletionHandler
      handler = ZshCompletionHandler(self.cli_instance)
    else:
      # Use bash handler as fallback
      from freyja.completion.bash import BashCompletionHandler
      handler = BashCompletionHandler(self.cli_instance)
    
    # Get completions
    completions = handler.get_completions(context)
    
    # Output completions
    for completion in completions:
      print(completion)
    
    sys.exit(0)

  @staticmethod
  def check_no_color_flag(args: List[str]) -> bool:
    """Check if --no-color flag is present in arguments."""
    return '--no-color' in args or '-n' in args