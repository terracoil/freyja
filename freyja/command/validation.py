"""Validation utilities for FreyjaCLI generation and parameter checking."""

import inspect
from typing import Any


class ValidationService:
  """Centralized validation service for FreyjaCLI parameter and constructor validation."""

  @staticmethod
  def validate_constructor_parameters(
    cls: type, context: str, allow_parameterless_only: bool = False
  ) -> None:
    """Validate constructor compatibility for FreyjaCLI argument generation.

    Constructor parameters become FreyjaCLI arguments during command execution.

    :param cls: The class to validate
    :param context: Context string for error messages
    :param allow_parameterless_only: Only allows parameterless constructors
    :raises ValueError: If constructor has parameters without defaults
    """
    try:
      sig = inspect.signature(cls)
      params_without_defaults = []

      for param_name, param in sig.parameters.items():
        # Skip varargs (self is excluded by signature(cls))
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
          continue

        # Check if parameter has no default value
        if param.default == param.empty:
          params_without_defaults.append(param_name)

      if params_without_defaults:
        param_list = ', '.join(params_without_defaults)
        class_name = cls.__name__

        if allow_parameterless_only:
          error_msg = (
            f"Constructor for {context} '{class_name}' has parameters without "
            f'default values: {param_list}. For classes using direct methods, '
            'constructor must be parameterless or all params must have defaults.'
          )
        else:
          error_msg = (
            f"Constructor for {context} '{class_name}' has parameters without "
            f'default values: {param_list}. All constructor parameters must have '
            'default values to be used as FreyjaCLI arguments.'
          )
        raise ValueError(error_msg)

    except Exception as e:
      # Re-raise ValueError as-is, others as ValueError with context
      error_to_raise = (
        e
        if isinstance(e, ValueError)
        else ValueError(f"Error validating constructor for {context} '{cls.__name__}': {e}")
      )
      if not isinstance(e, ValueError):
        error_to_raise.__cause__ = e
      raise error_to_raise from e

  @staticmethod
  def validate_inner_class_constructor_parameters(cls: type, context: str) -> None:
    """Validate inner class constructors for main instance injection."""
    try:
      # Inspect __init__ directly so we can validate that the first parameter is
      # actually named 'self' (legal Python doesn't require this, but freyja does).
      raw_params = list(inspect.signature(cls.__init__).parameters.items())  # type: ignore[misc]
      if not raw_params or raw_params[0][0] != 'self':
        raise ValueError(f"Constructor for {context} '{cls.__name__}' malformed (no self param)")

      sig = inspect.signature(cls)
      params = list(sig.parameters.items())
      params_without_defaults = []

      # signature(cls) already omits self; if any params remain, params[0] is "main"
      # under the new pattern (no default, no annotation) or a real arg under the old.
      if params:
        first_name, first_param = params[0]

        # If first parameter has no default and no annotation, assume it's main
        if first_param.default == first_param.empty and first_param.annotation == first_param.empty:
          # New pattern: main parameter - check remaining params for defaults
          for param_name, param in params[1:]:  # Skip main
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
              continue
            if param.default == param.empty:
              params_without_defaults.append(param_name)
        else:
          # Old pattern: all params need defaults
          for param_name, param in params:
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
              continue
            if param.default == param.empty:
              params_without_defaults.append(param_name)

      if params_without_defaults:
        param_list = ', '.join(params_without_defaults)
        class_name = cls.__name__
        error_msg = (
          f"Constructor for {context} '{class_name}' has parameters without "
          f'default values: {param_list}. All constructor parameters must have '
          'default values to be used as FreyjaCLI arguments.'
        )
        raise ValueError(error_msg)

    except Exception as e:
      # Re-raise ValueError as-is, others as ValueError with context
      error_to_raise = (
        e
        if isinstance(e, ValueError)
        else ValueError(f'Error validating inner class constructor for {context}: {e}')
      )
      if not isinstance(e, ValueError):
        error_to_raise.__cause__ = e
      raise error_to_raise from e

  @staticmethod
  def validate_function_signature(func: Any) -> bool:
    """Validate that functions have type annotations for argument generation."""
    result = True
    try:
      sig = inspect.signature(func)

      # Check each parameter has compatible type annotation
      for param_name, param in sig.parameters.items():
        # Skip self parameter and varargs
        if param_name == 'self' or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
          continue

        # Function must have type annotations for FreyjaCLI generation
        if param.annotation == param.empty:
          result = False
          break

    except (ValueError, TypeError):
      result = False

    return result

  @staticmethod
  def get_validation_errors(cls: type, functions: dict[str, Any]) -> list[str]:
    """Get validation errors for FreyjaCLI generation."""
    errors = []

    # Validate class constructor if provided
    if cls:
      try:
        ValidationService.validate_constructor_parameters(cls, 'main class')
      except ValueError as e:
        errors.append(str(e))

    # Validate each function
    for func_name, func in functions.items():
      if not ValidationService.validate_function_signature(func):
        errors.append(f"Function '{func_name}' has invalid signature for FreyjaCLI generation")

    return errors
