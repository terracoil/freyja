"""Guard clause integration for Freyja CLI methods.

This module provides access to modgud's guard functionality through a Freyja-specific
namespace. This prevents conflicts if the user has both freyja and modgud installed.

The vendored modgud is located at freyja/utils/modgud and is a git submodule.

Modgud v2.1.0 changed the registry API from module-level functions to class methods
on GuardRegistry. This module provides backward-compatible wrapper functions.
"""

# Import from vendored modgud submodule (v2.1.0)
from freyja.utils.modgud.modgud import (
  # Main decorator
  guarded_expression,
  # Common guard validators
  not_empty,
  not_none,
  positive,
  in_range,
  type_check,
  matches_pattern,
  valid_file_path,
  valid_url,
  valid_enum,
  # Guard registry class (v2.1.0 API)
  GuardRegistry,
  # Errors
  GuardClauseError,
)


# Wrapper functions for backward compatibility with v1.0.1 API
def register_guard(name, guard_factory, namespace=None):
  """Register a custom guard (wrapper for GuardRegistry.register)."""
  return GuardRegistry.register(name, guard_factory, namespace)


def get_guard(name, namespace=None):
  """Get a registered guard (wrapper for GuardRegistry.get)."""
  return GuardRegistry.get(name, namespace)


def has_custom_guard(name, namespace=None):
  """Check if guard exists (wrapper for GuardRegistry.has_guard)."""
  return GuardRegistry.has_guard(name, namespace)


def list_custom_guards(namespace=None):
  """List custom guards (wrapper for GuardRegistry.list_guards)."""
  return GuardRegistry.list_guards(namespace)


def list_guard_namespaces():
  """List namespaces (wrapper for GuardRegistry.list_namespaces)."""
  return GuardRegistry.list_namespaces()


def unregister_guard(name, namespace=None):
  """Unregister a guard (wrapper for GuardRegistry.unregister)."""
  return GuardRegistry.unregister(name, namespace)


def get_registry():
  """Get registry instance (wrapper for GuardRegistry.instance)."""
  return GuardRegistry.instance()


# Alias for Freyja usage - shorter, more concise name
guarded = guarded_expression

# Re-export with Freyja-specific naming
__all__ = [
  # Main decorator
  'guarded',
  'guarded_expression',
  # Direct guard imports (preferred style per modgud v2.1.0+)
  'not_empty',
  'not_none',
  'positive',
  'in_range',
  'type_check',
  'matches_pattern',
  'valid_file_path',
  'valid_url',
  'valid_enum',
  # Registry class (v2.1.0 API)
  'GuardRegistry',
  # Custom guard registration (backward-compatible wrappers)
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
