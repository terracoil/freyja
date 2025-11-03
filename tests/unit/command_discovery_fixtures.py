"""Shared fixtures and mock classes for CommandDiscovery tests."""


class MockClass:
  """Mock class for testing command discovery."""

  def __init__(self, config: str = 'default'):
    """Initialize mock class with config."""
    self.config = config

  def method_one(self, param: str) -> None:
    """First method for testing."""
    pass

  def method_two(self, count: int = 10, flag: bool = True) -> str:
    """Second method for testing."""
    return 'result'

  def _private_method(self) -> None:
    """Private method that should be ignored."""
    pass


class MockClassWithInner:
  """Mock class with inner classes for hierarchical testing."""

  def __init__(self, base_config: str = 'base'):
    """Initialize with base config."""
    self.base_config = base_config

  def direct_method(self, param: str) -> None:
    """Direct method on main class."""
    pass

  class InnerOperations:
    """Inner class for grouped operations."""

    def __init__(self, inner_config: str = 'inner'):
      """Initialize with inner config."""
      self.inner_config = inner_config

    def inner_method_one(self, data: str) -> None:
      """First inner method."""
      pass

    def inner_method_two(self, count: int = 3) -> str:
      """Second inner method."""
      return 'inner_result'

  class DataProcessing:
    """Another inner class for data operations."""

    def __init__(self, processing_mode: str = 'auto'):
      """Initialize with processing mode."""
      self.processing_mode = processing_mode

    def process_data(self, input_data: str, format_type: str = 'json') -> None:
      """Process data method."""
      pass


class MockClassSimple:
  """Simple mock class without inner classes."""

  def __init__(self):
    """Initialize simple mock class."""
    pass

  def simple_method(self, value: int) -> None:
    """Simple method for testing."""
    pass