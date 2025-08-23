# Auto-generate CLI from function signatures and docstrings.
import argparse
import enum
import inspect
import os
import sys
import traceback
import types
import warnings
from collections.abc import Callable
from typing import Any, Optional, Type, Union

from .docstring_parser import extract_function_help, parse_docstring
from .formatter import HierarchicalHelpFormatter

Target = Union[types.ModuleType, Type[Any]]


class TargetMode(enum.Enum):
    """Target mode enum for CLI generation."""
    MODULE = 'module'
    CLASS = 'class'


class CLI:
  """Automatically generates CLI from module functions or class methods using introspection."""

  def __init__(self, target: Target, title: Optional[str] = None, function_filter: Optional[Callable] = None,
               method_filter: Optional[Callable] = None, theme=None, theme_tuner: bool = False,
               enable_completion: bool = True):
    """Initialize CLI generator with auto-detection of target type.

    :param target: Module or class containing functions/methods to generate CLI from
    :param title: CLI application title (auto-generated from class docstring if None for classes)
    :param function_filter: Optional filter function for selecting functions (module mode)
    :param method_filter: Optional filter function for selecting methods (class mode)
    :param theme: Optional theme for colored output
    :param theme_tuner: If True, adds a built-in theme tuning command
    :param enable_completion: If True, enables shell completion support
    """
    # Auto-detect target type
    if inspect.isclass(target):
      self.target_mode = TargetMode.CLASS
      self.target_class = target
      self.target_module = None
      self.title = title or self.__extract_class_title(target)
      self.method_filter = method_filter or self.__default_method_filter
      self.function_filter = None
    elif inspect.ismodule(target):
      self.target_mode = TargetMode.MODULE
      self.target_module = target
      self.target_class = None
      self.title = title or "CLI Application"
      self.function_filter = function_filter or self.__default_function_filter
      self.method_filter = None
    else:
      raise ValueError(f"Target must be a module or class, got {type(target).__name__}")

    self.theme = theme
    self.theme_tuner = theme_tuner
    self.enable_completion = enable_completion
    self._completion_handler = None

    # Discover functions/methods based on target mode
    if self.target_mode == TargetMode.MODULE:
      self.__discover_functions()
    else:
      self.__discover_methods()

  def display(self):
    """Legacy method for backward compatibility - runs the CLI."""
    self.run()

  def run(self, args: list | None = None) -> Any:
    """Parse arguments and execute the appropriate function."""
    # Check for completion requests early
    if self.enable_completion and self.__is_completion_request():
      self.__handle_completion()

    # First, do a preliminary parse to check for --no-color flag
    # This allows us to disable colors before any help output is generated
    no_color = False
    if args:
      no_color = '--no-color' in args or '-n' in args

    parser = self.create_parser(no_color=no_color)
    parsed = None

    try:
      parsed = parser.parse_args(args)

      # Handle completion-related commands
      if self.enable_completion:
        if hasattr(parsed, 'install_completion') and parsed.install_completion:
          return 0 if self.install_completion() else 1

        if hasattr(parsed, 'show_completion') and parsed.show_completion:
          # Validate shell choice
          valid_shells = ["bash", "zsh", "fish", "powershell"]
          if parsed.show_completion not in valid_shells:
            print(f"Error: Invalid shell '{parsed.show_completion}'. Valid choices: {', '.join(valid_shells)}",
                  file=sys.stderr)
            return 1
          return self.__show_completion_script(parsed.show_completion)

      # Handle missing command/subcommand scenarios
      if not hasattr(parsed, '_cli_function'):
        return self.__handle_missing_command(parser, parsed)

      # Execute the command
      return self.__execute_command(parsed)

    except SystemExit:
      # Let argparse handle its own exits (help, errors, etc.)
      raise
    except Exception as e:
      # Handle execution errors gracefully
      if parsed is not None:
        return self.__handle_execution_error(parsed, e)
      else:
        # If parsing failed, this is likely an argparse error - re-raise as SystemExit
        raise SystemExit(1)


  def __extract_class_title(self, cls: type) -> str:
    """Extract title from class docstring, similar to function docstring extraction."""
    if cls.__doc__:
      main_desc, _ = parse_docstring(cls.__doc__)
      return main_desc or cls.__name__
    return cls.__name__

  def __default_function_filter(self, name: str, obj: Any) -> bool:
    """Default filter: include non-private callable functions defined in this module."""
    return (
        not name.startswith('_') and
        callable(obj) and
        not inspect.isclass(obj) and
        inspect.isfunction(obj) and
        obj.__module__ == self.target_module.__name__  # Exclude imported functions
    )

  def __default_method_filter(self, name: str, obj: Any) -> bool:
    """Default filter: include non-private callable methods defined in target class."""
    return (
        not name.startswith('_') and
        callable(obj) and
        (inspect.isfunction(obj) or inspect.ismethod(obj)) and
        hasattr(obj, '__qualname__') and
        self.target_class.__name__ in obj.__qualname__  # Check if class name is in qualname
    )

  def __discover_functions(self):
    """Auto-discover functions from module using the filter."""
    self.functions = {}
    for name, obj in inspect.getmembers(self.target_module):
      if self.function_filter(name, obj):
        self.functions[name] = obj

    # Optionally add built-in theme tuner
    if self.theme_tuner:
      self.__add_theme_tuner_function()

    # Build hierarchical command structure
    self.commands = self.__build_command_tree()

  def __discover_methods(self):
    """Auto-discover methods from class using inner class pattern or direct methods."""
    self.functions = {}

    # Check for inner classes first (hierarchical organization)
    inner_classes = self.__discover_inner_classes()

    if inner_classes:
      # Use inner class pattern for hierarchical commands
      # Validate main class and inner class constructors
      self.__validate_constructor_parameters(self.target_class, "main class")
      for class_name, inner_class in inner_classes.items():
        self.__validate_constructor_parameters(inner_class, f"inner class '{class_name}'")
      
      self.__discover_methods_from_inner_classes(inner_classes)
      self.use_inner_class_pattern = True
    else:
      # Use direct methods from the class (flat commands)
      # For direct methods, class should have parameterless constructor or all params with defaults
      self.__validate_constructor_parameters(self.target_class, "class", allow_parameterless_only=True)
      
      self.__discover_direct_methods()
      self.use_inner_class_pattern = False

    # Optionally add built-in theme tuner
    if self.theme_tuner:
      self.__add_theme_tuner_function()

    # Build hierarchical command structure
    self.commands = self.__build_command_tree()

  def __discover_inner_classes(self) -> dict[str, type]:
    """Discover inner classes that should be treated as command groups."""
    inner_classes = {}

    for name, obj in inspect.getmembers(self.target_class):
      if (inspect.isclass(obj) and
          not name.startswith('_') and
          obj.__qualname__.endswith(f'{self.target_class.__name__}.{name}')):
        inner_classes[name] = obj

    return inner_classes

  def __validate_constructor_parameters(self, cls: type, context: str, allow_parameterless_only: bool = False):
    """Validate that constructor parameters all have default values.
    
    :param cls: The class to validate
    :param context: Context string for error messages (e.g., "main class", "inner class 'UserOps'")
    :param allow_parameterless_only: If True, allows only parameterless constructors (for direct method pattern)
    """
    try:
      init_method = cls.__init__
      sig = inspect.signature(init_method)
      
      params_without_defaults = []
      
      for param_name, param in sig.parameters.items():
        # Skip self parameter
        if param_name == 'self':
          continue
        
        # Skip *args and **kwargs
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
          continue
        
        # Check if parameter has no default value
        if param.default == param.empty:
          params_without_defaults.append(param_name)
      
      if params_without_defaults:
        param_list = ', '.join(params_without_defaults)
        class_name = cls.__name__
        if allow_parameterless_only:
          # Direct method pattern requires truly parameterless constructor
          error_msg = (f"Constructor for {context} '{class_name}' has parameters without default values: {param_list}. "
                      "For classes using direct methods, the constructor must be parameterless or all parameters must have default values.")
        else:
          # Inner class pattern allows parameters but they must have defaults
          error_msg = (f"Constructor for {context} '{class_name}' has parameters without default values: {param_list}. "
                      "All constructor parameters must have default values to be used as CLI arguments.")
        raise ValueError(error_msg)
      
    except Exception as e:
      if isinstance(e, ValueError):
        raise e
      # Re-raise other exceptions as ValueError with context
      error_msg = f"Error validating constructor for {context} '{cls.__name__}': {e}"
      raise ValueError(error_msg) from e

  def __discover_methods_from_inner_classes(self, inner_classes: dict[str, type]):
    """Discover methods from inner classes for the new pattern."""
    from .str_utils import StrUtils

    # Store inner class info for later use in parsing/execution
    self.inner_classes = inner_classes
    self.use_inner_class_pattern = True

    # For each inner class, discover its methods
    for class_name, inner_class in inner_classes.items():
      command_name = StrUtils.kebab_case(class_name)

      # Get methods from the inner class
      for method_name, method_obj in inspect.getmembers(inner_class):
        if (not method_name.startswith('_') and
            callable(method_obj) and
            method_name != '__init__' and
            inspect.isfunction(method_obj)):

          # Create hierarchical name: command__subcommand
          hierarchical_name = f"{command_name}__{method_name}"
          self.functions[hierarchical_name] = method_obj

          # Store metadata for execution
          if not hasattr(self, 'inner_class_metadata'):
            self.inner_class_metadata = {}
          self.inner_class_metadata[hierarchical_name] = {
            'inner_class': inner_class,
            'inner_class_name': class_name,
            'command_name': command_name,
            'method_name': method_name
          }

  def __discover_direct_methods(self):
    """Discover methods directly from the class (flat command structure)."""
    # Get all methods from the class that match our filter
    for name, obj in inspect.getmembers(self.target_class):
      if self.method_filter(name, obj):
        # Store the unbound method - it will be bound at execution time
        self.functions[name] = obj

  def __add_theme_tuner_function(self):
    """Add built-in theme tuner function to available commands."""

    def tune_theme(base_theme: str = "universal"):
      """Interactive theme color tuning with real-time preview and RGB export.

      :param base_theme: Base theme to start with (universal or colorful, defaults to universal)
      """
      from auto_cli.theme.theme_tuner import run_theme_tuner
      run_theme_tuner(base_theme)

    # Add to functions with a hierarchical name to keep it organized
    self.functions['cli__tune-theme'] = tune_theme

  def __init_completion(self, shell: str = None):
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

  def __is_completion_request(self) -> bool:
    """Check if this is a completion request."""
    import os
    return (
        '--_complete' in sys.argv or
        os.environ.get('_AUTO_CLI_COMPLETE') is not None
    )

  def __handle_completion(self) -> None:
    """Handle completion request and exit."""
    if not self._completion_handler:
      self.__init_completion()

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
      self.__init_completion()

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

  def __show_completion_script(self, shell: str) -> int:
    """Show completion script for specified shell.

    :param shell: Target shell
    :return: Exit code (0 for success, 1 for error)
    """
    if not self.enable_completion:
      print("Completion is disabled for this CLI.", file=sys.stderr)
      return 1

    # Initialize completion handler for specific shell
    self.__init_completion(shell)

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

  def __build_command_tree(self) -> dict[str, dict]:
    """Build hierarchical command tree from discovered functions."""
    commands = {}

    for func_name, func_obj in self.functions.items():
      if '__' in func_name:
        # Parse hierarchical command: user__create or admin__user__reset
        self.__add_to_command_tree(commands, func_name, func_obj)
      else:
        # Flat command: hello, count_animals → hello, count-animals
        cli_name = func_name.replace('_', '-')
        commands[cli_name] = {
          'type': 'flat',
          'function': func_obj,
          'original_name': func_name
        }

    return commands

  def __add_to_command_tree(self, commands: dict, func_name: str, func_obj):
    """Add function to command tree, creating nested structure as needed."""
    # Split by double underscore: admin__user__reset_password → [admin, user, reset_password]
    parts = func_name.split('__')

    # Navigate/create tree structure
    current_level = commands
    path = []

    for i, part in enumerate(parts[:-1]):  # All but the last part are groups
      cli_part = part.replace('_', '-')  # Convert underscores to dashes
      path.append(cli_part)

      if cli_part not in current_level:
        group_info = {
          'type': 'group',
          'subcommands': {}
        }

        # Add inner class description if using inner class pattern
        if (hasattr(self, 'use_inner_class_pattern') and
            self.use_inner_class_pattern and
            hasattr(self, 'inner_class_metadata') and
            func_name in self.inner_class_metadata):
          metadata = self.inner_class_metadata[func_name]
          if metadata['command_name'] == cli_part:
            inner_class = metadata['inner_class']
            if inner_class.__doc__:
              from .docstring_parser import parse_docstring
              main_desc, _ = parse_docstring(inner_class.__doc__)
              group_info['description'] = main_desc

        current_level[cli_part] = group_info

      current_level = current_level[cli_part]['subcommands']

    # Add the final command
    final_command = parts[-1].replace('_', '-')
    command_info = {
      'type': 'command',
      'function': func_obj,
      'original_name': func_name,
      'command_path': path + [final_command]
    }

    # Add inner class metadata if available
    if (hasattr(self, 'inner_class_metadata') and
        func_name in self.inner_class_metadata):
      command_info['inner_class_metadata'] = self.inner_class_metadata[func_name]

    current_level[final_command] = command_info

  def __add_global_class_args(self, parser: argparse.ArgumentParser):
    """Add global arguments from main class constructor."""
    # Get the constructor signature
    init_method = self.target_class.__init__
    sig = inspect.signature(init_method)

    # Extract docstring help for constructor parameters
    _, param_help = extract_function_help(init_method)

    for param_name, param in sig.parameters.items():
      # Skip self parameter
      if param_name == 'self':
        continue

      # Skip *args and **kwargs
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue

      arg_config = {
        'dest': f'_global_{param_name}',  # Prefix to avoid conflicts
        'help': param_help.get(param_name, f"Global {param_name} parameter")
      }

      # Handle type annotations
      if param.annotation != param.empty:
        type_config = self.__get_arg_type_config(param.annotation)
        arg_config.update(type_config)

      # Handle defaults
      if param.default != param.empty:
        arg_config['default'] = param.default
      else:
        arg_config['required'] = True

      # Add argument with global- prefix to distinguish from sub-global args
      flag = f"--global-{param_name.replace('_', '-')}"
      parser.add_argument(flag, **arg_config)

  def __add_subglobal_class_args(self, parser: argparse.ArgumentParser, inner_class: type, command_name: str):
    """Add sub-global arguments from inner class constructor."""
    # Get the constructor signature
    init_method = inner_class.__init__
    sig = inspect.signature(init_method)

    # Extract docstring help for constructor parameters
    _, param_help = extract_function_help(init_method)

    for param_name, param in sig.parameters.items():
      # Skip self parameter
      if param_name == 'self':
        continue

      # Skip *args and **kwargs
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue

      arg_config = {
        'dest': f'_subglobal_{command_name}_{param_name}',  # Prefix to avoid conflicts
        'help': param_help.get(param_name, f"{command_name} {param_name} parameter")
      }

      # Handle type annotations
      if param.annotation != param.empty:
        type_config = self.__get_arg_type_config(param.annotation)
        arg_config.update(type_config)

      # Handle defaults
      if param.default != param.empty:
        arg_config['default'] = param.default
      else:
        arg_config['required'] = True

      # Add argument with command-specific prefix
      flag = f"--{param_name.replace('_', '-')}"
      parser.add_argument(flag, **arg_config)

  def __get_arg_type_config(self, annotation: type) -> dict[str, Any]:
    """Convert type annotation to argparse configuration."""
    from pathlib import Path
    from typing import get_args, get_origin

    # Handle Optional[Type] -> get the actual type
    # Handle both typing.Union and types.UnionType (Python 3.10+)
    origin = get_origin(annotation)
    if origin is Union or str(origin) == "<class 'types.UnionType'>":
      args = get_args(annotation)
      # Optional[T] is Union[T, NoneType]
      if len(args) == 2 and type(None) in args:
        annotation = next(arg for arg in args if arg is not type(None))

    if annotation in (str, int, float):
      return {'type': annotation}
    elif annotation == bool:
      return {'action': 'store_true'}
    elif annotation == Path:
      return {'type': Path}
    elif inspect.isclass(annotation) and issubclass(annotation, enum.Enum):
      return {
        'type': lambda x: annotation[x.split('.')[-1]],
        'choices': list(annotation),
        'metavar': f"{{{','.join(e.name for e in annotation)}}}"
      }
    return {}

  def __add_function_args(self, parser: argparse.ArgumentParser, fn: Callable):
    """Add function parameters as CLI arguments with help from docstring."""
    sig = inspect.signature(fn)
    _, param_help = extract_function_help(fn)

    for name, param in sig.parameters.items():
      # Skip self parameter for class methods
      if name == 'self':
        continue

      # Skip *args and **kwargs - they can't be CLI arguments
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue

      arg_config: dict[str, Any] = {
        'dest': name,
        'help': param_help.get(name, f"{name} parameter")
      }

      # Handle type annotations
      if param.annotation != param.empty:
        type_config = self.__get_arg_type_config(param.annotation)
        arg_config.update(type_config)

      # Handle defaults - determine if argument is required
      if param.default != param.empty:
        arg_config['default'] = param.default
        # Don't set required for optional args
      else:
        arg_config['required'] = True

      # Add argument with kebab-case flag name
      flag = f"--{name.replace('_', '-')}"
      parser.add_argument(flag, **arg_config)

  def create_parser(self, no_color: bool = False) -> argparse.ArgumentParser:
    """Create argument parser with hierarchical subcommand support."""
    # Create a custom formatter class that includes the theme (or no theme if no_color)
    effective_theme = None if no_color else self.theme

    def create_formatter_with_theme(*args, **kwargs):
      formatter = HierarchicalHelpFormatter(*args, theme=effective_theme, **kwargs)
      return formatter

    parser = argparse.ArgumentParser(
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
    original_format_help = parser.format_help

    def patched_format_help():
      # Get original help
      original_help = original_format_help()

      # Apply title styling if we have a theme
      if effective_theme and self.title in original_help:
        from .theme import ColorFormatter
        color_formatter = ColorFormatter()
        styled_title = color_formatter.apply_style(self.title, effective_theme.title)
        # Replace the plain title with the styled version
        original_help = original_help.replace(self.title, styled_title)

      return original_help

    parser.format_help = patched_format_help

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

    # Add global arguments from main class constructor (for inner class pattern)
    if (self.target_mode == TargetMode.CLASS and
        hasattr(self, 'use_inner_class_pattern') and
        self.use_inner_class_pattern):
      self.__add_global_class_args(parser)

    # Main subparsers
    subparsers = parser.add_subparsers(
      title='COMMANDS',
      dest='command',
      required=False,  # Allow no command to show help
      help='Available commands',
      metavar=''  # Remove the comma-separated list
    )

    # Store theme reference for consistency in subparsers
    subparsers._theme = effective_theme

    # Add commands (flat, groups, and nested groups)
    self.__add_commands_to_parser(subparsers, self.commands, [])

    # Now that the parser is fully configured, patch the formatter to have access to actions
    patch_formatter_with_parser_actions()

    return parser

  def __add_commands_to_parser(self, subparsers, commands: dict, path: list):
    """Recursively add commands to parser, supporting arbitrary nesting."""
    for name, info in commands.items():
      if info['type'] == 'flat':
        self.__add_flat_command(subparsers, name, info)
      elif info['type'] == 'group':
        self.__add_command_group(subparsers, name, info, path + [name])
      elif info['type'] == 'command':
        self.__add_leaf_command(subparsers, name, info)

  def __add_flat_command(self, subparsers, name: str, info: dict):
    """Add a flat command to subparsers."""
    func = info['function']
    desc, _ = extract_function_help(func)

    # Get the formatter class from the parent parser to ensure consistency
    effective_theme = getattr(subparsers, '_theme', self.theme)

    def create_formatter_with_theme(*args, **kwargs):
      return HierarchicalHelpFormatter(*args, theme=effective_theme, **kwargs)

    sub = subparsers.add_parser(
      name,
      help=desc,
      description=desc,
      formatter_class=create_formatter_with_theme
    )
    sub._command_type = 'flat'

    # Store theme reference for consistency
    sub._theme = effective_theme

    self.__add_function_args(sub, func)
    sub.set_defaults(_cli_function=func, _function_name=info['original_name'])

  def __add_command_group(self, subparsers, name: str, info: dict, path: list):
    """Add a command group with subcommands (supports nesting)."""
    # Check for inner class description
    group_help = None
    inner_class = None

    if 'description' in info:
      group_help = info['description']
    else:
      group_help = f"{name.title().replace('-', ' ')} operations"

    # Find the inner class for this command group (for sub-global arguments)
    if (hasattr(self, 'use_inner_class_pattern') and
        self.use_inner_class_pattern and
        hasattr(self, 'inner_classes')):
      for class_name, cls in self.inner_classes.items():
        from .str_utils import StrUtils
        if StrUtils.kebab_case(class_name) == name:
          inner_class = cls
          break

    # Get the formatter class from the parent parser to ensure consistency
    effective_theme = getattr(subparsers, '_theme', self.theme)

    def create_formatter_with_theme(*args, **kwargs):
      return HierarchicalHelpFormatter(*args, theme=effective_theme, **kwargs)

    group_parser = subparsers.add_parser(
      name,
      help=group_help,
      formatter_class=create_formatter_with_theme
    )

    # Add sub-global arguments from inner class constructor
    if inner_class:
      self.__add_subglobal_class_args(group_parser, inner_class, name)

    # Store description for formatter to use
    if 'description' in info:
      group_parser._command_group_description = info['description']
    group_parser._command_type = 'group'

    # Store theme reference for consistency
    group_parser._theme = effective_theme

    # Store subcommand info for help formatting
    subcommand_help = {}
    for subcmd_name, subcmd_info in info['subcommands'].items():
      if subcmd_info['type'] == 'command':
        func = subcmd_info['function']
        desc, _ = extract_function_help(func)
        subcommand_help[subcmd_name] = desc
      elif subcmd_info['type'] == 'group':
        # For nested groups, show as group with subcommands
        subcommand_help[subcmd_name] = f"{subcmd_name.title().replace('-', ' ')} operations"

    group_parser._subcommands = subcommand_help
    group_parser._subcommand_details = info['subcommands']

    # Create subcommand parsers with enhanced help
    dest_name = '_'.join(path) + '_subcommand' if len(path) > 1 else 'subcommand'
    sub_subparsers = group_parser.add_subparsers(
      title=f'{name.title().replace("-", " ")} COMMANDS',
      dest=dest_name,
      required=False,
      help=f'Available {name} commands',
      metavar=''
    )

    # Store reference for enhanced help formatting
    sub_subparsers._enhanced_help = True
    sub_subparsers._subcommand_details = info['subcommands']

    # Store theme reference for consistency in nested subparsers
    sub_subparsers._theme = effective_theme

    # Recursively add subcommands
    self.__add_commands_to_parser(sub_subparsers, info['subcommands'], path)

  def __add_leaf_command(self, subparsers, name: str, info: dict):
    """Add a leaf command (actual executable function)."""
    func = info['function']
    desc, _ = extract_function_help(func)

    # Get the formatter class from the parent parser to ensure consistency
    effective_theme = getattr(subparsers, '_theme', self.theme)

    def create_formatter_with_theme(*args, **kwargs):
      return HierarchicalHelpFormatter(*args, theme=effective_theme, **kwargs)

    sub = subparsers.add_parser(
      name,
      help=desc,
      description=desc,
      formatter_class=create_formatter_with_theme
    )
    sub._command_type = 'command'

    # Store theme reference for consistency
    sub._theme = effective_theme

    self.__add_function_args(sub, func)
    sub.set_defaults(
      _cli_function=func,
      _function_name=info['original_name'],
      _command_path=info['command_path']
    )


  def __handle_missing_command(self, parser: argparse.ArgumentParser, parsed) -> int:
    """Handle cases where no command or subcommand was provided."""
    # Analyze parsed arguments to determine what level of help to show
    command_parts = []
    result = 0

    # Check for command and nested subcommands
    if hasattr(parsed, 'command') and parsed.command:
      command_parts.append(parsed.command)

      # Check for nested subcommands
      for attr_name in dir(parsed):
        if attr_name.endswith('_subcommand') and getattr(parsed, attr_name):
          # Extract command path from attribute names
          if attr_name == 'subcommand':
            # Simple case: user subcommand
            subcommand = getattr(parsed, attr_name)
            if subcommand:
              command_parts.append(subcommand)
          else:
            # Complex case: user_subcommand for nested groups
            path_parts = attr_name.replace('_subcommand', '').split('_')
            command_parts.extend(path_parts)
            subcommand = getattr(parsed, attr_name)
            if subcommand:
              command_parts.append(subcommand)

    if command_parts:
      # Show contextual help for partial command
      result = self.__show_contextual_help(parser, command_parts)
    else:
      # No command provided - show main help
      parser.print_help()
      result = 0

    return result

  def __show_contextual_help(self, parser: argparse.ArgumentParser, command_parts: list) -> int:
    """Show help for a specific command level."""
    # Navigate to the appropriate subparser
    current_parser = parser
    result = 0

    for part in command_parts:
      # Find the subparser for this command part
      found_parser = None
      for action in current_parser._actions:
        if isinstance(action, argparse._SubParsersAction):
          if part in action.choices:
            found_parser = action.choices[part]
            break

      if found_parser:
        current_parser = found_parser
      else:
        print(f"Unknown command: {' '.join(command_parts[:command_parts.index(part) + 1])}", file=sys.stderr)
        parser.print_help()
        result = 1
        break

    if result == 0:
      current_parser.print_help()

    return result

  def __execute_command(self, parsed) -> Any:
    """Execute the parsed command with its arguments."""
    if self.target_mode == TargetMode.MODULE:
      # Existing function execution logic
      fn = parsed._cli_function
      sig = inspect.signature(fn)

      # Build kwargs from parsed arguments
      kwargs = {}
      for param_name in sig.parameters:
        # Skip *args and **kwargs - they can't be CLI arguments
        param = sig.parameters[param_name]
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
          continue

        # Convert kebab-case back to snake_case for function call
        attr_name = param_name.replace('-', '_')
        if hasattr(parsed, attr_name):
          value = getattr(parsed, attr_name)
          kwargs[param_name] = value

      # Execute function and return result
      return fn(**kwargs)

    elif self.target_mode == TargetMode.CLASS:
      # Support both inner class pattern and direct methods
      if (hasattr(self, 'use_inner_class_pattern') and
          self.use_inner_class_pattern and
          hasattr(parsed, '_cli_function') and
          hasattr(self, 'inner_class_metadata')):
        return self.__execute_inner_class_command(parsed)
      else:
        # Execute direct method from class
        return self.__execute_direct_method_command(parsed)

    else:
      raise RuntimeError(f"Unknown target mode: {self.target_mode}")

  def __execute_inner_class_command(self, parsed) -> Any:
    """Execute command using inner class pattern."""
    method = parsed._cli_function
    original_name = parsed._function_name

    # Get metadata for this command
    if original_name not in self.inner_class_metadata:
      raise RuntimeError(f"No metadata found for command: {original_name}")

    metadata = self.inner_class_metadata[original_name]
    inner_class = metadata['inner_class']
    command_name = metadata['command_name']

    # 1. Create main class instance with global arguments
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
      main_instance = self.target_class(**main_kwargs)
    except TypeError as e:
      raise RuntimeError(f"Cannot instantiate {self.target_class.__name__} with global args: {e}") from e

    # 2. Create inner class instance with sub-global arguments
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
      inner_instance = inner_class(**inner_kwargs)
    except TypeError as e:
      raise RuntimeError(f"Cannot instantiate {inner_class.__name__} with sub-global args: {e}") from e

    # 3. Get method from inner instance and execute with command arguments
    bound_method = getattr(inner_instance, metadata['method_name'])
    method_sig = inspect.signature(bound_method)
    method_kwargs = {}

    for param_name, param in method_sig.parameters.items():
      if param_name == 'self':
        continue
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue

      # Look for method argument (no prefix, just the parameter name)
      attr_name = param_name.replace('-', '_')
      if hasattr(parsed, attr_name):
        value = getattr(parsed, attr_name)
        method_kwargs[param_name] = value

    return bound_method(**method_kwargs)

  def __execute_direct_method_command(self, parsed) -> Any:
    """Execute command using direct method from class."""
    method = parsed._cli_function

    # Create class instance (requires parameterless constructor or all defaults)
    try:
      class_instance = self.target_class()
    except TypeError as e:
      raise RuntimeError(f"Cannot instantiate {self.target_class.__name__}: constructor parameters must have default values") from e

    # Get bound method
    bound_method = getattr(class_instance, method.__name__)

    # Execute with argument logic
    sig = inspect.signature(bound_method)
    kwargs = {}
    for param_name in sig.parameters:
      # Skip self parameter
      if param_name == 'self':
        continue

      # Skip *args and **kwargs - they can't be CLI arguments
      param = sig.parameters[param_name]
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue

      # Convert kebab-case back to snake_case for method call
      attr_name = param_name.replace('-', '_')
      if hasattr(parsed, attr_name):
        value = getattr(parsed, attr_name)
        kwargs[param_name] = value

    return bound_method(**kwargs)

  def __handle_execution_error(self, parsed, error: Exception) -> int:
    """Handle execution errors gracefully."""
    function_name = getattr(parsed, '_function_name', 'unknown')
    print(f"Error executing {function_name}: {error}", file=sys.stderr)

    if getattr(parsed, 'verbose', False):
      traceback.print_exc()

    return 1
