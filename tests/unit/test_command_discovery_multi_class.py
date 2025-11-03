"""Multi-class CommandDiscovery tests."""

import pytest
from freyja.command import CommandDiscovery

from .command_discovery_fixtures import MockClass, MockClassSimple, MockClassWithInner


class TestMultiClassCommandDiscovery:
  """Test multi-class CommandDiscovery functionality."""

  def test_discover_from_multi_class(self):
    """Test discovering cmd_tree from multiple classes."""
    classes = [MockClass, MockClassSimple]
    discovery = CommandDiscovery(classes, completion=False)
    commands = discovery.cmd_tree

    # Hierarchical structure for namespaced class, flat cmds for primary class
    command_names = list(commands.keys())
    assert 'mock-class' in command_names  # From MockClass (namespaced group)
    assert 'simple-method' in command_names  # From MockClassSimple (primary class, flat)

    # Check that MockClass methods are inside the mock-class group
    mock_class_group = commands['mock-class']
    assert mock_class_group['type'] == 'group'
    assert 'method-one' in mock_class_group['cmd_tree']  # From MockClass
    assert 'method-two' in mock_class_group['cmd_tree']  # From MockClass

    # Check metadata for namespacing
    # First class (MockClass) cmd_tree should be namespaced
    method_one_cmd_dict = mock_class_group['cmd_tree']['method-one']
    method_one_cmd = method_one_cmd_dict['command_info']
    assert method_one_cmd.metadata['is_namespaced'] is True
    assert method_one_cmd.metadata['class_namespace'] == 'mock-class'
    assert method_one_cmd.metadata['source_class'] == MockClass

    # Last class (MockClassSimple) should be in global namespace
    simple_cmd_dict = commands['simple-method']
    simple_cmd = simple_cmd_dict['command_info']
    assert simple_cmd.metadata['is_namespaced'] is False
    assert simple_cmd.metadata['class_namespace'] is None


if __name__ == '__main__':
  pytest.main([__file__, '-v'])