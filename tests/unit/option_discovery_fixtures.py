"""Shared fixtures and mock classes for OptionDiscovery tests."""

import enum
import pytest


class SampleEnum(enum.Enum):
  """Test enum."""

  OPTION_A = 'a'
  OPTION_B = 'b'


class MockCommandTree:
  """Mock command tree for testing OptionDiscovery."""

  def __init__(self):
    """Initialize mock command tree for testing."""
    self.flat_commands = {}
    self.groups = {}


@pytest.fixture
def sample_class():
  """Create sample class with methods."""

  class SampleClass:
    def __init__(self, config: str = 'default.json', debug: bool = False):
      self.config = config
      self.debug = debug

    def process(self, input_file: str, output: str = 'out.txt', verbose: bool = False):
      """Process file."""
      pass

    def convert(self, source: str, sample_format: SampleEnum = SampleEnum.OPTION_A):
      """Convert file."""
      pass

  return SampleClass


@pytest.fixture
def class_with_inner():
  """Create class with inner class."""

  class MainClass:
    def __init__(self, main_config: str = 'main.json'):
      self.main_config = main_config

    class DataOps:
      def __init__(self, main, data_dir: str = './data', parallel: bool = False):
        self.main = main
        self.data_dir = data_dir
        self.parallel = parallel

      def process_batch(self, pattern: str, limit: int = 100):
        """Process batch."""
        pass

  return MainClass


@pytest.fixture
def populated_tree_simple(sample_class):
  """Create populated command tree for simple class."""
  tree = MockCommandTree()
  # Add flat commands
  tree.flat_commands = {
    'process': {
      'type': 'command',
      'function': sample_class.process,
    },
    'convert': {
      'type': 'command',
      'function': sample_class.convert,
    },
  }
  return tree


@pytest.fixture
def populated_tree_hierarchical(class_with_inner):
  """Create populated command tree for class with inner classes."""
  tree = MockCommandTree()
  # Add group with inner class
  tree.groups = {
    'data-ops': {
      'type': 'group',
      'inner_class': class_with_inner.DataOps,
      'commands': {
        'process-batch': {
          'type': 'command',
          'function': class_with_inner.DataOps.process_batch,
        },
      },
    },
  }
  return tree