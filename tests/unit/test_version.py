"""Comprehensive tests for version utilities to achieve 80%+ coverage."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from freyja.utils.version import format_title_with_version, get_freyja_version


class TestGetFreyjaVersion:
  """Test suite for get_freyja_version function."""

  @patch("importlib.metadata.version")
  def test_get_version_from_metadata(self, mock_version):
    """Test getting version from installed package metadata."""
    mock_version.return_value = "1.2.3"
    result = get_freyja_version()
    assert result == "v1.2.3"
    mock_version.assert_called_once_with("freyja")

  @patch("importlib.metadata.version")
  def test_get_version_metadata_not_found_fallback_to_pyproject(self, mock_version):
    """Test fallback to pyproject.toml when package not installed."""
    import importlib.metadata

    mock_version.side_effect = importlib.metadata.PackageNotFoundError("freyja")

    # Mock the pyproject.toml path and contents
    with patch("pathlib.Path.exists") as mock_exists:
      mock_exists.return_value = True

      with patch("builtins.open", create=True) as mock_open:
        # Create mock file content for pyproject.toml
        mock_file_content = b"""
[tool.poetry]
version = "2.0.0"
"""
        mock_open.return_value.__enter__.return_value.read.return_value = mock_file_content

        with patch("tomllib.load") as mock_toml_load:
          mock_toml_load.return_value = {"tool": {"poetry": {"version": "2.0.0"}}}

          result = get_freyja_version()
          assert result == "v2.0.0"

  @patch("importlib.metadata.version")
  def test_get_version_both_methods_fail(self, mock_version):
    """Test fallback to 'unknown' when both methods fail."""
    import importlib.metadata

    mock_version.side_effect = importlib.metadata.PackageNotFoundError("freyja")

    with patch("pathlib.Path.exists") as mock_exists:
      mock_exists.return_value = False  # pyproject.toml doesn't exist

      result = get_freyja_version()
      assert result == "v0.0.0"  # Returns v0.0.0 when version is None/unknown

  @patch("importlib.metadata.version")
  def test_get_version_pyproject_read_error(self, mock_version):
    """Test fallback when pyproject.toml read fails."""
    import importlib.metadata

    mock_version.side_effect = importlib.metadata.PackageNotFoundError("freyja")

    with patch("pathlib.Path.exists") as mock_exists:
      mock_exists.return_value = True

      with patch("builtins.open", side_effect=IOError("Cannot read file")):
        result = get_freyja_version()
        assert result == "vunknown"

  @patch("importlib.metadata.version")
  def test_get_version_pyproject_invalid_structure(self, mock_version):
    """Test fallback when pyproject.toml has unexpected structure."""
    import importlib.metadata

    mock_version.side_effect = importlib.metadata.PackageNotFoundError("freyja")

    with patch("pathlib.Path.exists") as mock_exists:
      mock_exists.return_value = True

      with patch("builtins.open", create=True) as mock_open:
        mock_file_content = b"""
[project]
name = "freyja"
"""
        mock_open.return_value.__enter__.return_value.read.return_value = mock_file_content

        with patch("tomllib.load") as mock_toml_load:
          # Missing the expected tool.poetry.version structure
          mock_toml_load.return_value = {"project": {"name": "freyja"}}

          result = get_freyja_version()
          assert result == "v0.0.0"  # Returns default when version missing

  @patch("importlib.metadata.version")
  def test_get_version_empty_version_string(self, mock_version):
    """Test handling of empty version string."""
    mock_version.return_value = ""
    result = get_freyja_version()
    assert result == "v0.0.0"

  @patch("importlib.metadata.version")
  def test_get_version_none_version(self, mock_version):
    """Test handling of None version."""
    mock_version.return_value = None
    result = get_freyja_version()
    assert result == "v0.0.0"

  @patch("importlib.metadata.version")
  def test_get_version_with_alpha_beta_tags(self, mock_version):
    """Test version with alpha/beta/rc tags."""
    mock_version.return_value = "1.0.0-alpha.1"
    result = get_freyja_version()
    assert result == "v1.0.0-alpha.1"

  @patch("importlib.metadata.version")
  def test_get_version_with_long_version_string(self, mock_version):
    """Test version with long/complex version string."""
    mock_version.return_value = "2024.1.0+build.1234.git.abcdef"
    result = get_freyja_version()
    assert result == "v2024.1.0+build.1234.git.abcdef"


class TestFormatTitleWithVersion:
  """Test suite for format_title_with_version function."""

  @patch("freyja.utils.version.get_freyja_version")
  def test_format_title_basic(self, mock_get_version):
    """Test basic title formatting with version."""
    mock_get_version.return_value = "v1.0.0"
    result = format_title_with_version("My CLI App")
    assert result == "My CLI App (freyja v1.0.0)"
    mock_get_version.assert_called_once()

  @patch("freyja.utils.version.get_freyja_version")
  def test_format_title_empty_string(self, mock_get_version):
    """Test formatting with empty title."""
    mock_get_version.return_value = "v1.0.0"
    result = format_title_with_version("")
    assert result == " (freyja v1.0.0)"

  @patch("freyja.utils.version.get_freyja_version")
  def test_format_title_with_special_chars(self, mock_get_version):
    """Test formatting with special characters in title."""
    mock_get_version.return_value = "v2.0.0"
    result = format_title_with_version("My-CLI_App™")
    assert result == "My-CLI_App™ (freyja v2.0.0)"

  @patch("freyja.utils.version.get_freyja_version")
  def test_format_title_with_unicode(self, mock_get_version):
    """Test formatting with Unicode characters."""
    mock_get_version.return_value = "v1.5.0"
    result = format_title_with_version("CLI 应用程序 🚀")
    assert result == "CLI 应用程序 🚀 (freyja v1.5.0)"

  @patch("freyja.utils.version.get_freyja_version")
  def test_format_title_very_long(self, mock_get_version):
    """Test formatting with very long title."""
    mock_get_version.return_value = "v1.0.0"
    long_title = "A" * 100
    result = format_title_with_version(long_title)
    assert result == f"{long_title} (freyja v1.0.0)"

  @patch("freyja.utils.version.get_freyja_version")
  def test_format_title_with_unknown_version(self, mock_get_version):
    """Test formatting when version is unknown."""
    mock_get_version.return_value = "vunknown"
    result = format_title_with_version("My App")
    assert result == "My App (freyja vunknown)"

  @patch("freyja.utils.version.get_freyja_version")
  def test_format_title_multiple_calls(self, mock_get_version):
    """Test multiple calls to format_title_with_version."""
    mock_get_version.return_value = "v1.0.0"

    result1 = format_title_with_version("App1")
    result2 = format_title_with_version("App2")

    assert result1 == "App1 (freyja v1.0.0)"
    assert result2 == "App2 (freyja v1.0.0)"
    assert mock_get_version.call_count == 2


class TestVersionIntegration:
  """Integration tests for version utilities."""

  def test_real_version_format(self):
    """Test that real version follows expected format."""
    version = get_freyja_version()
    assert version.startswith("v")
    # Should have at least v + one character
    assert len(version) >= 2

  def test_title_formatting_with_real_version(self):
    """Test title formatting with actual version."""
    result = format_title_with_version("Test App")
    assert "Test App" in result
    assert "(freyja v" in result
    assert ")" in result

  @patch("importlib.metadata.version")
  def test_exception_handling_in_get_version(self, mock_version):
    """Test robust exception handling in get_freyja_version."""
    import importlib.metadata
    # Test various exceptions - should fall back to pyproject
    mock_version.side_effect = importlib.metadata.PackageNotFoundError("freyja")
    with patch("pathlib.Path.exists", return_value=False):
      result = get_freyja_version()
      assert result == "v0.0.0"  # Returns v0.0.0 when version is None/unknown

  @patch("pathlib.Path.exists")
  @patch("importlib.metadata.version")
  def test_pyproject_path_resolution(self, mock_version, mock_exists):
    """Test correct path resolution for pyproject.toml."""
    import importlib.metadata

    mock_version.side_effect = importlib.metadata.PackageNotFoundError("freyja")
    mock_exists.return_value = True

    # The path should be relative to the version.py file
    with patch("builtins.open", create=True) as mock_open:
      mock_file_content = b"""
[tool.poetry]
version = "3.0.0"
"""
      mock_open.return_value.__enter__.return_value.read.return_value = mock_file_content

      with patch("tomllib.load") as mock_toml_load:
        mock_toml_load.return_value = {"tool": {"poetry": {"version": "3.0.0"}}}

        result = get_freyja_version()

        # Verify the path construction
        mock_open.assert_called_once()
        call_args = mock_open.call_args[0][0]
        # Should be an absolute path to pyproject.toml
        assert isinstance(call_args, Path)
        assert call_args.name == "pyproject.toml"

  def test_version_is_string(self):
    """Test that get_freyja_version always returns a string."""
    version = get_freyja_version()
    assert isinstance(version, str)

  def test_formatted_title_is_string(self):
    """Test that format_title_with_version always returns a string."""
    result = format_title_with_version("Test")
    assert isinstance(result, str)