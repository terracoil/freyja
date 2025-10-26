"""Tests for validation module to achieve 90%+ coverage."""

import inspect
from unittest.mock import Mock, patch

import pytest

from freyja.command.validation import ValidationService


class TestValidationService:
  """Test suite for ValidationService class."""

  def test_validate_constructor_parameters_valid(self):
    """Test constructor validation with valid class."""

    class ValidClass:
      def __init__(self, arg1: str = "default", arg2: int = 42):
        pass

    # Should not raise
    ValidationService.validate_constructor_parameters(ValidClass, "test class")

  def test_validate_constructor_parameters_no_params(self):
    """Test constructor validation with parameterless constructor."""

    class NoParamsClass:
      def __init__(self):
        pass

    # Should not raise
    ValidationService.validate_constructor_parameters(NoParamsClass, "test class")

  def test_validate_constructor_parameters_missing_defaults(self):
    """Test constructor validation with missing defaults."""

    class InvalidClass:
      def __init__(self, required_arg: str):
        pass

    with pytest.raises(ValueError, match="parameters without default values: required_arg"):
      ValidationService.validate_constructor_parameters(InvalidClass, "test class")

  def test_validate_constructor_parameters_allow_parameterless_only(self):
    """Test constructor validation with allow_parameterless_only flag."""

    class ClassWithDefaults:
      def __init__(self, arg: str = "default"):
        pass

    # Should not raise even with flag
    ValidationService.validate_constructor_parameters(
      ClassWithDefaults, "test class", allow_parameterless_only=True
    )

    class ClassWithoutDefaults:
      def __init__(self, required: str):
        pass

    with pytest.raises(ValueError, match="For classes using direct methods"):
      ValidationService.validate_constructor_parameters(
        ClassWithoutDefaults, "test class", allow_parameterless_only=True
      )

  def test_validate_constructor_parameters_with_varargs(self):
    """Test constructor validation with varargs."""

    class VarArgsClass:
      def __init__(self, *args, **kwargs):
        pass

    # Should not raise - varargs are ignored
    ValidationService.validate_constructor_parameters(VarArgsClass, "test class")

  def test_validate_constructor_parameters_exception_handling(self):
    """Test constructor validation exception handling."""

    class BadClass:
      # Invalid class that might cause inspection issues
      pass

    BadClass.__init__ = "not a method"  # Cause inspection error

    with pytest.raises(ValueError, match="Error validating constructor"):
      ValidationService.validate_constructor_parameters(BadClass, "test class")

  def test_validate_inner_class_constructor_valid(self):
    """Test inner class constructor validation with valid class."""

    class ValidInnerClass:
      def __init__(self, arg1: str = "default"):
        pass

    # Should not raise
    ValidationService.validate_inner_class_constructor_parameters(ValidInnerClass, "inner class")

  def test_validate_inner_class_constructor_with_main_param(self):
    """Test inner class constructor with main parameter pattern."""

    class InnerClassWithMain:
      def __init__(self, main, arg1: str = "default"):
        # Second param without annotation/default is assumed to be main instance
        pass

    # Should not raise
    ValidationService.validate_inner_class_constructor_parameters(InnerClassWithMain, "inner class")

  def test_validate_inner_class_constructor_malformed(self):
    """Test inner class constructor validation with malformed constructor."""

    class MalformedClass:
      def __init__(not_self):  # No 'self' parameter
        pass

    with pytest.raises(ValueError, match="malformed"):
      ValidationService.validate_inner_class_constructor_parameters(MalformedClass, "inner class")

  def test_validate_inner_class_constructor_missing_defaults(self):
    """Test inner class constructor with missing defaults."""

    class InvalidInnerClass:
      def __init__(self, required_arg: str):
        pass

    with pytest.raises(ValueError, match="parameters without default values: required_arg"):
      ValidationService.validate_inner_class_constructor_parameters(InvalidInnerClass, "inner class")

  def test_validate_inner_class_constructor_only_self(self):
    """Test inner class constructor with only self parameter."""

    class OnlySelfClass:
      def __init__(self):
        pass

    # Should not raise
    ValidationService.validate_inner_class_constructor_parameters(OnlySelfClass, "inner class")

  def test_validate_function_signature_valid(self):
    """Test function signature validation with valid function."""

    def valid_func(arg1: str, arg2: int = 42) -> None:
      pass

    assert ValidationService.validate_function_signature(valid_func) is True

  def test_validate_function_signature_missing_annotations(self):
    """Test function signature validation with missing annotations."""

    def invalid_func(arg1, arg2=42):
      pass

    assert ValidationService.validate_function_signature(invalid_func) is False

  def test_validate_function_signature_with_self(self):
    """Test function signature validation with self parameter."""

    class MyClass:
      def method(self, arg1: str) -> None:
        pass

    assert ValidationService.validate_function_signature(MyClass.method) is True

  def test_validate_function_signature_with_varargs(self):
    """Test function signature validation with varargs."""

    def func_with_varargs(arg1: str, *args, **kwargs) -> None:
      pass

    # Varargs are skipped
    assert ValidationService.validate_function_signature(func_with_varargs) is True

  def test_validate_function_signature_exception(self):
    """Test function signature validation with invalid input."""
    # Not a callable
    assert ValidationService.validate_function_signature("not a function") is False

  def test_get_validation_errors_no_errors(self):
    """Test get_validation_errors with valid inputs."""

    class ValidClass:
      def __init__(self, arg: str = "default"):
        pass

    def valid_func(arg: int) -> None:
      pass

    errors = ValidationService.get_validation_errors(ValidClass, {"func": valid_func})
    assert errors == []

  def test_get_validation_errors_class_error(self):
    """Test get_validation_errors with class constructor error."""

    class InvalidClass:
      def __init__(self, required: str):
        pass

    errors = ValidationService.get_validation_errors(InvalidClass, {})
    assert len(errors) == 1
    assert "parameters without default values" in errors[0]

  def test_get_validation_errors_function_error(self):
    """Test get_validation_errors with function signature error."""

    def invalid_func(untyped_arg):
      pass

    errors = ValidationService.get_validation_errors(None, {"invalid_func": invalid_func})
    assert len(errors) == 1
    assert "invalid signature" in errors[0]

  def test_get_validation_errors_multiple_errors(self):
    """Test get_validation_errors with multiple errors."""

    class InvalidClass:
      def __init__(self, required: str):
        pass

    def invalid_func(untyped_arg):
      pass

    def valid_func(arg: int) -> None:
      pass

    errors = ValidationService.get_validation_errors(
      InvalidClass, {"invalid_func": invalid_func, "valid_func": valid_func}
    )
    assert len(errors) == 2