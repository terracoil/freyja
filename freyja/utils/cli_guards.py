"""Freyja-specific guard validators for CLI validation.

These guards are specific to Freyja's CLI functionality and are registered
as custom guards using modgud's guard registration system.
"""

import re
from typing import Any, Callable, Union

from freyja.utils.guards import register_guard
from freyja.utils.modgud.modgud.guarded_expression.common_guards import CommonGuards
from freyja.utils.modgud.modgud.guarded_expression.types import GuardFunction


class CLIGuards:
  """Freyja-specific guard validators for CLI operations."""

  @staticmethod
  def valid_command_name(param_name: str = 'command', position: int = 0) -> GuardFunction:
    """Guard ensuring parameter is a valid CLI command name.

    Valid command names:
    - Start with a letter
    - Contain only letters, numbers, hyphens, and underscores
    - Are between 1 and 50 characters

    Args:
        param_name: Name of the parameter to check
        position: Position for positional args (default: 0)

    """

    def check_command_name(*args: Any, **kwargs: Any) -> Union[bool, str]:
      value = CommonGuards._extract_param(param_name, position, args, kwargs, default=None)

      if value is None:
        return f'{param_name} is required'

      cmd_str = str(value)

      # Check length
      if len(cmd_str) == 0 or len(cmd_str) > 50:
        return f'{param_name} must be between 1 and 50 characters'

      # Check pattern: start with letter, contain only valid characters
      if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', cmd_str):
        return (
          f'{param_name} must start with a letter and contain only '
          f'letters, numbers, hyphens, and underscores: {cmd_str}'
        )

      return True

    return check_command_name

  @staticmethod
  def valid_theme_name(param_name: str = 'theme', position: int = 0) -> GuardFunction:
    """Guard ensuring parameter is a valid Freyja theme name.

    Valid themes: 'colorful', 'universal'

    Args:
        param_name: Name of the parameter to check
        position: Position for positional args (default: 0)

    """

    def check_theme_name(*args: Any, **kwargs: Any) -> Union[bool, str]:
      value = CommonGuards._extract_param(param_name, position, args, kwargs, default=None)

      if value is None:
        return f'{param_name} is required'

      valid_themes = ['colorful', 'universal']
      theme_str = str(value).lower()

      if theme_str not in valid_themes:
        return f'{param_name} must be one of {valid_themes}: got {theme_str}'

      return True

    return check_theme_name

  @staticmethod
  def valid_shell_type(param_name: str = 'shell', position: int = 0) -> GuardFunction:
    """Guard ensuring parameter is a valid shell type for completion.

    Valid shells: 'bash', 'zsh', 'fish'

    Args:
        param_name: Name of the parameter to check
        position: Position for positional args (default: 0)

    """

    def check_shell_type(*args: Any, **kwargs: Any) -> Union[bool, str]:
      value = CommonGuards._extract_param(param_name, position, args, kwargs, default=None)

      if value is None:
        return f'{param_name} is required'

      valid_shells = ['bash', 'zsh', 'fish']
      shell_str = str(value).lower()

      if shell_str not in valid_shells:
        return f'{param_name} must be one of {valid_shells}: got {shell_str}'

      return True

    return check_shell_type


# Register Freyja-specific guards in the 'freyja' namespace
def register_freyja_guards():
  """Register all Freyja-specific guards in the modgud registry.

  This should be called during Freyja initialization to make these
  guards available for use.
  """
  register_guard('valid_command_name', CLIGuards.valid_command_name, namespace='freyja')
  register_guard('valid_theme_name', CLIGuards.valid_theme_name, namespace='freyja')
  register_guard('valid_shell_type', CLIGuards.valid_shell_type, namespace='freyja')


# Auto-register on module import
register_freyja_guards()
