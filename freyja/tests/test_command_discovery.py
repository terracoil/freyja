"""Test suite for CommandDiscovery."""

import pytest
import types
import inspect
from freyja.command import CommandDiscovery
from freyja.cli import TargetMode


# Test fixtures - create a mock module
def mock_function(param: str, count: int = 5) -> None:
    """Mock function for testing."""
    pass


def _private_function() -> None:
    """Private function that should be ignored."""
    pass


def another_function(flag: bool = False) -> str:
    """Another mock function."""
    return "test"


class MockClass:
    """Mock class for testing command discovery."""
    
    def __init__(self, config: str = "default"):
        self.config = config
    
    def method_one(self, param: str) -> None:
        """First method for testing."""
        pass
    
    def method_two(self, count: int = 10, flag: bool = True) -> str:
        """Second method for testing."""
        return "result"
    
    def _private_method(self) -> None:
        """Private method that should be ignored."""
        pass


class MockClassWithInner:
    """Mock class with inner classes for hierarchical testing."""
    
    def __init__(self, base_config: str = "base"):
        self.base_config = base_config
    
    def direct_method(self, param: str) -> None:
        """Direct method on main class."""
        pass
    
    class InnerOperations:
        """Inner class for grouped operations."""
        
        def __init__(self, inner_config: str = "inner"):
            self.inner_config = inner_config
        
        def inner_method_one(self, data: str) -> None:
            """First inner method."""
            pass
        
        def inner_method_two(self, count: int = 3) -> str:
            """Second inner method."""
            return "inner_result"
    
    class DataProcessing:
        """Another inner class for data operations."""
        
        def __init__(self, processing_mode: str = "auto"):
            self.processing_mode = processing_mode
        
        def process_data(self, input_data: str, format_type: str = "json") -> None:
            """Process data method."""
            pass


class MockClassSimple:
    """Simple mock class without inner classes."""
    
    def __init__(self):
        pass
    
    def simple_method(self, value: int) -> None:
        """Simple method for testing."""
        pass


class TestCommandDiscovery:
    """Test CommandDiscovery functionality."""
    
    def test_init_with_module(self):
        """Test initialization with module target."""
        # Create a mock module
        mock_module = types.ModuleType('test_module')
        mock_module.mock_function = mock_function
        mock_module.another_function = another_function
        mock_module._private_function = _private_function
        
        discovery = CommandDiscovery(mock_module, completion=False)
        
        assert discovery.mode == TargetMode.MODULE
        assert discovery.target_module == mock_module
        assert discovery.primary_class is None
        assert discovery.target_classes is None
    
    def test_init_with_single_class(self):
        """Test initialization with single class target."""
        discovery = CommandDiscovery(MockClassSimple, completion=False)
        
        assert discovery.mode == TargetMode.CLASS
        assert discovery.primary_class == MockClassSimple  # Unified handling
        assert discovery.target_classes == [MockClassSimple]
        assert discovery.target_module is None
    
    def test_init_with_class_list(self):
        """Test initialization with list of classes."""
        classes = [MockClass, MockClassSimple]
        discovery = CommandDiscovery(classes, completion=False)
        
        assert discovery.mode == TargetMode.CLASS
        assert discovery.primary_class == MockClassSimple  # Last class in list
        assert discovery.target_classes == classes
        assert discovery.target_module is None
    
    def test_init_with_invalid_target(self):
        """Test initialization with invalid target raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            CommandDiscovery("invalid_target")
        
        assert "Target must be module, class, or list of classes" in str(exc_info.value)
    
    def test_discover_from_module(self):
        """Test discovering commands from a module."""
        # Create a mock module
        mock_module = types.ModuleType('test_module')
        mock_module.__name__ = 'test_module'
        
        # Create functions with the correct __module__ attribute
        def test_mock_function(param: str, count: int = 5) -> None:
            """Mock function for testing."""
            pass
        
        def test_another_function(flag: bool = False) -> str:
            """Another mock function."""
            return "test"
        
        def _test_private_function() -> None:
            """Private function that should be ignored."""
            pass
        
        # Set the __module__ attribute to match our mock module
        test_mock_function.__module__ = 'test_module'
        test_another_function.__module__ = 'test_module'
        _test_private_function.__module__ = 'test_module'
        
        # Add functions to the module
        mock_module.test_mock_function = test_mock_function
        mock_module.test_another_function = test_another_function
        mock_module._test_private_function = _test_private_function
        
        discovery = CommandDiscovery(mock_module)
        commands = discovery.discover_commands()
        
        # Should find public functions only
        command_names = [cmd.name for cmd in commands]
        assert 'test-mock-function' in command_names
        assert 'test-another-function' in command_names
        assert 'test-private-function' not in command_names  # Should be filtered out
        
        # Check command info structure
        mock_cmd = next(cmd for cmd in commands if cmd.name == 'test-mock-function')
        assert mock_cmd.original_name == 'test_mock_function'
        assert mock_cmd.function == test_mock_function
        assert isinstance(mock_cmd.signature, inspect.Signature)
        assert mock_cmd.docstring == "Mock function for testing."
        assert not mock_cmd.is_hierarchical
    
    def test_discover_from_simple_class(self):
        """Test discovering commands from a simple class without inner classes."""
        discovery = CommandDiscovery(MockClassSimple, completion=False)
        commands = discovery.discover_commands()
        
        # Should find public methods only
        command_names = [cmd.name for cmd in commands]
        assert 'simple-method' in command_names
        assert len(commands) == 1
        
        # Check command info
        cmd = commands[0]
        assert cmd.original_name == 'simple_method'
        assert not cmd.is_hierarchical
        assert cmd.parent_class is None
        assert cmd.inner_class is None
    
    def test_discover_from_class_with_inner_classes(self):
        """Test discovering commands from class with inner classes."""
        discovery = CommandDiscovery(MockClassWithInner, completion=False)
        commands = discovery.discover_commands()
        
        command_names = [cmd.name for cmd in commands]
        
        # Should have direct method
        assert 'direct-method' in command_names
        
        # Should have hierarchical methods from inner classes (now with just method names)
        assert 'inner-method-one' in command_names
        assert 'inner-method-two' in command_names
        assert 'process-data' in command_names
        
        # Check hierarchical command structure
        hierarchical_cmd = next(cmd for cmd in commands if cmd.name == 'inner-method-one')
        assert hierarchical_cmd.is_hierarchical
        assert hierarchical_cmd.parent_class == 'InnerOperations'
        assert hierarchical_cmd.command_path == 'inner-operations'
        assert hierarchical_cmd.inner_class == MockClassWithInner.InnerOperations
        assert hierarchical_cmd.group_name == 'inner-operations'  # New field
        assert hierarchical_cmd.method_name == 'inner-method-one'  # New field
        assert 'inner_class' in hierarchical_cmd.metadata
        
        # Check direct method
        direct_cmd = next(cmd for cmd in commands if cmd.name == 'direct-method')
        assert not direct_cmd.is_hierarchical
        assert direct_cmd.parent_class is None
    
    def test_discover_from_multi_class(self):
        """Test discovering commands from multiple classes."""
        classes = [MockClass, MockClassSimple]
        discovery = CommandDiscovery(classes, completion=False)
        commands = discovery.discover_commands()
        
        # Should have commands from both classes
        command_names = [cmd.name for cmd in commands]
        assert 'method-one' in command_names  # From MockClass
        assert 'method-two' in command_names  # From MockClass
        assert 'simple-method' in command_names  # From MockClassSimple
        
        # Check metadata for namespacing
        # First class (MockClass) should be namespaced
        method_one_cmd = next(cmd for cmd in commands if cmd.name == 'method-one' and cmd.metadata.get('source_class') == MockClass)
        assert method_one_cmd.metadata['is_namespaced'] == True
        assert method_one_cmd.metadata['class_namespace'] == 'mock-class'
        
        # Last class (MockClassSimple) should be in global namespace
        simple_cmd = next(cmd for cmd in commands if cmd.name == 'simple-method')
        assert simple_cmd.metadata['is_namespaced'] == False
        assert simple_cmd.metadata['class_namespace'] is None
    
    def test_custom_function_filter(self):
        """Test custom function filter."""
        mock_module = types.ModuleType('test_module')
        mock_module.__name__ = 'test_module'
        
        # Create test functions
        def mock_function_test(param: str) -> None:
            pass
        
        def another_function_test(param: str) -> None:
            pass
        
        # Set module attributes correctly
        mock_function_test.__module__ = 'test_module'
        another_function_test.__module__ = 'test_module'
        mock_module.mock_function_test = mock_function_test
        mock_module.another_function_test = another_function_test
        
        # Filter that only allows functions starting with 'mock'
        def custom_filter(name, obj):
            return name.startswith('mock') and callable(obj) and inspect.isfunction(obj)
        
        discovery = CommandDiscovery(mock_module, function_filter=custom_filter, completion=False)
        commands = discovery.discover_commands()
        
        # Should only find mock_function_test
        command_names = [cmd.name for cmd in commands]
        assert 'mock-function-test' in command_names
        assert 'another-function-test' not in command_names
        assert len(commands) == 1
    
    def test_custom_method_filter(self):
        """Test custom method filter."""
        # Filter that only allows methods starting with 'method'
        def custom_filter(target_class, name, obj):
            return name.startswith('method') and callable(obj)
        
        discovery = CommandDiscovery(MockClass, method_filter=custom_filter, completion=False)
        commands = discovery.discover_commands()
        
        # Should find method_one and method_two but not others
        command_names = [cmd.name for cmd in commands]
        assert 'method-one' in command_names
        assert 'method-two' in command_names
        assert len([cmd for cmd in commands if not cmd.is_hierarchical]) == 2
    
    def test_command_info_structure(self):
        """Test CommandInfo data structure completeness."""
        discovery = CommandDiscovery(MockClassSimple, completion=False)
        commands = discovery.discover_commands()
        
        cmd = commands[0]
        
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])