"""Hierarchical CommandDiscovery tests for inner classes."""

import pytest
from freyja.command import CommandDiscovery

from .command_discovery_fixtures import MockClassWithInner, MockClassSimple


class TestHierarchicalCommandDiscovery:
  """Test hierarchical CommandDiscovery functionality with inner classes."""

  def test_discover_from_class_with_inner_classes(self):
    """Test discovering cmd_tree from class with inner classes."""
    discovery = CommandDiscovery(MockClassWithInner, completion=False)
    commands = discovery.cmd_tree

    # Should have direct method at top level
    assert 'direct-method' in commands
    assert commands['direct-method']['type'] == 'command'

    # Should have hierarchical groups
    assert 'inner-operations' in commands
    assert commands['inner-operations']['type'] == 'group'
    assert 'data-processing' in commands
    assert commands['data-processing']['type'] == 'group'

    # Check methods within inner-operations group
    inner_ops = commands['inner-operations']
    assert 'inner-method-one' in inner_ops['cmd_tree']
    assert 'inner-method-two' in inner_ops['cmd_tree']

    # Check methods within data-processing group
    data_proc = commands['data-processing']
    assert 'process-data' in data_proc['cmd_tree']

    # Check command structure within groups
    hierarchical_cmd = inner_ops['cmd_tree']['inner-method-one']
    assert hierarchical_cmd['type'] == 'command'
    assert hierarchical_cmd['command_info'].is_hierarchical
    assert hierarchical_cmd['command_info'].parent_class == 'InnerOperations'
    assert hierarchical_cmd['command_info'].command_path == 'inner-operations'
    assert hierarchical_cmd['command_info'].inner_class == MockClassWithInner.InnerOperations
    assert hierarchical_cmd['command_info'].group_name == 'inner-operations'
    assert hierarchical_cmd['command_info'].method_name == 'inner-method-one'
    assert 'inner_class' in hierarchical_cmd['command_info'].metadata

    # Check direct method
    direct_cmd = commands['direct-method']
    assert not direct_cmd['command_info'].is_hierarchical
    assert direct_cmd['command_info'].parent_class is None

  def test_discover_namespaced_inner_classes(self):
    """Test discovery with namespaced inner classes (multi-class scenario)."""
    classes = [MockClassWithInner, MockClassSimple]
    discovery = CommandDiscovery(classes, completion=False)
    commands = discovery.cmd_tree

    # First class should be namespaced
    namespaced_group_name = 'mock-class-with-inner'
    assert namespaced_group_name in commands

    # Check that inner classes are properly nested within namespaced group
    namespaced_group = commands[namespaced_group_name]
    assert 'inner-operations' in namespaced_group['cmd_tree']
    assert 'data-processing' in namespaced_group['cmd_tree']

    # Verify the hierarchical structure is maintained within namespaced groups
    inner_ops = namespaced_group['cmd_tree']['inner-operations']
    assert 'inner-method-one' in inner_ops['cmd_tree']


if __name__ == '__main__':
  pytest.main([__file__, '-v'])