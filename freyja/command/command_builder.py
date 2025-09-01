"""Command tree building service for FreyjaCLI applications.

Consolidates all command structure generation logic for both module-based and class-based CLIs.
Builds proper nested dictionary structures for hierarchical commands.
"""

from typing import Dict, Any, Type, Optional, List
from .command_discovery import CommandInfo
from freyja.parser import DocStringParser

CommandTree = dict[str, dict]
class CommandBuilder:
  """Centralized service for building command structures from discovered commands."""

  def __init__(self, target_mode: Any, commands: List[CommandInfo]):
    """Build command tree from discovered CommandInfo objects."""
    self.target_mode = target_mode
    self.commands = commands

  def build_command_tree(self) -> CommandTree:
    """Build command structure from discovered commands."""
    commands:CommandTree = {}
    
    # Group commands by type and group_name
    flat_commands = []
    grouped_commands = {}
    
    for command in self.commands:
      if command.is_hierarchical and command.group_name:
        # Group hierarchical commands
        if command.group_name not in grouped_commands:
          grouped_commands[command.group_name] = []
        grouped_commands[command.group_name].append(command)
      else:
        # Collect flat commands
        flat_commands.append(command)
    
    # Add flat commands
    for command in flat_commands:
      commands[command.name] = {
        'type': 'command',
        'function': command.function,
        'original_name': command.original_name
      }
    
    # Add hierarchical commands as groups
    for group_name, group_commands in grouped_commands.items():
      # Get group description from first command's inner class
      description = self._get_group_description(group_commands[0])
      
      commands[group_name] = {
        'type': 'group',
        'description': description,
        'inner_class': group_commands[0].inner_class,
        'commands': {}
      }
      
      # Add commands to the group
      for command in group_commands:
        commands[group_name]['commands'][command.name] = {
          'type': 'command',
          'function': command.function,
          'original_name': command.original_name,
          'group_name': group_name,
          'method_name': command.method_name
        }
    
    return commands

  @staticmethod
  def _get_group_description(command: CommandInfo) -> str:
    """Get description for command group from inner class docstring."""
    if command.inner_class and command.inner_class.__doc__:
      description, _ = DocStringParser.parse_docstring(command.inner_class.__doc__)
      return description
    
    # Fallback to generating description from group name
    if command.group_name:
      return f"{command.group_name.title().replace('-', ' ')} operations"
    
    return "Command operations"

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
