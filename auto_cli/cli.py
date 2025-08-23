# Auto-generate CLI from function signatures and docstrings.
import argparse
import enum
import inspect
import sys
import traceback
import types
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
               method_filter: Optional[Callable] = None, theme=None,
               enable_completion: bool = True, enable_theme_tuner: bool = False, alphabetize: bool = True):
    """Initialize CLI generator with auto-detection of target type.

    :param target: Module or class containing functions/methods to generate CLI from
    :param title: CLI application title (auto-generated from class docstring if None for classes)
    :param function_filter: Optional filter function for selecting functions (module mode)
    :param method_filter: Optional filter function for selecting methods (class mode)
    :param theme: Optional theme for colored output
    :param enable_completion: If True, enables shell completion support
    :param enable_theme_tuner: If True, enables theme tuning support
    :param alphabetize: If True, sort commands and options alphabetically (System commands always appear first)
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
    self.enable_theme_tuner = enable_theme_tuner
    self.enable_completion = enable_completion
    self.alphabetize = alphabetize
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
    if self.enable_completion and self._is_completion_request():
      self._handle_completion()

    # First, do a preliminary parse to check for --no-color flag
    # This allows us to disable colors before any help output is generated
    no_color = False
    if args:
      no_color = '--no-color' in args or '-n' in args

    parser = self.create_parser(no_color=no_color)
    parsed = None

    try:
      parsed = parser.parse_args(args)

      # Handle missing command/command group scenarios
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

    # Build hierarchical command structure
    self.commands = self.__build_command_tree()

  def __discover_methods(self):
    """Auto-discover methods from class using inner class pattern or direct methods."""
    self.functions = {}

    # Check for inner classes first (hierarchical organization)
    inner_classes = self.__discover_inner_classes()

    if inner_classes:
      # Use mixed pattern: both direct methods AND inner class methods
      # Validate main class and inner class constructors
      self.__validate_constructor_parameters(self.target_class, "main class")
      for class_name, inner_class in inner_classes.items():
        self.__validate_constructor_parameters(inner_class, f"inner class '{class_name}'")

      # Discover both direct methods and inner class methods
      self.__discover_direct_methods()  # Direct methods on main class
      self.__discover_methods_from_inner_classes(inner_classes)  # Inner class methods
      self.use_inner_class_pattern = True
    else:
      # Use direct methods from the class (flat commands only)
      # For direct methods, class should have parameterless constructor or all params with defaults
      self.__validate_constructor_parameters(self.target_class, "class", allow_parameterless_only=True)

      self.__discover_direct_methods()
      self.use_inner_class_pattern = False

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

          # Create hierarchical name: command__command
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
    from .system import System
    completion = System.Completion(cli_instance=self)
    return completion.is_completion_request()

  def _handle_completion(self) -> None:
    """Handle completion request and exit."""
    from .system import System
    completion = System.Completion(cli_instance=self)
    completion.handle_completion()

  def install_completion(self, shell: str = None, force: bool = False) -> bool:
    """Install shell completion for this CLI.

    :param shell: Target shell (auto-detect if None)
    :param force: Force overwrite existing completion
    :return: True if installation successful
    """
    from .system import System
    completion = System.Completion(cli_instance=self)
    return completion.install(shell, force)

  def _show_completion_script(self, shell: str) -> int:
    """Show completion script for specified shell.

    :param shell: Target shell
    :return: Exit code (0 for success, 1 for error)
    """
    from .system import System
    completion = System.Completion(cli_instance=self)
    try:
      completion.show(shell)
      return 0
    except Exception:
      return 1

  def __build_system_commands(self) -> dict[str, dict]:
    """Build System commands when theme tuner or completion is enabled.
    
    Uses the same hierarchical command building logic as regular classes.
    """
    from .system import System
    
    system_commands = {}
    
    # Only inject commands if they're enabled
    if not self.enable_theme_tuner and not self.enable_completion:
      return system_commands
    
    # Discover System inner classes and their methods
    system_inner_classes = {}
    system_functions = {}
    
    # Check TuneTheme if theme tuner is enabled
    if self.enable_theme_tuner and hasattr(System, 'TuneTheme'):
      tune_theme_class = System.TuneTheme
      system_inner_classes['TuneTheme'] = tune_theme_class
      
      # Get methods from TuneTheme class
      for attr_name in dir(tune_theme_class):
        if not attr_name.startswith('_') and callable(getattr(tune_theme_class, attr_name)):
          attr = getattr(tune_theme_class, attr_name)
          if callable(attr) and hasattr(attr, '__self__') is False:  # Unbound method
            method_name = f"TuneTheme__{attr_name}"
            system_functions[method_name] = attr
    
    # Check Completion if completion is enabled
    if self.enable_completion and hasattr(System, 'Completion'):
      completion_class = System.Completion
      system_inner_classes['Completion'] = completion_class
      
      # Get methods from Completion class
      for attr_name in dir(completion_class):
        if not attr_name.startswith('_') and callable(getattr(completion_class, attr_name)):
          attr = getattr(completion_class, attr_name)
          if callable(attr) and hasattr(attr, '__self__') is False:  # Unbound method
            method_name = f"Completion__{attr_name}"
            system_functions[method_name] = attr
    
    # Build hierarchical structure using the same logic as regular classes
    if system_functions:
      groups = {}
      for func_name, func_obj in system_functions.items():
        if '__' in func_name:  # Inner class method with double underscore
          # Parse: class_name__method_name -> (class_name, method_name)
          parts = func_name.split('__', 1)
          if len(parts) == 2:
            group_name, method_name = parts
            # Convert class names to kebab-case 
            from .str_utils import StrUtils
            cli_group_name = StrUtils.kebab_case(group_name)
            cli_method_name = method_name.replace('_', '-')
            
            if cli_group_name not in groups:
              # Get inner class description
              description = None
              original_class_name = group_name
              if original_class_name in system_inner_classes:
                inner_class = system_inner_classes[original_class_name]
                if inner_class.__doc__:
                  from .docstring_parser import parse_docstring
                  description, _ = parse_docstring(inner_class.__doc__)
              
              groups[cli_group_name] = {
                'type': 'group',
                'commands': {},
                'description': description or f"{cli_group_name.title().replace('-', ' ')} operations",
                'inner_class': system_inner_classes.get(original_class_name),  # Store class reference
                'is_system_command': True  # Mark as system command
              }
            
            # Add method as command in the group
            groups[cli_group_name]['commands'][cli_method_name] = {
              'type': 'command',
              'function': func_obj,
              'original_name': func_name,
              'command_path': [cli_group_name, cli_method_name],
              'is_system_command': True  # Mark as system command
            }
      
      # Add groups to system commands
      system_commands.update(groups)
    
    return system_commands

  def __build_command_tree(self) -> dict[str, dict]:
    """Build command tree from discovered functions.

    For module-based CLIs: Creates flat structure with all commands at top level.
    For class-based CLIs: Creates hierarchical structure with command groups and commands.
    """
    commands = {}

    # First, inject System commands if enabled (they appear first in help)
    system_commands = self.__build_system_commands()
    if system_commands:
      # Group all system commands under a "system" parent group
      commands['system'] = {
        'type': 'group',
        'commands': system_commands,
        'description': 'System utilities and configuration',
        'is_system_command': True
      }

    if self.target_mode == TargetMode.MODULE:
      # Module mode: Always flat structure
      for func_name, func_obj in self.functions.items():
        cli_name = func_name.replace('_', '-')
        commands[cli_name] = {
          'type': 'command',
          'function': func_obj,
          'original_name': func_name
        }

    elif self.target_mode == TargetMode.CLASS:
      if hasattr(self, 'use_inner_class_pattern') and self.use_inner_class_pattern:
        # Class mode with inner classes: Hierarchical structure

        # Add direct methods as top-level commands
        for func_name, func_obj in self.functions.items():
          if '__' not in func_name:  # Direct method on main class
            cli_name = func_name.replace('_', '-')
            commands[cli_name] = {
              'type': 'command',
              'function': func_obj,
              'original_name': func_name
            }

        # Group inner class methods by command group
        groups = {}
        for func_name, func_obj in self.functions.items():
          if '__' in func_name:  # Inner class method with double underscore
            # Parse: class_name__method_name -> (class_name, method_name)
            parts = func_name.split('__', 1)
            if len(parts) == 2:
              group_name, method_name = parts
              cli_group_name = group_name.replace('_', '-')
              cli_method_name = method_name.replace('_', '-')

              if cli_group_name not in groups:
                # Get inner class description
                description = None
                if hasattr(self, 'inner_classes'):
                  for class_name, inner_class in self.inner_classes.items():
                    from .str_utils import StrUtils
                    if StrUtils.kebab_case(class_name) == cli_group_name:
                      if inner_class.__doc__:
                        from .docstring_parser import parse_docstring
                        description, _ = parse_docstring(inner_class.__doc__)
                      break

                groups[cli_group_name] = {
                  'type': 'group',
                  'commands': {},
                  'description': description or f"{cli_group_name.title().replace('-', ' ')} operations"
                }

              # Add method as command in the group
              groups[cli_group_name]['commands'][cli_method_name] = {
                'type': 'command',
                'function': func_obj,
                'original_name': func_name,
                'command_path': [cli_group_name, cli_method_name]
              }

        # Add groups to commands
        commands.update(groups)

      else:
        # Class mode without inner classes: Flat structure
        for func_name, func_obj in self.functions.items():
          cli_name = func_name.replace('_', '-')
          commands[cli_name] = {
            'type': 'command',
            'function': func_obj,
            'original_name': func_name
          }

    return commands

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

      # Add argument without prefix (user requested no global- prefix)
      flag = f"--{param_name.replace('_', '-')}"

      # Check for conflicts with built-in CLI options
      built_in_options = {'verbose', 'no-color', 'help'}
      if param_name.replace('_', '-') in built_in_options:
        # Skip built-in options to avoid conflicts
        continue

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
      
      # Set clean metavar if not already set by type config (e.g., enums set their own metavar)
      if 'metavar' not in arg_config and 'action' not in arg_config:
        arg_config['metavar'] = param_name.upper()

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
    """Create argument parser with hierarchical command group support."""
    # Create a custom formatter class that includes the theme (or no theme if no_color)
    effective_theme = None if no_color else self.theme

    def create_formatter_with_theme(*args, **kwargs):
      formatter = HierarchicalHelpFormatter(*args, theme=effective_theme, alphabetize=self.alphabetize, **kwargs)
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
      if info['type'] == 'group':
        self.__add_command_group(subparsers, name, info, path + [name])
      elif info['type'] == 'command':
        self.__add_leaf_command(subparsers, name, info)

  def __add_command_group(self, subparsers, name: str, info: dict, path: list):
    """Add a command group with commands (supports nesting)."""
    # Check for inner class description
    group_help = None
    inner_class = None

    if 'description' in info:
      group_help = info['description']
    else:
      group_help = f"{name.title().replace('-', ' ')} operations"

    # Find the inner class for this command group (for sub-global arguments)
    # First check if it's provided directly in the info (for system commands)
    if 'inner_class' in info and info['inner_class']:
      inner_class = info['inner_class']
    elif (hasattr(self, 'use_inner_class_pattern') and
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
      return HierarchicalHelpFormatter(*args, theme=effective_theme, alphabetize=self.alphabetize, **kwargs)

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
    
    # Mark as System command if applicable
    if 'is_system_command' in info:
      group_parser._is_system_command = info['is_system_command']

    # Store theme reference for consistency
    group_parser._theme = effective_theme

    # Store command info for help formatting
    command_help = {}
    for cmd_name, cmd_info in info['commands'].items():
      if cmd_info['type'] == 'command':
        func = cmd_info['function']
        desc, _ = extract_function_help(func)
        command_help[cmd_name] = desc
      elif cmd_info['type'] == 'group':
        # For nested groups, use their actual description if available
        if 'description' in cmd_info and cmd_info['description']:
          command_help[cmd_name] = cmd_info['description']
        else:
          command_help[cmd_name] = f"{cmd_name.title().replace('-', ' ')} operations"

    group_parser._commands = command_help
    group_parser._command_details = info['commands']

    # Create command parsers with enhanced help
    dest_name = '_'.join(path) + '_command' if len(path) > 1 else 'command'
    sub_subparsers = group_parser.add_subparsers(
      title=f'{name.title().replace("-", " ")} COMMANDS',
      dest=dest_name,
      required=False,
      help=f'Available {name} commands',
      metavar=''
    )

    # Store reference for enhanced help formatting
    sub_subparsers._enhanced_help = True
    sub_subparsers._command_details = info['commands']

    # Store theme reference for consistency in nested subparsers
    sub_subparsers._theme = effective_theme

    # Recursively add commands
    self.__add_commands_to_parser(sub_subparsers, info['commands'], path)

  def __add_leaf_command(self, subparsers, name: str, info: dict):
    """Add a leaf command (actual executable function)."""
    func = info['function']
    desc, _ = extract_function_help(func)

    # Get the formatter class from the parent parser to ensure consistency
    effective_theme = getattr(subparsers, '_theme', self.theme)

    def create_formatter_with_theme(*args, **kwargs):
      return HierarchicalHelpFormatter(*args, theme=effective_theme, alphabetize=self.alphabetize, **kwargs)

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

    # Set defaults - command_path is optional for direct methods
    defaults = {
      '_cli_function': func,
      '_function_name': info['original_name']
    }

    if 'command_path' in info:
      defaults['_command_path'] = info['command_path']

    if 'is_system_command' in info:
      defaults['_is_system_command'] = info['is_system_command']

    sub.set_defaults(**defaults)

  def __handle_missing_command(self, parser: argparse.ArgumentParser, parsed) -> int:
    """Handle cases where no command or command group was provided."""
    # Analyze parsed arguments to determine what level of help to show
    command_parts = []
    result = 0

    # Check for command and nested command groups
    if hasattr(parsed, 'command') and parsed.command:
      # Check if this is a system command by looking for system_*_command attributes
      is_system_command = False
      for attr_name in dir(parsed):
        if attr_name.startswith('system_') and attr_name.endswith('_command'):
          is_system_command = True
          # This is a system command path: system -> [command] -> [subcommand]
          command_parts.append('system')
          command_parts.append(parsed.command)
          
          # Check if there's a specific subcommand
          subcommand = getattr(parsed, attr_name)
          if subcommand:
            command_parts.append(subcommand)
          break
      
      if not is_system_command:
        # Regular command path
        command_parts.append(parsed.command)

        # Check for nested command groups
        for attr_name in dir(parsed):
          if attr_name.endswith('_command') and getattr(parsed, attr_name):
            # Extract command path from attribute names
            if attr_name == 'command':
              # Simple case: user command
              command = getattr(parsed, attr_name)
              if command:
                command_parts.append(command)
            else:
              # Complex case: user_command for nested groups
              path_parts = attr_name.replace('_command', '').split('_')
              command_parts.extend(path_parts)
              command = getattr(parsed, attr_name)
              if command:
                command_parts.append(command)

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
      # Check for special case: system tune-theme should default to run-interactive
      if (len(command_parts) == 2 and 
          command_parts[0] == 'system' and 
          command_parts[1] == 'tune-theme'):
        # Execute tune-theme run-interactive by default
        return self.__execute_default_tune_theme()
      
      current_parser.print_help()

    return result

  def __execute_default_tune_theme(self) -> int:
    """Execute the default tune-theme command (run-interactive)."""
    from .system import System
    
    # Create System instance
    system_instance = System()
    
    # Create TuneTheme instance with default arguments
    tune_theme_instance = System.TuneTheme()
    
    # Execute run_interactive method
    tune_theme_instance.run_interactive()
    
    return 0

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
      # Determine if this is a System command, inner class method, or direct method
      original_name = getattr(parsed, '_function_name', '')
      is_system_command = getattr(parsed, '_is_system_command', False)

      if is_system_command:
        # Execute System command
        return self.__execute_system_command(parsed)
      elif (hasattr(self, 'use_inner_class_pattern') and
          self.use_inner_class_pattern and
          hasattr(self, 'inner_class_metadata') and
          original_name in self.inner_class_metadata):
        # Check if this is an inner class method (contains double underscore)
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

  def __execute_system_command(self, parsed) -> Any:
    """Execute System command using the same pattern as inner class commands."""
    from .system import System
    
    method = parsed._cli_function
    original_name = parsed._function_name
    
    # Parse the System command name: TuneTheme__method_name or Completion__method_name
    if '__' not in original_name:
      raise RuntimeError(f"Invalid System command format: {original_name}")
    
    class_name, method_name = original_name.split('__', 1)
    
    # Get the System inner class
    if class_name == 'TuneTheme':
      inner_class = System.TuneTheme
    elif class_name == 'Completion':
      inner_class = System.Completion
    else:
      raise RuntimeError(f"Unknown System command class: {class_name}")
    
    # 1. Create main System instance (no global args needed for System)
    system_instance = System()
    
    # 2. Create inner class instance with sub-global arguments if any exist
    inner_kwargs = {}
    inner_sig = inspect.signature(inner_class.__init__)
    
    for param_name, param in inner_sig.parameters.items():
      if param_name == 'self':
        continue
      if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
        continue
      
      # Look for sub-global argument (using kebab-case naming convention)
      from .str_utils import StrUtils
      command_name = StrUtils.kebab_case(class_name)
      subglobal_attr = f'_subglobal_{command_name}_{param_name}'
      if hasattr(parsed, subglobal_attr):
        value = getattr(parsed, subglobal_attr)
        inner_kwargs[param_name] = value
    
    try:
      inner_instance = inner_class(**inner_kwargs)
    except TypeError as e:
      raise RuntimeError(f"Cannot instantiate System.{class_name} with args: {e}") from e
    
    # 3. Get method from inner instance and execute with command arguments
    bound_method = getattr(inner_instance, method_name)
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
      raise RuntimeError(
        f"Cannot instantiate {self.target_class.__name__}: constructor parameters must have default values") from e

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
