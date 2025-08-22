# Auto-generate CLI from function signatures and docstrings.
import argparse
import enum
import inspect
import os
import sys
import traceback
from collections.abc import Callable
from typing import Any, Union

from .docstring_parser import extract_function_help
from .formatter import HierarchicalHelpFormatter


class CLI:
  """Automatically generates CLI from module functions using introspection."""

  # Class-level storage for command group descriptions
  _command_group_descriptions = {}

  @classmethod
  def CommandGroup(cls, description: str):
    """Decorator to provide documentation for top-level command groups.

    Usage:
        @CLI.CommandGroup("User management operations")
        def user__create(username: str, email: str):
            pass

        @CLI.CommandGroup("Database operations")
        def db__backup(output_file: str):
            pass

    :param description: Description text for the command group
    """
    def decorator(func):
      # Extract the group name from the function name
      func_name = func.__name__
      if '__' in func_name:
        group_name = func_name.split('__')[0].replace('_', '-')
        cls._command_group_descriptions[group_name] = description
      return func
    return decorator

  def __init__(self, target_module, title: str, function_filter: Callable | None = None, theme=None,
      theme_tuner: bool = False, enable_completion: bool = True):
    """Initialize CLI generator with module functions, title, and optional customization.

    :param target_module: Module containing functions to generate CLI from
    :param title: CLI application title
    :param function_filter: Optional filter function for selecting functions
    :param theme: Optional theme for colored output
    :param theme_tuner: If True, adds a built-in theme tuning command
    :param enable_completion: If True, enables shell completion support
    """
    self.target_module=target_module
    self.title=title
    self.theme=theme
    self.theme_tuner=theme_tuner
    self.enable_completion=enable_completion
    self.function_filter=function_filter or self._default_function_filter
    self._completion_handler=None
    self._discover_functions()

  def _default_function_filter(self, name: str, obj: Any) -> bool:
    """Default filter: include non-private callable functions defined in this module."""
    return (
        not name.startswith('_') and
        callable(obj) and
        not inspect.isclass(obj) and
        inspect.isfunction(obj) and
        obj.__module__ == self.target_module.__name__  # Exclude imported functions
    )

  def _discover_functions(self):
    """Auto-discover functions from module using the filter."""
    self.functions={}
    for name, obj in inspect.getmembers(self.target_module):
      if self.function_filter(name, obj):
        self.functions[name]=obj

    # Optionally add built-in theme tuner
    if self.theme_tuner:
      self._add_theme_tuner_function()

    # Build hierarchical command structure
    self.commands=self._build_command_tree()

  def _add_theme_tuner_function(self):
    """Add built-in theme tuner function to available commands."""

    def tune_theme(base_theme: str = "universal"):
      """Interactive theme color tuning with real-time preview and RGB export.

      :param base_theme: Base theme to start with (universal or colorful, defaults to universal)
      """
      from auto_cli.theme.theme_tuner import run_theme_tuner
      run_theme_tuner(base_theme)

    # Add to functions with a hierarchical name to keep it organized
    self.functions['cli__tune-theme']=tune_theme

  def _init_completion(self, shell: str = None):
    """Initialize completion handler if enabled.

    :param shell: Target shell (auto-detect if None)
    """
    if not self.enable_completion:
      return

    try:
      from .completion import get_completion_handler
      self._completion_handler = get_completion_handler(self, shell)
    except ImportError:
      # Completion module not available
      self.enable_completion = False

  def _is_completion_request(self) -> bool:
    """Check if this is a completion request."""
    import os
    return (
      '--_complete' in sys.argv or
      os.environ.get('_AUTO_CLI_COMPLETE') is not None
    )

  def _handle_completion(self) -> None:
    """Handle completion request and exit."""
    if not self._completion_handler:
      self._init_completion()

    if not self._completion_handler:
      sys.exit(1)

    # Parse completion context from command line and environment
    from .completion.base import CompletionContext

    # Get completion context
    words = sys.argv[:]
    current_word = ""
    cursor_pos = 0

    # Handle --_complete flag
    if '--_complete' in words:
      complete_idx = words.index('--_complete')
      words = words[:complete_idx]  # Remove --_complete and after
      if complete_idx < len(sys.argv) - 1:
        current_word = sys.argv[complete_idx + 1] if complete_idx + 1 < len(sys.argv) else ""

    # Extract subcommand path
    subcommand_path = []
    if len(words) > 1:
      for word in words[1:]:
        if not word.startswith('-'):
          subcommand_path.append(word)

    # Create parser for context
    parser = self.create_parser(no_color=True)

    # Create completion context
    context = CompletionContext(
      words=words,
      current_word=current_word,
      cursor_position=cursor_pos,
      subcommand_path=subcommand_path,
      parser=parser,
      cli=self
    )

    # Get completions and output them
    completions = self._completion_handler.get_completions(context)
    for completion in completions:
      print(completion)

    sys.exit(0)

  def install_completion(self, shell: str = None, force: bool = False) -> bool:
    """Install shell completion for this CLI.

    :param shell: Target shell (auto-detect if None)
    :param force: Force overwrite existing completion
    :return: True if installation successful
    """
    if not self.enable_completion:
      print("Completion is disabled for this CLI.", file=sys.stderr)
      return False

    if not self._completion_handler:
      self._init_completion()

    if not self._completion_handler:
      print("Completion handler not available.", file=sys.stderr)
      return False

    from .completion.installer import CompletionInstaller

    # Extract program name from sys.argv[0]
    prog_name = os.path.basename(sys.argv[0])
    if prog_name.endswith('.py'):
      prog_name = prog_name[:-3]

    installer = CompletionInstaller(self._completion_handler, prog_name)
    return installer.install(shell, force)

  def _show_completion_script(self, shell: str) -> int:
    """Show completion script for specified shell.

    :param shell: Target shell
    :return: Exit code (0 for success, 1 for error)
    """
    if not self.enable_completion:
      print("Completion is disabled for this CLI.", file=sys.stderr)
      return 1

    # Initialize completion handler for specific shell
    self._init_completion(shell)

    if not self._completion_handler:
      print("Completion handler not available.", file=sys.stderr)
      return 1

    # Extract program name from sys.argv[0]
    prog_name = os.path.basename(sys.argv[0])
    if prog_name.endswith('.py'):
      prog_name = prog_name[:-3]

    try:
      script = self._completion_handler.generate_script(prog_name)
      print(script)
      return 0
    except Exception as e:
      print(f"Error generating completion script: {e}", file=sys.stderr)
      return 1

  def _build_command_tree(self) -> dict[str, dict]:
    """Build hierarchical command tree from discovered functions."""
    commands={}

    for func_name, func_obj in self.functions.items():
      if '__' in func_name:
        # Parse hierarchical command: user__create or admin__user__reset
        self._add_to_command_tree(commands, func_name, func_obj)
      else:
        # Flat command: hello, count_animals → hello, count-animals
        cli_name=func_name.replace('_', '-')
        commands[cli_name]={
          'type':'flat',
          'function':func_obj,
          'original_name':func_name
        }

    return commands

  def _add_to_command_tree(self, commands: dict, func_name: str, func_obj):
    """Add function to command tree, creating nested structure as needed."""
    # Split by double underscore: admin__user__reset_password → [admin, user, reset_password]
    parts=func_name.split('__')

    # Navigate/create tree structure
    current_level=commands
    path=[]

    for i, part in enumerate(parts[:-1]):  # All but the last part are groups
      cli_part=part.replace('_', '-')  # Convert underscores to dashes
      path.append(cli_part)

      if cli_part not in current_level:
        current_level[cli_part]={
          'type':'group',
          'subcommands':{}
        }

      current_level=current_level[cli_part]['subcommands']

    # Add the final command
    final_command=parts[-1].replace('_', '-')
    current_level[final_command]={
      'type':'command',
      'function':func_obj,
      'original_name':func_name,
      'command_path':path + [final_command]
    }

  def _get_arg_type_config(self, annotation: type) -> dict[str, Any]:
    """Convert type annotation to argparse configuration."""
    from pathlib import Path
    from typing import get_args, get_origin

    # Handle Optional[Type] -> get the actual type
    # Handle both typing.Union and types.UnionType (Python 3.10+)
    origin=get_origin(annotation)
    if origin is Union or str(origin) == "<class 'types.UnionType'>":
      args=get_args(annotation)
      # Optional[T] is Union[T, NoneType]
      if len(args) == 2 and type(None) in args:
        annotation=next(arg for arg in args if arg is not type(None))

    if annotation in (str, int, float):
      return {'type':annotation}
    elif annotation == bool:
      return {'action':'store_true'}
    elif annotation == Path:
      return {'type':Path}
    elif inspect.isclass(annotation) and issubclass(annotation, enum.Enum):
      return {
        'type':lambda x:annotation[x.split('.')[-1]],
        'choices':list(annotation),
        'metavar':f"{{{','.join(e.name for e in annotation)}}}"
      }
    return {}

  def _add_function_args(self, parser: argparse.ArgumentParser, fn: Callable):
    """Add function parameters as CLI arguments with help from docstring."""
    sig=inspect.signature(fn)
    _, param_help=extract_function_help(fn)

    for name, param in sig.parameters.items():
      # Skip *args and **kwargs - they can't be CLI arguments
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue

      arg_config: dict[str, Any]={
        'dest':name,
        'help':param_help.get(name, f"{name} parameter")
      }

      # Handle type annotations
      if param.annotation != param.empty:
        type_config=self._get_arg_type_config(param.annotation)
        arg_config.update(type_config)

      # Handle defaults - determine if argument is required
      if param.default != param.empty:
        arg_config['default']=param.default
        # Don't set required for optional args
      else:
        arg_config['required']=True

      # Add argument with kebab-case flag name
      flag=f"--{name.replace('_', '-')}"
      parser.add_argument(flag, **arg_config)

  def create_parser(self, no_color: bool = False) -> argparse.ArgumentParser:
    """Create argument parser with hierarchical subcommand support."""
    # Create a custom formatter class that includes the theme (or no theme if no_color)
    effective_theme=None if no_color else self.theme

    def create_formatter_with_theme(*args, **kwargs):
      formatter=HierarchicalHelpFormatter(*args, theme=effective_theme, **kwargs)
      return formatter

    parser=argparse.ArgumentParser(
      description=self.title,
      formatter_class=create_formatter_with_theme
    )

    # Store reference to parser in the formatter class so it can access all actions
    # We'll do this after the parser is fully configured
    def patch_formatter_with_parser_actions():
      original_get_formatter = parser._get_formatter
      def patched_get_formatter():
        formatter = original_get_formatter()
        # Give the formatter access to the parser's actions
        formatter._parser_actions = parser._actions
        return formatter
      parser._get_formatter = patched_get_formatter

    # We need to patch this after the parser is fully set up
    # Store the patch function for later use

    # Monkey-patch the parser to style the title
    original_format_help=parser.format_help

    def patched_format_help():
      # Get original help
      original_help=original_format_help()

      # Apply title styling if we have a theme
      if effective_theme and self.title in original_help:
        from .theme import ColorFormatter
        color_formatter=ColorFormatter()
        styled_title=color_formatter.apply_style(self.title, effective_theme.title)
        # Replace the plain title with the styled version
        original_help=original_help.replace(self.title, styled_title)

      return original_help

    parser.format_help=patched_format_help

    # Add global verbose flag
    parser.add_argument(
      "-v", "--verbose",
      action="store_true",
      help="Enable verbose output"
    )

    # Add global no-color flag
    parser.add_argument(
      "-n", "--no-color",
      action="store_true",
      help="Disable colored output"
    )

    # Add completion-related hidden arguments
    if self.enable_completion:
      parser.add_argument(
        "--_complete",
        action="store_true",
        help=argparse.SUPPRESS  # Hide from help
      )

      parser.add_argument(
        "--install-completion",
        action="store_true",
        help="Install shell completion for this CLI"
      )

      parser.add_argument(
        "--show-completion",
        metavar="SHELL",
        help="Show completion script for specified shell (choices: bash, zsh, fish, powershell)"
      )

    # Main subparsers
    subparsers=parser.add_subparsers(
      title='COMMANDS',
      dest='command',
      required=False,  # Allow no command to show help
      help='Available commands',
      metavar=''  # Remove the comma-separated list
    )

    # Store theme reference for consistency in subparsers
    subparsers._theme=effective_theme

    # Add commands (flat, groups, and nested groups)
    self._add_commands_to_parser(subparsers, self.commands, [])

    # Now that the parser is fully configured, patch the formatter to have access to actions
    patch_formatter_with_parser_actions()

    return parser

  def _add_commands_to_parser(self, subparsers, commands: dict, path: list):
    """Recursively add commands to parser, supporting arbitrary nesting."""
    for name, info in commands.items():
      if info['type'] == 'flat':
        self._add_flat_command(subparsers, name, info)
      elif info['type'] == 'group':
        self._add_command_group(subparsers, name, info, path + [name])
      elif info['type'] == 'command':
        self._add_leaf_command(subparsers, name, info)

  def _add_flat_command(self, subparsers, name: str, info: dict):
    """Add a flat command to subparsers."""
    func=info['function']
    desc, _=extract_function_help(func)

    # Get the formatter class from the parent parser to ensure consistency
    effective_theme=getattr(subparsers, '_theme', self.theme)

    def create_formatter_with_theme(*args, **kwargs):
      return HierarchicalHelpFormatter(*args, theme=effective_theme, **kwargs)

    sub=subparsers.add_parser(
      name,
      help=desc,
      description=desc,
      formatter_class=create_formatter_with_theme
    )
    sub._command_type='flat'

    # Store theme reference for consistency
    sub._theme=effective_theme

    self._add_function_args(sub, func)
    sub.set_defaults(_cli_function=func, _function_name=info['original_name'])

  def _add_command_group(self, subparsers, name: str, info: dict, path: list):
    """Add a command group with subcommands (supports nesting)."""
    # Check for CommandGroup decorator description, otherwise use default
    if name in self._command_group_descriptions:
      group_help = self._command_group_descriptions[name]
    else:
      group_help=f"{name.title().replace('-', ' ')} operations"

    # Get the formatter class from the parent parser to ensure consistency
    effective_theme=getattr(subparsers, '_theme', self.theme)

    def create_formatter_with_theme(*args, **kwargs):
      return HierarchicalHelpFormatter(*args, theme=effective_theme, **kwargs)

    group_parser=subparsers.add_parser(
      name,
      help=group_help,
      formatter_class=create_formatter_with_theme
    )

    # Store CommandGroup description for formatter to use
    if name in self._command_group_descriptions:
      group_parser._command_group_description = self._command_group_descriptions[name]
    group_parser._command_type='group'

    # Store theme reference for consistency
    group_parser._theme=effective_theme

    # Store subcommand info for help formatting
    subcommand_help={}
    for subcmd_name, subcmd_info in info['subcommands'].items():
      if subcmd_info['type'] == 'command':
        func=subcmd_info['function']
        desc, _=extract_function_help(func)
        subcommand_help[subcmd_name]=desc
      elif subcmd_info['type'] == 'group':
        # For nested groups, show as group with subcommands
        subcommand_help[subcmd_name]=f"{subcmd_name.title().replace('-', ' ')} operations"

    group_parser._subcommands=subcommand_help
    group_parser._subcommand_details=info['subcommands']

    # Create subcommand parsers with enhanced help
    dest_name='_'.join(path) + '_subcommand' if len(path) > 1 else 'subcommand'
    sub_subparsers=group_parser.add_subparsers(
      title=f'{name.title().replace("-", " ")} COMMANDS',
      dest=dest_name,
      required=False,
      help=f'Available {name} commands',
      metavar=''
    )

    # Store reference for enhanced help formatting
    sub_subparsers._enhanced_help=True
    sub_subparsers._subcommand_details=info['subcommands']

    # Store theme reference for consistency in nested subparsers
    sub_subparsers._theme=effective_theme

    # Recursively add subcommands
    self._add_commands_to_parser(sub_subparsers, info['subcommands'], path)

  def _add_leaf_command(self, subparsers, name: str, info: dict):
    """Add a leaf command (actual executable function)."""
    func=info['function']
    desc, _=extract_function_help(func)

    # Get the formatter class from the parent parser to ensure consistency
    effective_theme=getattr(subparsers, '_theme', self.theme)

    def create_formatter_with_theme(*args, **kwargs):
      return HierarchicalHelpFormatter(*args, theme=effective_theme, **kwargs)

    sub=subparsers.add_parser(
      name,
      help=desc,
      description=desc,
      formatter_class=create_formatter_with_theme
    )
    sub._command_type='command'

    # Store theme reference for consistency
    sub._theme=effective_theme

    self._add_function_args(sub, func)
    sub.set_defaults(
      _cli_function=func,
      _function_name=info['original_name'],
      _command_path=info['command_path']
    )

  def run(self, args: list | None = None) -> Any:
    """Parse arguments and execute the appropriate function."""
    # Check for completion requests early
    if self.enable_completion and self._is_completion_request():
      self._handle_completion()

    # First, do a preliminary parse to check for --no-color flag
    # This allows us to disable colors before any help output is generated
    no_color=False
    if args:
      no_color='--no-color' in args or '-n' in args

    parser=self.create_parser(no_color=no_color)

    try:
      parsed=parser.parse_args(args)

      # Handle completion-related commands
      if self.enable_completion:
        if hasattr(parsed, 'install_completion') and parsed.install_completion:
          return 0 if self.install_completion() else 1

        if hasattr(parsed, 'show_completion') and parsed.show_completion:
          # Validate shell choice
          valid_shells = ["bash", "zsh", "fish", "powershell"]
          if parsed.show_completion not in valid_shells:
            print(f"Error: Invalid shell '{parsed.show_completion}'. Valid choices: {', '.join(valid_shells)}", file=sys.stderr)
            return 1
          return self._show_completion_script(parsed.show_completion)

      # Handle missing command/subcommand scenarios
      if not hasattr(parsed, '_cli_function'):
        return self._handle_missing_command(parser, parsed)

      # Execute the command
      return self._execute_command(parsed)

    except SystemExit:
      # Let argparse handle its own exits (help, errors, etc.)
      raise
    except Exception as e:
      # Handle execution errors gracefully
      return self._handle_execution_error(parsed, e)

  def _handle_missing_command(self, parser: argparse.ArgumentParser, parsed) -> int:
    """Handle cases where no command or subcommand was provided."""
    # Analyze parsed arguments to determine what level of help to show
    command_parts=[]
    result=0

    # Check for command and nested subcommands
    if hasattr(parsed, 'command') and parsed.command:
      command_parts.append(parsed.command)

      # Check for nested subcommands
      for attr_name in dir(parsed):
        if attr_name.endswith('_subcommand') and getattr(parsed, attr_name):
          # Extract command path from attribute names
          if attr_name == 'subcommand':
            # Simple case: user subcommand
            subcommand=getattr(parsed, attr_name)
            if subcommand:
              command_parts.append(subcommand)
          else:
            # Complex case: user_subcommand for nested groups
            path_parts=attr_name.replace('_subcommand', '').split('_')
            command_parts.extend(path_parts)
            subcommand=getattr(parsed, attr_name)
            if subcommand:
              command_parts.append(subcommand)

    if command_parts:
      # Show contextual help for partial command
      result=self._show_contextual_help(parser, command_parts)
    else:
      # No command provided - show main help
      parser.print_help()
      result=0

    return result

  def _show_contextual_help(self, parser: argparse.ArgumentParser, command_parts: list) -> int:
    """Show help for a specific command level."""
    # Navigate to the appropriate subparser
    current_parser=parser
    result=0

    for part in command_parts:
      # Find the subparser for this command part
      found_parser=None
      for action in current_parser._actions:
        if isinstance(action, argparse._SubParsersAction):
          if part in action.choices:
            found_parser=action.choices[part]
            break

      if found_parser:
        current_parser=found_parser
      else:
        print(f"Unknown command: {' '.join(command_parts[:command_parts.index(part) + 1])}", file=sys.stderr)
        parser.print_help()
        result=1
        break

    if result == 0:
      current_parser.print_help()

    return result

  def _execute_command(self, parsed) -> Any:
    """Execute the parsed command with its arguments."""
    fn=parsed._cli_function
    sig=inspect.signature(fn)

    # Build kwargs from parsed arguments
    kwargs={}
    for param_name in sig.parameters:
      # Skip *args and **kwargs - they can't be CLI arguments
      param=sig.parameters[param_name]
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue

      # Convert kebab-case back to snake_case for function call
      attr_name=param_name.replace('-', '_')
      if hasattr(parsed, attr_name):
        value=getattr(parsed, attr_name)
        kwargs[param_name]=value

    # Execute function and return result
    return fn(**kwargs)

  def _handle_execution_error(self, parsed, error: Exception) -> int:
    """Handle execution errors gracefully."""
    function_name=getattr(parsed, '_function_name', 'unknown')
    print(f"Error executing {function_name}: {error}", file=sys.stderr)

    if getattr(parsed, 'verbose', False):
      traceback.print_exc()

    return 1

  def display(self):
    """Legacy method for backward compatibility - runs the CLI."""
    exit_code=0
    try:
      result=self.run()
      if isinstance(result, int):
        exit_code=result
    except SystemExit:
      # Argparse already handled the exit
      exit_code=0
    except Exception as e:
      print(f"Unexpected error: {e}", file=sys.stderr)
      traceback.print_exc()
      exit_code=1

    sys.exit(exit_code)
