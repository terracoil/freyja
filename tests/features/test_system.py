"""Tests for the System class (shell completion only post-theme-collapse)."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from freyja import FreyjaCLI
from freyja.cli import SystemClassBuilder

System = SystemClassBuilder.build(completion=True)


class TestSystem:
  """Test the System class initialization."""

  def test_system_initialization(self):
    """Test System class can be initialized."""
    assert System() is not None


class TestSystemCompletion:
  """Test the System.Completion inner class."""

  def test_completion_initialization(self):
    """Test Completion class initializes correctly."""
    completion = System().Completion()
    assert completion.shell in ['bash', 'zsh', 'fish', 'powershell']
    assert completion._cli_instance is None
    assert completion._completion_handler is None

  def test_completion_initialization_with_cli(self):
    """Test Completion class initializes with FreyjaCLI instance."""
    mock_cli = MagicMock()
    completion = System.Completion(cli_instance=mock_cli)
    assert completion._cli_instance == mock_cli

  def test_completion_explicit_shell(self):
    """Test Completion class with explicitly specified shell."""
    completion = System().Completion(shell='bash')  # noqa: S604
    assert completion.shell == 'bash'

    completion = System().Completion(shell='zsh')  # noqa: S604
    assert completion.shell == 'zsh'

  def test_is_completion_request_false(self):
    """Test completion request detection returns False normally."""
    completion = System().Completion()
    with patch.object(sys, 'argv', ['script.py']):
      with patch('os.environ.get', return_value=None):
        assert completion.is_completion_request() is False

  def test_is_completion_request_true_argv(self):
    """Test completion request detection returns True with --_complete flag."""
    completion = System().Completion()
    with patch.object(sys, 'argv', ['script.py', '--_complete']):
      assert completion.is_completion_request() is True

  def test_is_completion_request_true_env(self):
    """Test completion request detection returns True with env var."""
    completion = System().Completion()
    with patch.object(sys, 'argv', ['script.py']):
      with patch('os.environ.get', return_value='1'):
        assert completion.is_completion_request() is True

  def test_install_completion_disabled(self):
    """Test install completion when completion is disabled."""
    mock_cli = MagicMock()
    mock_cli.enable_completion = False
    completion = System.Completion(cli_instance=mock_cli)
    assert completion.install() is False

  def test_show_completion_disabled(self):
    """Test show completion when completion is disabled."""
    mock_cli = MagicMock()
    mock_cli.enable_completion = False
    completion = System.Completion(cli_instance=mock_cli)
    completion.show('bash')

  def test_install_completion_no_cli_instance(self):
    """Test install completion without FreyjaCLI instance."""
    completion = System().Completion()
    assert completion.install() is False

  @patch('sys.exit')
  def test_handle_completion_no_handler(self, mock_exit):
    """Test handle completion without completion handler."""
    completion = System().Completion()
    with patch.object(completion, 'init_completion'):
      completion.handle_completion()
      mock_exit.assert_called_once_with(1)


class TestSystemCLIGeneration:
  """Test System class FreyjaCLI generation."""

  def test_system_cli_generation(self):
    """Test System class generates FreyjaCLI correctly."""
    cli = FreyjaCLI(System)
    cli.create_parser()
    assert cli.target_class == System

  def test_system_cli_has_completion_inner_class(self):
    """Test System FreyjaCLI recognizes the Completion inner class."""
    cli = FreyjaCLI(System)
    assert 'completion' in cli.commands
    assert cli.commands['completion']['type'] == 'group'

  def test_system_completion_methods(self):
    """Test System FreyjaCLI exposes Completion methods as hierarchical commands."""
    cli = FreyjaCLI(System)
    completion_group = cli.commands['completion']
    for command in ('install', 'show'):
      assert command in completion_group['cmd_tree']
      assert completion_group['cmd_tree'][command]['type'] == 'command'


class TestSystemIntegration:
  """Integration tests for System class with FreyjaCLI."""

  def test_system_help_generation(self):
    """Test System FreyjaCLI generates help correctly."""
    cli = FreyjaCLI(System, title='System Test FreyjaCLI')
    help_text = cli.create_parser().format_help()

    assert 'System Test FreyjaCLI' in help_text
    assert 'completion' in help_text

  def test_system_command_group_help(self):
    """Test System FreyjaCLI command group help generation."""
    cli = FreyjaCLI(System)
    parser = cli.create_parser()

    with pytest.raises(SystemExit):
      parser.parse_args(['completion', '--help'])


if __name__ == '__main__':
  pytest.main([__file__])
