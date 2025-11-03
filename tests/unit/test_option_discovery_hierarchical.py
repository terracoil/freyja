"""Hierarchical OptionDiscovery tests for inner classes and groups."""

import pytest
from freyja.parser.option_discovery import OptionDiscovery

from .option_discovery_fixtures import (
    class_with_inner,
    populated_tree_hierarchical
)


class TestHierarchicalOptionDiscovery:
  """Test hierarchical OptionDiscovery functionality with inner classes."""

  def test_discover_subglobal_options(self, class_with_inner, populated_tree_hierarchical):
    """Test discovering sub-global options from inner class constructors."""
    discovery = OptionDiscovery(populated_tree_hierarchical, class_with_inner)

    subglobal_options = discovery.discover_subglobal_options()

    assert isinstance(subglobal_options, dict)
    assert 'data-ops' in subglobal_options
    assert '--data-dir' in subglobal_options['data-ops']
    assert '--parallel' in subglobal_options['data-ops']

  def test_get_all_known_options_hierarchical_command(
    self, class_with_inner, populated_tree_hierarchical
  ):
    """Test aggregating all options for hierarchical command."""
    discovery = OptionDiscovery(populated_tree_hierarchical, class_with_inner)

    all_options = discovery.get_all_known_options(['data-ops', 'process-batch'])

    assert isinstance(all_options, set)
    # Should include global + subglobal + command options
    assert '--main-config' in all_options  # Global
    assert '--data-dir' in all_options  # Sub-global
    assert '--parallel' in all_options  # Sub-global
    assert '--limit' in all_options  # Command
    # Note: pattern is positional, not an option

  def test_discover_positional_with_groups(self, class_with_inner, populated_tree_hierarchical):
    """Test discovering positional parameters with hierarchical groups."""
    discovery = OptionDiscovery(populated_tree_hierarchical, class_with_inner)

    positionals = discovery.discover_positional_parameters()

    assert isinstance(positionals, dict)
    # Should find positional parameter in hierarchical command
    hierarchical_key = 'data-ops--process-batch'
    assert hierarchical_key in positionals
    assert positionals[hierarchical_key].param_name == 'pattern'


if __name__ == '__main__':
  pytest.main([__file__, '-v'])