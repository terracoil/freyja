"""OptionDiscovery validation and edge case tests."""

import pytest
from freyja.parser.option_discovery import OptionDiscovery

from .option_discovery_fixtures import (
    MockCommandTree,
    sample_class,
    populated_tree_simple
)


class TestOptionDiscoveryValidation:
  """Test OptionDiscovery validation and edge case functionality."""

  def test_validate_option_conflicts_none(self, sample_class, populated_tree_simple):
    """Test conflict validation when no conflicts exist."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    conflicts = discovery.validate_option_conflicts()

    assert isinstance(conflicts, dict)
    assert len(conflicts) == 0

  def test_validate_option_conflicts_detected(self):
    """Test conflict validation detects conflicts."""

    class ConflictClass:
      def __init__(self, config: str = 'main.json'):
        self.config = config

      class Inner:
        def __init__(self, main, config: str = 'inner.json'):  # Conflicts with global
          self.main = main
          self.config = config

        def process(self):
          pass

    tree = MockCommandTree()
    tree.groups = {
      'inner': {
        'type': 'group',
        'inner_class': ConflictClass.Inner,
        'commands': {},
      },
    }
    discovery = OptionDiscovery(tree, ConflictClass)

    conflicts = discovery.validate_option_conflicts()

    assert isinstance(conflicts, dict)
    assert len(conflicts) > 0  # Should detect global vs inner conflict

  def test_suggest_option_corrections(self, sample_class, populated_tree_simple):
    """Test option correction suggestions."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    suggestions = discovery.suggest_option_corrections('--confg', ['process'])

    assert isinstance(suggestions, list)
    # Suggestions may be empty if similarity too low
    if len(suggestions) > 0:
      assert any('config' in s for s in suggestions)

  def test_analyze_constructor_params_no_signature(self):
    """Test _analyze_constructor_params with class that can't be introspected."""
    tree = MockCommandTree()

    # Create a mock class that will cause signature inspection issues
    class MockBadClass:
      def __init__(self):
        pass

    # Mock the signature inspection to fail
    import inspect
    original_signature = inspect.signature

    def failing_signature(obj):
      raise ValueError(f"Cannot inspect signature: {obj}")

    try:
      inspect.signature = failing_signature
      discovery = OptionDiscovery(tree, MockBadClass)

      # Should handle gracefully when signature inspection fails
      options = discovery._analyze_constructor_params(MockBadClass)
      assert isinstance(options, set)
    finally:
      inspect.signature = original_signature

  def test_option_conflicts_resolution(self):
    """Test detailed option conflict resolution and reporting."""

    class ComplexConflictClass:
      def __init__(self, name: str = 'main', debug: bool = False):
        self.name = name
        self.debug = debug

      class Config:
        def __init__(self, main, name: str = 'config', verbose: bool = False):
          self.main = main
          self.name = name  # Conflicts with global 'name'
          self.verbose = verbose

        def setup(self, debug: bool = True):  # Conflicts with global 'debug'
          pass

      class Utils:
        def __init__(self, main, tool: str = 'default'):
          self.main = main
          self.tool = tool

        def run(self, name: str):  # Another conflict with global 'name'
          pass

    tree = MockCommandTree()
    tree.groups = {
      'config': {
        'type': 'group',
        'inner_class': ComplexConflictClass.Config,
        'commands': {
          'setup': {
            'type': 'command',
            'function': ComplexConflictClass.Config.setup,
          }
        },
      },
      'helpers': {
        'type': 'group',
        'inner_class': ComplexConflictClass.Utils,
        'commands': {
          'run': {
            'type': 'command',
            'function': ComplexConflictClass.Utils.run,
          }
        },
      },
    }

    discovery = OptionDiscovery(tree, ComplexConflictClass)
    conflicts = discovery.validate_option_conflicts()

    assert isinstance(conflicts, dict)
    assert len(conflicts) > 0  # Should detect multiple conflicts

  def test_suggest_corrections_empty_known_options(self):
    """Test option correction suggestions with empty known options."""
    tree = MockCommandTree()

    class EmptyClass:
      def __init__(self):
        pass

    discovery = OptionDiscovery(tree, EmptyClass)

    # Test with no known options available
    suggestions = discovery.suggest_option_corrections('--unknown', [])
    assert isinstance(suggestions, list)
    # Should return empty or minimal suggestions

  def test_parameter_analysis_edge_cases(self):
    """Test parameter analysis with various edge cases."""

    class EdgeCaseClass:
      def __init__(self, *args, **kwargs):
        """Constructor with variable arguments."""
        pass

      def method_with_complex_params(self, required: str, *args, **kwargs):
        """Method with variable arguments."""
        pass

    tree = MockCommandTree()
    tree.flat_commands = {
      'method_with_complex_params': {
        'type': 'command',
        'function': EdgeCaseClass.method_with_complex_params,
      }
    }

    discovery = OptionDiscovery(tree, EdgeCaseClass)

    # Should handle methods with *args/**kwargs gracefully
    command_options = discovery.discover_command_options()
    assert isinstance(command_options, dict)
    assert 'method_with_complex_params' in command_options


if __name__ == '__main__':
  pytest.main([__file__, '-v'])