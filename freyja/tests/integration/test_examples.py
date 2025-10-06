"""Tests for class-based example functionality."""

import subprocess
from pathlib import Path


class TestClassExample:
    """Test cases for the cls_example file."""

    def test_class_example_help(self):
        """Test that cls_example shows help without errors."""
        examples_path = Path(__file__).parent.parent.parent.parent / "examples" / "cls_example"
        result = subprocess.run(
            [str(examples_path), "--help"], capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout
        assert "Enhanced data processing utility" in result.stdout

    def test_class_example_process_file(self):
        """Test the file-operations process-single command group in cls_example."""
        examples_path = Path(__file__).parent.parent.parent.parent / "examples" / "cls_example"
        result = subprocess.run(
            [str(examples_path), "file-operations", "process-single", "test.txt"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Processing file: test.txt" in result.stdout

    def test_class_example_config_command(self):
        """Test config-management set-default-mode command group in cls_example."""
        examples_path = Path(__file__).parent.parent.parent.parent / "examples" / "cls_example"
        result = subprocess.run(
            [str(examples_path), "config-management", "set-default-mode", "FAST"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Setting default processing mode to: fast" in result.stdout

    def test_class_example_config_help(self):
        """Test that config management cmd_tree are listed in main help."""
        examples_path = Path(__file__).parent.parent.parent.parent / "examples" / "cls_example"
        result = subprocess.run(
            [str(examples_path), "--help"], capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        assert "config-management" in result.stdout  # Command group should appear
        assert "set-default-mode" in result.stdout  # Command group command should appear
