"""Basic CommandDiscovery functionality tests."""

import inspect

import pytest
from freyja.cli import TargetModeEnum
from freyja.command import CommandDiscovery

from .command_discovery_fixtures import MockClass, MockClassSimple


class TestBasicCommandDiscovery:
  """Test basic CommandDiscovery functionality."""

  def test_init_with_single_class(self):
    """Test initialization with single class target."""
    discovery = CommandDiscovery(MockClassSimple, completion=False)

    assert discovery.mode == TargetModeEnum.CLASS
    assert discovery.primary_class == MockClassSimple  # Unified handling
    assert discovery.target_classes == [MockClassSimple]

  def test_init_with_class_list(self):
    """Test initialization with list of classes."""
    classes = [MockClass, MockClassSimple]
    discovery = CommandDiscovery(classes, completion=False)

    assert discovery.mode == TargetModeEnum.CLASS
    assert discovery.primary_class == MockClassSimple  # Last class in list
    assert discovery.target_classes == classes

  def test_init_with_invalid_target(self):
    """Test initialization with invalid target raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
      CommandDiscovery('invalid_target')

    assert 'Target must be class or list of classes' in str(exc_info.value)

  def test_discover_from_simple_class(self):
    """Test discovering cmd_tree from a simple class without inner classes."""
    discovery = CommandDiscovery(MockClassSimple, completion=False)
    commands = discovery.cmd_tree

    # Should find public methods only
    command_names = list(commands.keys())
    assert 'simple-method' in command_names
    assert len(commands) == 1

    # Check command info
    cmd_dict = commands['simple-method']
    assert cmd_dict['type'] == 'command'
    assert cmd_dict['original_name'] == 'simple_method'
    assert not cmd_dict['command_info'].is_hierarchical
    assert cmd_dict['command_info'].parent_class is None
    assert cmd_dict['command_info'].inner_class is None

  def test_custom_method_filter(self):
    """Test custom method filter."""

    # Filter that only allows methods starting with 'method'
    def custom_filter(target_class, name, obj):
      return name.startswith('method') and callable(obj)

    discovery = CommandDiscovery(MockClass, method_filter=custom_filter, completion=False)
    commands = discovery.cmd_tree

    # Should find method_one and method_two but not others
    command_names = list(commands.keys())
    assert 'method-one' in command_names
    assert 'method-two' in command_names
    all_command_infos = commands.get_all_commands()
    assert len([cmd for cmd in all_command_infos if not cmd.is_hierarchical]) == 2

  def test_command_info_structure(self):
    """Test CommandInfo data structure completeness."""
    discovery = CommandDiscovery(MockClassSimple, completion=False)
    commands = discovery.cmd_tree

    # Get the first command from the tree
    command_names = list(commands.keys())
    assert len(command_names) > 0
    first_command_name = command_names[0]
    cmd = commands.tree[first_command_name]['command_info']

    # Test required fields
    assert isinstance(cmd.name, str)
    assert isinstance(cmd.original_name, str)
    assert callable(cmd.function)
    assert isinstance(cmd.signature, inspect.Signature)

    # Test optional fields have correct types when present
    assert cmd.docstring is None or isinstance(cmd.docstring, str)
    assert isinstance(cmd.is_hierarchical, bool)
    assert cmd.parent_class is None or isinstance(cmd.parent_class, str)
    assert cmd.command_path is None or isinstance(cmd.command_path, str)
    assert cmd.inner_class is None or inspect.isclass(cmd.inner_class)
    assert isinstance(cmd.metadata, dict)

  def test_validate_classes_empty_list(self):
    """Test _validate_classes with empty list."""
    with pytest.raises(ValueError) as exc_info:
      CommandDiscovery._validate_classes([])

    assert "no target classes were found" in str(exc_info.value)

  def test_validate_classes_invalid_items(self):
    """Test _validate_classes with invalid items in list."""
    with pytest.raises(ValueError) as exc_info:
      CommandDiscovery._validate_classes([MockClass, "not_a_class", MockClassSimple])

    assert "All items in list must be classes" in str(exc_info.value)
    assert "str" in str(exc_info.value)

  def test_discover_with_completion_enabled(self):
    """Test discovery with completion enabled adds system classes."""
    discovery = CommandDiscovery(MockClassSimple, completion=True)

    # Should have system classes added
    assert len(discovery.target_classes) > 1
    # Should still work and have our simple method
    commands = discovery.cmd_tree
    assert 'simple-method' in commands

  def test_discover_with_theme_tuner_enabled(self):
    """Test discovery with theme tuner enabled adds system classes."""
    discovery = CommandDiscovery(MockClassSimple, theme_tuner=True)

    # Should have system classes added
    assert len(discovery.target_classes) > 1
    commands = discovery.cmd_tree
    assert 'simple-method' in commands

  def test_method_filtering_edge_cases(self):
    """Test method filtering with edge cases."""

    # Filter that rejects everything
    def reject_all_filter(target_class, name, obj):
      return False

    discovery = CommandDiscovery(MockClassSimple, method_filter=reject_all_filter, completion=False)
    commands = discovery.cmd_tree

    # Should have no commands (all filtered out)
    assert len(commands) == 0 or all(cmd_dict['type'] != 'command' for cmd_dict in commands.values())

  def test_is_system_method(self):
    """Test is_system method for identifying system classes."""
    discovery = CommandDiscovery(MockClassSimple, completion=False)

    # User classes should not be system classes
    assert not discovery.is_system(MockClassSimple)
    assert not discovery.is_system(MockClass)


if __name__ == '__main__':
  pytest.main([__file__, '-v'])