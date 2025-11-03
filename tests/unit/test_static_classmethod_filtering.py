"""Test filtering of @staticmethod and @classmethod methods from CLI commands."""

import pytest
from freyja.command import CommandDiscovery


class TestStaticClassmethodFiltering:
  """Test that @staticmethod and @classmethod methods are excluded from CLI commands."""

  def test_static_and_classmethod_filtering(self):
    """Test that static methods and class methods are not included as CLI commands."""

    class TestClass:
      """Test class with various method types."""

      def __init__(self, config: str = "default.json"):
        """Initialize test class."""
        self.config = config

      def instance_method(self, param: str) -> None:
        """This should become a CLI command."""
        pass

      @staticmethod
      def static_method(param: str) -> None:
        """This should NOT become a CLI command."""
        pass

      @classmethod
      def class_method(cls, param: str) -> None:
        """This should NOT become a CLI command."""
        pass

      def _private_method(self, param: str) -> None:
        """This should NOT become a CLI command."""
        pass

    # Disable system commands for cleaner testing
    discovery = CommandDiscovery(TestClass, completion=False)
    all_commands = discovery.cmd_tree.get_all_commands()
    command_names = [cmd.name for cmd in all_commands]

    # Should only have the instance method
    assert 'instance-method' in command_names, "Instance methods should be included as CLI commands"
    assert 'static-method' not in command_names, "@staticmethod methods should be excluded from CLI commands"
    assert 'class-method' not in command_names, "@classmethod methods should be excluded from CLI commands"
    assert 'private-method' not in command_names, "Private methods should be excluded from CLI commands"

  def test_custom_method_filter_overrides_default(self):
    """Test that custom method filter can override the default behavior."""

    class TestClass:
      def __init__(self):
        pass

      def instance_method(self, param: str) -> None:
        """Instance method."""
        pass

      @staticmethod
      def static_method(param: str) -> None:
        """Static method."""
        pass

    # Custom filter that allows everything callable (for testing override)
    def allow_all_filter(target_class, name, obj):
      return callable(obj) and not name.startswith('_') and hasattr(obj, '__qualname__')

    discovery = CommandDiscovery(TestClass, method_filter=allow_all_filter, completion=False)
    all_commands = discovery.cmd_tree.get_all_commands()
    command_names = [cmd.name for cmd in all_commands]

    # With custom filter, both methods should be included
    assert 'instance-method' in command_names
    assert 'static-method' in command_names  # Custom filter allows static methods

  def test_edge_case_method_types(self):
    """Test edge cases with different method types."""

    class TestClass:
      def __init__(self):
        pass

      def regular_method(self, param: str) -> None:
        """Regular instance method."""
        pass

      @property
      def some_property(self) -> str:
        """Property should not be a command."""
        return "value"

    discovery = CommandDiscovery(TestClass, completion=False)
    all_commands = discovery.cmd_tree.get_all_commands()
    command_names = [cmd.name for cmd in all_commands]

    # Should only have the regular method
    assert 'regular-method' in command_names
    assert 'some-property' not in command_names  # Properties should be excluded

  def test_inherited_static_classmethod_filtering(self):
    """Test that inherited static/class methods are also filtered correctly."""

    class BaseClass:
      @staticmethod
      def base_static_method() -> None:
        """Inherited static method."""
        pass

      @classmethod
      def base_class_method(cls) -> None:
        """Inherited class method."""
        pass

      def base_instance_method(self) -> None:
        """Inherited instance method."""
        pass

    class DerivedClass(BaseClass):
      def __init__(self):
        pass

      def derived_instance_method(self) -> None:
        """Derived instance method."""
        pass

    discovery = CommandDiscovery(DerivedClass, completion=False)
    all_commands = discovery.cmd_tree.get_all_commands()
    command_names = [cmd.name for cmd in all_commands]

    # Should only have instance methods from both base and derived classes
    assert 'derived-instance-method' in command_names
    assert 'base-instance-method' in command_names
    assert 'base-static-method' not in command_names
    assert 'base-class-method' not in command_names


if __name__ == '__main__':
  pytest.main([__file__, '-v'])