"""Shared test utilities for Freyja test suite."""
import io
import sys
from typing import Any
from contextlib import contextmanager
from freyja.shared.command_tree import CommandTree


class CLITestHelper:
  """Helper for testing CLI functionality without subprocess."""

  @staticmethod
  @contextmanager
  def capture_cli_output():
    """
    Capture stdout/stderr from CLI execution.

    :return: Tuple of (stdout, stderr) StringIO objects
    """
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
      sys.stdout = stdout_capture
      sys.stderr = stderr_capture
      yield stdout_capture, stderr_capture
    finally:
      sys.stdout = old_stdout
      sys.stderr = old_stderr

  @staticmethod
  def create_test_class(methods_config: dict[str, dict[str, Any]]) -> type:
    """
    Dynamically create test classes with specified methods.

    :param methods_config: Dict mapping method names to their config
    :return: Dynamically created class

    Example:
      config = {
        'process': {
          'params': [('input_file', str), ('output', str, './out')],
          'docstring': 'Process input file'
        }
      }
    """
    def create_method(method_name: str, params: list, doc: str):
      """Create a method with specified signature."""
      # Build parameter list
      param_names = [p[0] for p in params]

      def method(self, **kwargs):
        """Dynamically created method."""
        return f"{method_name} called with {kwargs}"

      method.__name__ = method_name
      method.__doc__ = doc

      # Add parameter annotations
      annotations = {'return': None}
      for param in params:
        param_name = param[0]
        param_type = param[1]
        annotations[param_name] = param_type

      method.__annotations__ = annotations

      return method

    # Create class dict
    class_dict = {}
    for method_name, config in methods_config.items():
      params = config.get('params', [])
      docstring = config.get('docstring', '')
      class_dict[method_name] = create_method(method_name, params, docstring)

    # Create and return class
    return type('TestClass', (), class_dict)

  @staticmethod
  def assert_command_tree_structure(tree: CommandTree, expected_structure: dict[str, Any]) -> None:
    """
    Validate command tree structure matches expectations.

    :param tree: CommandTree instance to validate
    :param expected_structure: Expected structure as dict
    """
    # Verify commands exist
    expected_commands = expected_structure.get('commands', [])
    for cmd in expected_commands:
      assert cmd in tree.commands, f"Expected command '{cmd}' not found in tree"

    # Verify groups exist
    expected_groups = expected_structure.get('groups', [])
    for group in expected_groups:
      assert group in tree.groups, f"Expected group '{group}' not found in tree"

    # Verify command count
    if 'command_count' in expected_structure:
      actual_count = len(tree.commands)
      expected_count = expected_structure['command_count']
      assert actual_count == expected_count, f"Expected {expected_count} commands, got {actual_count}"


class MockFileSystem:
  """Mock file operations for testing without disk I/O."""

  def __init__(self):
    """Initialize mock filesystem."""
    self.files: dict[str, str] = {}
    self.directories: set[str] = set()

  def create_temp_structure(self, structure_dict: dict[str, Any]) -> None:
    """
    Create temporary file structure for testing.

    :param structure_dict: Dict representing file structure

    Example:
      {
        'dir1': {
          'file1.txt': 'content',
          'subdir': {
            'file2.txt': 'more content'
          }
        }
      }
    """
    def process_structure(base_path: str, struct: dict):
      """Recursively process structure dict."""
      for name, content in struct.items():
        full_path = f"{base_path}/{name}" if base_path else name

        if isinstance(content, dict):
          # It's a directory
          self.directories.add(full_path)
          process_structure(full_path, content)
        else:
          # It's a file
          self.files[full_path] = str(content)

    process_structure('', structure_dict)

  def read_file(self, path: str) -> str:
    """
    Read file content from mock filesystem.

    :param path: Path to file
    :return: File content
    """
    if path not in self.files:
      raise FileNotFoundError(f"File not found: {path}")
    return self.files[path]

  def file_exists(self, path: str) -> bool:
    """
    Check if file exists in mock filesystem.

    :param path: Path to check
    :return: True if file exists
    """
    return path in self.files

  def dir_exists(self, path: str) -> bool:
    """
    Check if directory exists in mock filesystem.

    :param path: Path to check
    :return: True if directory exists
    """
    return path in self.directories
