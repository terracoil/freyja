"""Guard clause integration for Freyja CLI methods.

This module provides access to modgud's guard functionality through a Freyja-specific
namespace. This prevents conflicts if the user has both freyja and modgud installed.

The vendored modgud is located at freyja/utils/modgud and is a git submodule.
"""

# Import from vendored modgud submodule
from freyja.utils.modgud.modgud import (
  # Main decorator
  guarded_expression,
  # Common guard validators (can import directly or via CommonGuards)
  not_empty,
  not_none,
  positive,
  in_range,
  type_check,
  matches_pattern,
  valid_file_path,
  valid_url,
  valid_enum,
  # Guard registry functions
  register_guard,
  get_guard,
  has_custom_guard,
  list_custom_guards,
  list_guard_namespaces,
  unregister_guard,
  get_registry,
  # Errors
  GuardClauseError,
)

# Re-export with Freyja-specific naming
__all__ = [
  # Main decorator
  'guarded',
  # Direct guard imports (preferred style per modgud v1.0+)
  'not_empty',
  'not_none',
  'positive',
  'in_range',
  'type_check',
  'matches_pattern',
  'valid_file_path',
  'valid_url',
  'valid_enum',
  # Custom guard registration
  'register_guard',
  'get_guard',
  'has_custom_guard',
  'list_custom_guards',
  'list_guard_namespaces',
  'unregister_guard',
  'get_registry',
  # Errors
  'GuardClauseError',
]

# Alias for Freyja usage - shorter, more concise name
guarded = guarded_expression
