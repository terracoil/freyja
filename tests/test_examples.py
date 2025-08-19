"""Tests for examples.py functionality."""
import subprocess
import sys
from pathlib import Path


class TestExamples:
    """Test cases for the examples.py file."""

    def test_examples_help(self):
        """Test that examples.py shows help without errors."""
        examples_path = Path(__file__).parent.parent / "examples.py"
        result = subprocess.run(
            [sys.executable, str(examples_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout or "usage:" in result.stdout

    def test_examples_foo_command(self):
        """Test the foo command in examples.py."""
        examples_path = Path(__file__).parent.parent / "examples.py"
        result = subprocess.run(
            [sys.executable, str(examples_path), "foo"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        assert "FOO!" in result.stdout

    def test_examples_train_command_help(self):
        """Test the train command help in examples.py."""
        examples_path = Path(__file__).parent.parent / "examples.py"
        result = subprocess.run(
            [sys.executable, str(examples_path), "train", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        assert "data-dir" in result.stdout
        assert "initial-learning-rate" in result.stdout

    def test_examples_count_animals_command_help(self):
        """Test the count_animals command help in examples.py."""
        examples_path = Path(__file__).parent.parent / "examples.py"
        result = subprocess.run(
            [sys.executable, str(examples_path), "count-animals", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        assert "count" in result.stdout
        assert "animal" in result.stdout
