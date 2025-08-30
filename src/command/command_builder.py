"""Command tree building service for CLI applications.

Consolidates all command structure generation logic for both module-based and class-based CLIs.
Handles flat commands and hierarchical command organization through inner class patterns.
"""

from typing import Dict, Any, Type, Optional


class CommandBuilder:
  """Centralized service for building command structures from discovered functions/methods."""

  def __init__(self, target_mode: Any, functions: Dict[str, Any],
               inner_classes: Optional[Dict[str, Type]] = None,
               use_inner_class_pattern: bool = False):
    """Flat command building requires function discovery and organizational metadata."""
    self.target_mode = target_mode
    self.functions = functions
    self.inner_classes = inner_classes or {}
    self.use_inner_class_pattern = use_inner_class_pattern

  def build_command_tree(self) -> Dict[str, Dict]:
    """Build flat command structure from discovered functions based on target mode."""
    from ..enums.target_mode import TargetMode

    if self.target_mode == TargetMode.MODULE:
      return self._build_module_commands()
    elif self.target_mode == TargetMode.CLASS:
      if self.use_inner_class_pattern:
        return self._build_hierarchical_class_commands()
      else:
        return self._build_flat_class_commands()
    elif self.target_mode == TargetMode.MULTI_CLASS:
      # Multi-class mode uses same structure as class mode since functions are already discovered
      if self.use_inner_class_pattern:
        return self._build_hierarchical_class_commands()
      else:
        return self._build_flat_class_commands()
    else:
      raise ValueError(f"Unknown target mode: {self.target_mode}")

  def _build_module_commands(self) -> Dict[str, Dict]:
    """Module mode creates flat command structure."""
    commands = {}
    for func_name, func_obj in self.functions.items():
      cli_name = func_name.replace('_', '-')
      commands[cli_name] = {
        'type': 'command',
        'function': func_obj,
        'original_name': func_name
      }
    return commands

  def _build_flat_class_commands(self) -> Dict[str, Dict]:
    """Class mode without inner classes creates flat command structure."""
    from ..utils.string_utils import StringUtils
    commands = {}
    for func_name, func_obj in self.functions.items():
      cli_name = StringUtils.kebab_case(func_name)
      commands[cli_name] = {
        'type': 'command',
        'function': func_obj,
        'original_name': func_name
      }
    return commands

  def _build_hierarchical_class_commands(self) -> Dict[str, Dict]:
    """Class mode with inner classes creates hierarchical command structure."""
    from ..utils.string_utils import StringUtils
    commands = {}
    processed_groups = set()

    # Process functions in order to preserve class ordering
    for func_name, func_obj in self.functions.items():
      if '__' not in func_name:  # Direct method on main class
        cli_name = StringUtils.kebab_case(func_name)
        commands[cli_name] = {
          'type': 'command',
          'function': func_obj,
          'original_name': func_name
        }
      else:  # Inner class method - create groups as we encounter them
        parts = func_name.split('__', 1)
        if len(parts) == 2:
          group_name, method_name = parts
          cli_group_name = StringUtils.kebab_case(group_name)

          # Create group if not already processed
          if cli_group_name not in processed_groups:
            group_commands = self._build_single_command_group(cli_group_name)
            if group_commands:
              commands[cli_group_name] = group_commands
              processed_groups.add(cli_group_name)

    return commands

  def _build_command_groups(self) -> Dict[str, Dict]:
    """Build command groups from inner class methods."""
    from ..utils.string_utils import StringUtils

    groups = {}
    for func_name, func_obj in self.functions.items():
      if '__' in func_name:  # Inner class method with double underscore
        # Parse: class_name__method_name -> (class_name, method_name)
        parts = func_name.split('__', 1)
        if len(parts) == 2:
          group_name, method_name = parts
          cli_group_name = StringUtils.kebab_case(group_name)
          cli_method_name = StringUtils.kebab_case(method_name)

          if cli_group_name not in groups:
            # Get inner class description
            description = self._get_group_description(cli_group_name)

            groups[cli_group_name] = {
              'type': 'group',
              'commands': {},
              'description': description
            }

          # Add method as command in the group
          groups[cli_group_name]['commands'][cli_method_name] = {
            'type': 'command',
            'function': func_obj,
            'original_name': func_name,
            'command_path': [cli_group_name, cli_method_name]
          }

    return groups

  def _build_single_command_group(self, cli_group_name: str) -> Dict[str, Any]:
    """Build a single command group from inner class methods."""
    from ..utils.string_utils import StringUtils

    group_commands = {}

    # Find all methods for this group
    for func_name, func_obj in self.functions.items():
      if '__' in func_name:
        parts = func_name.split('__', 1)
        if len(parts) == 2:
          group_name, method_name = parts
          if StringUtils.kebab_case(group_name) == cli_group_name:
            cli_method_name = StringUtils.kebab_case(method_name)
            group_commands[cli_method_name] = {
              'type': 'command',
              'function': func_obj,
              'original_name': func_name,
              'command_path': [cli_group_name, cli_method_name]
            }

    if not group_commands:
      return None

    # Get group description
    description = self._get_group_description(cli_group_name)

    return {
      'type': 'group',
      'commands': group_commands,
      'description': description
    }

  def _get_group_description(self, cli_group_name: str) -> str:
    """Get description for command group from inner class docstring."""
    from ..utils.string_utils import StringUtils
    from .docstring_parser import parse_docstring

    description = None
    for class_name, inner_class in self.inner_classes.items():
      if StringUtils.kebab_case(class_name) == cli_group_name:
        if inner_class.__doc__:
          description, _ = parse_docstring(inner_class.__doc__)
        break

    return description or f"{cli_group_name.title().replace('-', ' ')} operations"

  @staticmethod
  def create_command_info(func_obj: Any, original_name: str, command_path: Optional[list] = None,
                          is_system_command: bool = False) -> Dict[str, Any]:
    """Create standardized command information dictionary."""
    info = {
      'type': 'command',
      'function': func_obj,
      'original_name': original_name
    }

    if command_path:
      info['command_path'] = command_path

    if is_system_command:
      info['is_system_command'] = is_system_command

    return info

  @staticmethod
  def create_group_info(description: str, commands: Dict[str, Any],
                        inner_class: Optional[Type] = None,
                        is_system_command: bool = False) -> Dict[str, Any]:
    """Create standardized group information dictionary."""
    info = {
      'type': 'group',
      'description': description,
      'commands': commands
    }

    if inner_class:
      info['inner_class'] = inner_class

    if is_system_command:
      info['is_system_command'] = is_system_command

    return info
