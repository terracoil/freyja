"""Test suite for CommandDiscovery."""

import inspect

import pytest
from freyja.cli import TargetMode
from freyja.command import CommandDiscovery


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


class TestCommandDiscovery:
  """Test CommandDiscovery functionality."""

  def test_init_with_single_class(self):
    """Test initialization with single class target."""
    discovery = CommandDiscovery(MockClassSimple, completion=False)

    assert discovery.mode == TargetMode.CLASS
    assert discovery.primary_class == MockClassSimple  # Unified handling
    assert discovery.target_classes == [MockClassSimple]

  def test_init_with_class_list(self):
    """Test initialization with list of classes."""
    classes = [MockClass, MockClassSimple]
    discovery = CommandDiscovery(classes, completion=False)

    assert discovery.mode == TargetMode.CLASS
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


if __name__ == '__main__':
  pytest.main([__file__, '-v'])
