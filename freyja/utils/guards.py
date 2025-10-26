"""Guard clause integration for Freyja CLI methods.

This module provides access to modgud's guard functionality through a Freyja-specific
namespace. This prevents conflicts if the user has both freyja and modgud installed.

The vendored modgud is located at freyja/utils/modgud and is a git submodule.
"""

# Import from vendored modgud submodule (note the extra 'modgud' in the path)
from freyja.utils.modgud.modgud import (
  CommonGuards,
  GuardClauseError,
  get_guard,
  guarded_expression,
  has_custom_guard,
  list_custom_guards,
  list_guard_namespaces,
  register_guard,
  unregister_guard,
)

# Re-export with Freyja-specific aliases
__all__ = [
  # Main decorator
  'guarded',
  # Common guards
  'Guards',
  # Custom guard registration
  'register_guard',
  'get_guard',
  'has_custom_guard',
  'list_custom_guards',
  'list_guard_namespaces',
  'unregister_guard',
  # Errors
  'GuardClauseError',
]

# Aliases for Freyja usage
guarded = guarded_expression  # Shorter, more Freyja-like name
Guards = CommonGuards  # Shorter name for guard factories
