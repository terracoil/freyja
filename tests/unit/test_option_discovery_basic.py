"""Basic OptionDiscovery functionality tests."""

import pytest
from freyja.parser.option_discovery import OptionDiscovery

from .option_discovery_fixtures import (
    SampleEnum, 
    MockCommandTree, 
    sample_class, 
    populated_tree_simple
)


class TestBasicOptionDiscovery:
  """Test basic OptionDiscovery functionality."""

  def test_discover_global_options(self, sample_class, populated_tree_simple):
    """Test discovering global options from main class constructor."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    global_options = discovery.discover_global_options()

    assert isinstance(global_options, set)
    assert '--config' in global_options
    assert '--debug' in global_options
    assert len(global_options) == 2

  def test_discover_command_options(self, sample_class, populated_tree_simple):
    """Test discovering command-specific options from methods."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    command_options = discovery.discover_command_options()

    assert isinstance(command_options, dict)
    assert 'process' in command_options
    assert '--output' in command_options['process']
    assert '--verbose' in command_options['process']
    # Note: input_file is positional, not an option

  def test_discover_positional_parameters(self, sample_class, populated_tree_simple):
    """Test discovering positional parameters from methods."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    positionals = discovery.discover_positional_parameters()

    assert isinstance(positionals, dict)
    assert 'process' in positionals
    assert positionals['process'] is not None
    assert positionals['process'].param_name == 'input_file'
    assert positionals['process'].is_required is True

  def test_get_all_known_options_flat_command(self, sample_class, populated_tree_simple):
    """Test aggregating all options for a flat command."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    all_options = discovery.get_all_known_options(['process'])

    assert isinstance(all_options, set)
    # Should include global + command options
    assert '--config' in all_options
    assert '--debug' in all_options
    assert '--output' in all_options
    assert '--verbose' in all_options

  def test_empty_class_no_options(self):
    """Test discovery with class that has no parameters."""

    class EmptyClass:
      def __init__(self):
        pass

      def simple_method(self):
        pass

    tree = MockCommandTree()
    discovery = OptionDiscovery(tree, EmptyClass)

    global_options = discovery.discover_global_options()
    command_options = discovery.discover_command_options()

    assert isinstance(global_options, set)
    assert len(global_options) == 0
    assert isinstance(command_options, dict)

  def test_method_without_parameters(self):
    """Test discovery for method with no parameters."""

    class SimpleClass:
      def __init__(self, config: str = 'test.json'):
        self.config = config

      def no_params(self):
        """Method with no parameters."""
        pass

    tree = MockCommandTree()
    tree.flat_commands = {
      'no_params': {
        'type': 'command',
        'function': SimpleClass.no_params,
      },
    }
    discovery = OptionDiscovery(tree, SimpleClass)

    command_options = discovery.discover_command_options()

    assert 'no_params' in command_options
    assert len(command_options['no_params']) == 0  # No options for this command

  def test_discover_global_options_no_target_class(self):
    """Test discover_global_options with no target class."""
    tree = MockCommandTree()
    discovery = OptionDiscovery(tree, None)  # No target class

    global_options = discovery.discover_global_options()
    assert isinstance(global_options, set)
    assert len(global_options) == 0

  def test_enum_parameter_handling(self, sample_class, populated_tree_simple):
    """Test handling of enum parameters in options discovery."""
    discovery = OptionDiscovery(populated_tree_simple, sample_class)

    command_options = discovery.discover_command_options()

    # convert method should have format parameter (enum type)
    assert 'convert' in command_options
    assert '--source' in command_options['convert']
    assert '--sample-format' in command_options['convert']


if __name__ == '__main__':
  pytest.main([__file__, '-v'])