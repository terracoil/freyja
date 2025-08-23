"""Tests for shell completion functionality."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from auto_cli.cli import CLI
from auto_cli.completion.base import CompletionContext, CompletionHandler
from auto_cli.completion.bash import BashCompletionHandler
from auto_cli.completion import get_completion_handler


# Test module for completion
def test_function(name: str = "test", count: int = 1):
    """Test function for completion.

    :param name: Name parameter
    :param count: Count parameter
    """
    print(f"Hello {name} x{count}")


def nested__command(value: str = "default"):
    """Nested command for completion testing.

    :param value: Value parameter
    """
    return f"Nested: {value}"


class TestCompletionHandler:
    """Test completion handler functionality."""

    def test_get_completion_handler(self):
        """Test completion handler factory function."""
        # Create test CLI
        cli = CLI(sys.modules[__name__], "Test CLI")

        # Test bash handler
        handler = get_completion_handler(cli, 'bash')
        assert isinstance(handler, BashCompletionHandler)

        # Test unknown shell defaults to bash
        handler = get_completion_handler(cli, 'unknown')
        assert isinstance(handler, BashCompletionHandler)

    def test_bash_completion_handler(self):
        """Test bash completion handler."""
        cli = CLI(sys.modules[__name__], "Test CLI")
        handler = BashCompletionHandler(cli)

        # Test script generation
        script = handler.generate_script("test_cli")
        assert "test_cli" in script
        assert "_test_cli_completion" in script
        assert "complete -F" in script

    def test_completion_context(self):
        """Test completion context creation."""
        cli = CLI(sys.modules[__name__], "Test CLI")
        parser = cli.create_parser(no_color=True)

        context = CompletionContext(
            words=["prog", "test-function", "--name"],
            current_word="",
            cursor_position=0,
            subcommand_path=["test-function"],
            parser=parser,
            cli=cli
        )

        assert context.words == ["prog", "test-function", "--name"]
        assert context.subcommand_path == ["test-function"]
        assert context.cli == cli

    def test_get_available_commands(self):
        """Test getting available commands from parser."""
        cli = CLI(sys.modules[__name__], "Test CLI")
        handler = BashCompletionHandler(cli)
        parser = cli.create_parser(no_color=True)

        commands = handler.get_available_commands(parser)
        assert "test-function" in commands
        assert "nested" in commands

    def test_get_available_options(self):
        """Test getting available options from parser."""
        cli = CLI(sys.modules[__name__], "Test CLI")
        handler = BashCompletionHandler(cli)
        parser = cli.create_parser(no_color=True)

        # Navigate to test-function subcommand
        subparser = handler.get_subcommand_parser(parser, ["test-function"])
        assert subparser is not None

        options = handler.get_available_options(subparser)
        assert "--name" in options
        assert "--count" in options

    def test_complete_partial_word(self):
        """Test partial word completion."""
        cli = CLI(sys.modules[__name__], "Test CLI")
        handler = BashCompletionHandler(cli)

        candidates = ["test-function", "test-command", "other-command"]

        # Test prefix matching
        result = handler.complete_partial_word(candidates, "test")
        assert result == ["test-function", "test-command"]

        # Test empty partial returns all
        result = handler.complete_partial_word(candidates, "")
        assert result == candidates

        # Test no matches
        result = handler.complete_partial_word(candidates, "xyz")
        assert result == []


class TestCompletionIntegration:
    """Test completion integration with CLI."""

    def test_cli_with_completion_enabled(self):
        """Test CLI with completion enabled."""
        cli = CLI(sys.modules[__name__], "Test CLI", enable_completion=True)
        assert cli.enable_completion is True

        # Test parser includes completion arguments
        parser = cli.create_parser()
        help_text = parser.format_help()
        assert "--install-completion" in help_text
        assert "--show-completion" in help_text

    def test_cli_with_completion_disabled(self):
        """Test CLI with completion disabled."""
        cli = CLI(sys.modules[__name__], "Test CLI", enable_completion=False)
        assert cli.enable_completion is False

        # Test parser doesn't include completion arguments
        parser = cli.create_parser()
        help_text = parser.format_help()
        assert "--install-completion" not in help_text
        assert "--show-completion" not in help_text

    @patch.dict(os.environ, {"_AUTO_CLI_COMPLETE": "bash"})
    def test_completion_request_detection(self):
        """Test completion request detection."""
        cli = CLI(sys.modules[__name__], "Test CLI", enable_completion=True)
        assert cli._CLI__is_completion_request() is True

    def test_show_completion_script(self):
        """Test showing completion script."""
        cli = CLI(sys.modules[__name__], "Test CLI", enable_completion=True)

        with patch('sys.argv', ['test_cli']):
            exit_code = cli._CLI__show_completion_script('bash')
            assert exit_code == 0

    def test_completion_disabled_error(self):
        """Test error when completion is disabled."""
        cli = CLI(sys.modules[__name__], "Test CLI", enable_completion=False)

        exit_code = cli._CLI__show_completion_script('bash')
        assert exit_code == 1


class TestFileCompletion:
    """Test file path completion."""

    def test_file_path_completion(self):
        """Test file path completion functionality."""
        cli = CLI(sys.modules[__name__], "Test CLI")
        handler = BashCompletionHandler(cli)

        # Create temporary directory with test files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test files
            (tmpdir_path / "test1.txt").touch()
            (tmpdir_path / "test2.py").touch()
            (tmpdir_path / "subdir").mkdir()

            # Change to temp directory for testing
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Test completing empty partial
                completions = handler._complete_file_path("")
                assert any("test1.txt" in c for c in completions)
                assert any("test2.py" in c for c in completions)
                # Directory should either end with separator or be "subdir"
                assert any("subdir" in c for c in completions)

                # Test completing partial filename
                completions = handler._complete_file_path("test")
                assert any("test1.txt" in c for c in completions)
                assert any("test2.py" in c for c in completions)

            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    pytest.main([__file__])
