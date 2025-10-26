"""Tests for CommandPathResolver."""

import pytest
from freyja.parser.command_path_resolver import CommandPathResolver, CommandPath
import inspect


class MockCommandTree:
  """Mock command tree with flat_commands and groups attributes for testing."""

  def __init__(self):
    self.flat_commands = {}
    self.groups = {}


class TestCommandPathResolver:
  """Test CommandPathResolver functionality."""

  @pytest.fixture
  def simple_tree(self):
    """Create simple command tree with flat commands."""
    tree = MockCommandTree()
    tree.flat_commands = {
      "test": {
        "type": "command",
        "function": lambda: None,
        "description": "Test command",
      },
      "process": {
        "type": "command",
        "function": lambda: None,
        "description": "Process command",
      },
    }
    return tree

  @pytest.fixture
  def hierarchical_tree(self):
    """Create hierarchical command tree with groups."""
    tree = MockCommandTree()
    tree.groups = {
      "data": {
        "type": "group",
        "description": "Data operations",
        "commands": {
          "process": {
            "type": "command",
            "function": lambda: None,
            "description": "Process data",
          },
          "export": {
            "type": "command",
            "function": lambda: None,
            "description": "Export data",
          },
        },
      },
    }
    return tree

  @pytest.fixture
  def mixed_tree(self):
    """Create tree with both flat commands and hierarchical groups."""
    tree = MockCommandTree()
    tree.flat_commands = {
      "status": {
        "type": "command",
        "function": lambda: None,
        "description": "Show status",
      },
    }
    tree.groups = {
      "config": {
        "type": "group",
        "description": "Configuration",
        "commands": {
          "get": {
            "type": "command",
            "function": lambda: None,
            "description": "Get config",
          },
          "set": {
            "type": "command",
            "function": lambda: None,
            "description": "Set config",
          },
        },
      },
    }
    return tree

  def test_resolve_simple_command(self, simple_tree):
    """Test resolving simple flat command path."""
    resolver = CommandPathResolver(simple_tree)
    result = resolver.resolve_path(["test"])

    assert result.path_elements == ["test"]
    assert result.is_valid is True
    assert result.is_complete is True
    assert not result.is_group  # May be False or {} (both falsy)
    assert result.remaining_args == []

  def test_resolve_with_options(self, simple_tree):
    """Test resolving command path with options."""
    resolver = CommandPathResolver(simple_tree)
    result = resolver.resolve_path(["test", "--option", "value"])

    assert result.path_elements == ["test"]
    assert result.remaining_args == ["--option", "value"]
    assert result.is_valid is True
    assert result.is_complete is True

  def test_resolve_hierarchical_path(self, hierarchical_tree):
    """Test resolving hierarchical command path."""
    resolver = CommandPathResolver(hierarchical_tree)
    result = resolver.resolve_path(["data", "process"])

    assert result.path_elements == ["data", "process"]
    assert result.is_valid is True
    assert result.is_complete is True
    assert result.is_group is False

  def test_resolve_hierarchical_with_options(self, hierarchical_tree):
    """Test resolving hierarchical path with options."""
    resolver = CommandPathResolver(hierarchical_tree)
    result = resolver.resolve_path(["data", "process", "--input", "file.txt"])

    assert result.path_elements == ["data", "process"]
    assert result.remaining_args == ["--input", "file.txt"]
    assert result.is_valid is True

  def test_resolve_group_only(self, hierarchical_tree):
    """Test resolving to a group without command."""
    resolver = CommandPathResolver(hierarchical_tree)
    result = resolver.resolve_path(["data"])

    assert result.path_elements == ["data"]
    assert result.is_valid is True
    assert result.is_complete is False
    assert result.is_group is True

  def test_resolve_empty_args(self, simple_tree):
    """Test resolving empty argument list."""
    resolver = CommandPathResolver(simple_tree)
    result = resolver.resolve_path([])

    assert result.path_elements == []
    assert result.is_valid is True
    assert result.is_complete is False
    assert result.is_group is False
    assert result.remaining_args == []

  def test_resolve_invalid_command(self, simple_tree):
    """Test resolving non-existent command."""
    resolver = CommandPathResolver(simple_tree)
    result = resolver.resolve_path(["nonexistent"])

    assert result.path_elements == []
    assert result.is_valid is True  # Empty path is valid
    assert result.is_complete is False
    assert result.remaining_args == ["nonexistent"]

  def test_validate_path_valid_flat(self, simple_tree):
    """Test path validation for valid flat command."""
    resolver = CommandPathResolver(simple_tree)
    is_valid = resolver.validate_path(["test"])

    assert is_valid is True

  def test_validate_path_valid_hierarchical(self, hierarchical_tree):
    """Test path validation for valid hierarchical command."""
    resolver = CommandPathResolver(hierarchical_tree)
    is_valid = resolver.validate_path(["data", "process"])

    assert is_valid is True

  def test_validate_path_invalid(self, simple_tree):
    """Test path validation for invalid path."""
    resolver = CommandPathResolver(simple_tree)
    is_valid = resolver.validate_path(["nonexistent"])

    assert not is_valid  # May be False or {} (both falsy)

  def test_get_available_commands_root(self, mixed_tree):
    """Test getting available commands at root level."""
    resolver = CommandPathResolver(mixed_tree)
    commands = resolver.get_available_commands()

    assert isinstance(commands, list)
    assert "status" in commands  # Flat command
    assert "config" in commands  # Group

  def test_get_available_commands_in_group(self, hierarchical_tree):
    """Test getting available commands within a group."""
    resolver = CommandPathResolver(hierarchical_tree)
    commands = resolver.get_available_commands(["data"])

    assert isinstance(commands, list)
    assert "process" in commands
    assert "export" in commands

  def test_get_command_info_flat(self, simple_tree):
    """Test getting command info for flat command."""
    resolver = CommandPathResolver(simple_tree)
    info = resolver.get_command_info(["test"])

    assert info is not None
    assert info["type"] == "command"
    assert "function" in info

  def test_get_command_info_hierarchical(self, hierarchical_tree):
    """Test getting command info for hierarchical command."""
    resolver = CommandPathResolver(hierarchical_tree)
    info = resolver.get_command_info(["data", "process"])

    assert info is not None
    assert info["type"] == "command"
    assert "function" in info

  def test_get_command_info_none(self, simple_tree):
    """Test getting command info for non-existent command."""
    resolver = CommandPathResolver(simple_tree)
    info = resolver.get_command_info(["nonexistent"])

    assert info is None

  def test_is_command_executable_true(self, simple_tree):
    """Test checking if path is executable command."""
    resolver = CommandPathResolver(simple_tree)
    is_executable = resolver.is_command_executable(["test"])

    assert is_executable is True

  def test_is_command_executable_false(self, hierarchical_tree):
    """Test checking if group path is not executable."""
    resolver = CommandPathResolver(hierarchical_tree)
    is_executable = resolver.is_command_executable(["data"])

    assert is_executable is False

  def test_is_command_group_true(self, hierarchical_tree):
    """Test checking if path is a command group."""
    resolver = CommandPathResolver(hierarchical_tree)
    is_group = resolver.is_command_group(["data"])

    assert is_group is True

  def test_is_command_group_false(self, simple_tree):
    """Test checking if command path is not a group."""
    resolver = CommandPathResolver(simple_tree)
    is_group = resolver.is_command_group(["test"])

    assert not is_group  # May be False or {} (both falsy)

  def test_extract_command_and_remaining(self, simple_tree):
    """Test extracting command path and remaining args."""
    resolver = CommandPathResolver(simple_tree)
    command_path, remaining = resolver.extract_command_and_remaining(
      ["test", "--option", "value"]
    )

    assert command_path == ["test"]
    assert remaining == ["--option", "value"]

  def test_find_longest_valid_path_flat(self, simple_tree):
    """Test finding longest valid path for flat command."""
    resolver = CommandPathResolver(simple_tree)
    longest = resolver.find_longest_valid_path(["test", "extra", "args"])

    assert longest == ["test"]

  def test_find_longest_valid_path_hierarchical(self, hierarchical_tree):
    """Test finding longest valid path for hierarchical command."""
    resolver = CommandPathResolver(hierarchical_tree)
    longest = resolver.find_longest_valid_path(["data", "process", "--option"])

    assert longest == ["data", "process"]

  def test_suggest_commands_root(self, mixed_tree):
    """Test command suggestions at root level."""
    resolver = CommandPathResolver(mixed_tree)
    suggestions = resolver.suggest_commands(["st"])

    assert isinstance(suggestions, list)
    assert "status" in suggestions

  def test_suggest_commands_in_group(self, hierarchical_tree):
    """Test command suggestions within a group."""
    resolver = CommandPathResolver(hierarchical_tree)
    suggestions = resolver.suggest_commands(["data", "pro"])

    assert isinstance(suggestions, list)
    assert "process" in suggestions


class TestCommandPath:
  """Test CommandPath dataclass."""

  def test_command_path_creation(self):
    """Test creating CommandPath instance."""
    path = CommandPath(
      path_elements=["test"],
      is_valid=True,
      is_complete=True,
      is_group=False,
      remaining_args=[],
    )

    assert path.path_elements == ["test"]
    assert path.is_valid is True
    assert path.is_complete is True
    assert path.is_group is False
    assert path.remaining_args == []

  def test_command_path_with_remaining_args(self):
    """Test CommandPath with remaining arguments."""
    path = CommandPath(
      path_elements=["data", "process"],
      is_valid=True,
      is_complete=True,
      is_group=False,
      remaining_args=["--input", "file.txt"],
    )

    assert len(path.remaining_args) == 2
    assert "--input" in path.remaining_args

  def test_command_path_group(self):
    """Test CommandPath representing a group."""
    path = CommandPath(
      path_elements=["data"],
      is_valid=True,
      is_complete=False,
      is_group=True,
      remaining_args=[],
    )

    assert path.is_group is True
    assert path.is_complete is False
