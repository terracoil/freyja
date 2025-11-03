"""Test configuration and fixtures for freyja tests."""

import enum
from pathlib import Path

import pytest


class TestEnum(enum.Enum):
  """Test enumeration for FreyjaCLI testing."""

  OPTION_A = 1
  OPTION_B = 2
  OPTION_C = 3


def sample_function(name: str = 'world', count: int = 1):
  """Sample function with docstring parameters.

  :param name: The name to greet in the message
  :param count: Number of times to repeat the greeting
  """
  return f'Hello {name}! ' * count


def function_with_types(
  text: str,
  number: int = 42,
  ratio: float = 3.14,
  active: bool = False,
  choice: TestEnum = TestEnum.OPTION_A,
  file_path: Path | None = None,
):
  """Function with various type annotations.

  :param text: Required text input parameter
  :param number: Optional integer with default value
  :param ratio: Optional float with default value
  :param active: Boolean flag parameter
  :param choice: Enumeration choice parameter
  :param file_path: Optional file path parameter
  """
  return {
    'text': text,
    'number': number,
    'ratio': ratio,
    'active': active,
    'choice': choice,
    'file_path': file_path,
  }


def function_without_docstring():
  """Function without parameter docstrings."""
  return 'No docstring parameters'


def function_with_args_kwargs(required: str, *args, **kwargs):
  """Function with *args and **kwargs.

  :param required: Required parameter
  """
  return f'Required: {required}, args: {args}, kwargs: {kwargs}'


class SampleTestClass:
  """Sample class for testing."""

  def __init__(self, config: str = 'test.json', debug: bool = False):
    """Initialize test class with config and debug settings."""
    self.config = config
    self.debug = debug

  def sample_method(self, name: str = 'world', count: int = 1):
    """Sample method with parameters."""
    return f'Hello {name}! ' * count

  def method_with_types(
    self,
    text: str,
    number: int = 42,
    ratio: float = 3.14,
    active: bool = False,
    choice: TestEnum = TestEnum.OPTION_A,
    file_path: Path | None = None,
  ):
    """Method with various type annotations."""
    return {
      'text': text,
      'number': number,
      'ratio': ratio,
      'active': active,
      'choice': choice,
      'file_path': file_path,
    }


@pytest.fixture
def sample_test_class():
  """Provide a sample class for testing."""
  return SampleTestClass


@pytest.fixture
def sample_function_opts():
  """Provide sample function options for backward compatibility tests."""
  return {
    'sample_function': {'description': 'Sample function for testing'},
    'function_with_types': {'description': 'Function with various types'},
  }


@pytest.fixture
def complex_nested_class():
  """Provide a class with 3+ levels of nesting for edge case testing."""

  class OuterClass:
    """Outer class with nested inner classes."""

    def __init__(self, config: str = 'outer.json'):
      self.config = config

    def outer_method(self, value: str = 'outer') -> str:
      """Outer method."""
      return f'Outer: {value}'

    class MiddleClass:
      """Middle class nested in outer."""

      def __init__(self, setting: str = 'middle'):
        self.setting = setting

      def middle_method(self, value: str = 'middle') -> str:
        """Middle method."""
        return f'Middle: {value}'

      class InnerClass:
        """Inner class nested in middle."""

        def __init__(self, option: str = 'inner'):
          self.option = option

        def inner_method(self, value: str = 'inner') -> str:
          """Inner method."""
          return f'Inner: {value}'

        class DeepClass:
          """Deepest nested class."""

          def deep_method(self, value: str = 'deep') -> str:
            """Deep method."""
            return f'Deep: {value}'

  return OuterClass


@pytest.fixture
def edge_case_methods_class():
  """Provide a class with unusual but valid method signatures."""

  class EdgeCaseClass:
    """Class with edge case method signatures."""

    def __init__(self):
      pass

    def method_single_required(self, required: str) -> str:
      """Method with only one required parameter (becomes positional)."""
      return required

    def method_multiple_required(self, first: str, second: int, third: bool) -> str:
      """Method with multiple required parameters."""
      return f'{first}-{second}-{third}'

    def method_many_params(
      self,
      a: str,
      b: str = 'b',
      c: int = 1,
      d: float = 1.0,
      e: bool = False,
      f: str = 'f',
      g: str = 'g',
      h: str = 'h',
    ) -> str:
      """Method with many parameters."""
      return f'{a}-{b}-{c}-{d}-{e}-{f}-{g}-{h}'

    def method_with_union_types(self, value: str | int = 'default') -> str:
      """Method with union type annotation."""
      return str(value)

    def method_with_list(self, items: list[str] = None) -> str:
      """Method with list parameter."""
      items = items or []
      return ','.join(items)

    def method_with_dict(self, config: dict[str, str] = None) -> str:
      """Method with dict parameter."""
      config = config or {}
      return str(config)

  return EdgeCaseClass


@pytest.fixture
def mock_terminal():
  """Provide mock terminal for testing interactive features."""

  class MockTerminal:
    """Mock terminal for capturing and simulating terminal interactions."""

    def __init__(self):
      self.width = 80
      self.height = 24
      self.supports_color = True
      self.inputs = []
      self.outputs = []

    def set_size(self, width: int, height: int) -> None:
      """Set terminal size."""
      self.width = width
      self.height = height

    def set_color_support(self, supports: bool) -> None:
      """Set color support."""
      self.supports_color = supports

    def add_input(self, text: str) -> None:
      """Add simulated user input."""
      self.inputs.append(text)

    def get_input(self) -> str:
      """Get next simulated input."""
      return self.inputs.pop(0) if self.inputs else ''

    def write_output(self, text: str) -> None:
      """Capture output written to terminal."""
      self.outputs.append(text)

    def get_outputs(self) -> list[str]:
      """Get all captured outputs."""
      return self.outputs.copy()

    def clear_outputs(self) -> None:
      """Clear captured outputs."""
      self.outputs.clear()

  return MockTerminal()


def pytest_configure(config):
  """Configure pytest markers."""
  config.addinivalue_line('markers', 'slow: marks tests as slow (deselect with \'-m "not slow"\')')


def pytest_collection_modifyitems(config, items):
  """Automatically mark certain tests as slow."""
  for item in items:
    if 'external_links' in item.nodeid:
      item.add_marker(pytest.mark.slow)
