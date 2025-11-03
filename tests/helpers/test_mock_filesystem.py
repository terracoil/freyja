"""Mock filesystem utilities for Freyja test suite."""

from typing import Any


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
        full_path = f'{base_path}/{name}' if base_path else name

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
      raise FileNotFoundError(f'File not found: {path}')
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