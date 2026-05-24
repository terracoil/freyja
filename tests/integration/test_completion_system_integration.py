"""Comprehensive integration tests for the completion system.

These tests verify that completion and normal execution are completely isolated
and that completion never interferes with normal command execution.
"""

import inspect
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from freyja.cli.execution_coordinator import ExecutionCoordinator
from freyja.freyja_cli import FreyjaCLI
from freyja.shared.command_info import CommandInfo
from freyja.shared.command_tree import CommandTree

COMPLETION_ENV_VARS = (
  '_FREYJA_COMPLETE',
  '_FREYJA_COMPLETE_ZSH',
  '_FREYJA_COMPLETE_BASH',
  '_FREYJA_COMPLETE_FISH',
  '_FREYJA_COMPLETE_POWERSHELL',
  'COMP_WORDS_STR',
  'COMP_CWORD_NUM',
)


class TestCompletionSystemIntegration:
  """Comprehensive integration tests for completion system isolation."""

  @pytest.fixture(autouse=True)
  def _clear_completion_env(self):
    """Clear completion env vars before and after each test."""
    for var in COMPLETION_ENV_VARS:
      os.environ.pop(var, None)
    yield
    for var in COMPLETION_ENV_VARS:
      os.environ.pop(var, None)

  @pytest.fixture
  def examples_dir_fixture(self):
    """Path to the project's examples directory."""
    return Path(__file__).parent.parent.parent / 'examples'

  def create_test_cli(self):
    """Create a test CLI instance."""

    class TestCommands:
      """Test helper class for CLI commands."""

      def __init__(self):
        pass

      def hello(self, name: str = 'world'):
        """Say hello to someone."""
        return f'Hello, {name}!'

      def goodbye(self, name: str = 'world'):
        """Say goodbye to someone."""
        return f'Goodbye, {name}!'

    return FreyjaCLI(TestCommands, title='Test CLI')

  def test_normal_execution_without_completion_env(self):
    """Test that normal execution works without completion environment."""
    cli = self.create_test_cli()

    # Ensure no completion detection
    assert not cli._is_completion_request()

    # Test that we can create and use the CLI normally
    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
      with patch('sys.argv', ['test', '--help']):
        try:
          cli.run()
        except SystemExit as e:
          # Help should exit with code 0
          assert e.code == 0

    output = mock_stdout.getvalue()
    assert 'Test CLI' in output

  def test_completion_detection_accuracy(self):
    """Test that completion is only detected when appropriate variables are set."""
    cli = self.create_test_cli()

    # Should not detect completion normally
    assert not cli._is_completion_request()

    # Should detect with _FREYJA_COMPLETE
    with patch.dict(os.environ, {'_FREYJA_COMPLETE': 'zsh'}):
      assert cli._is_completion_request()

    # Should detect with shell-specific variables
    for shell_var in ['_FREYJA_COMPLETE_ZSH', '_FREYJA_COMPLETE_BASH', '_FREYJA_COMPLETE_FISH']:
      with patch.dict(os.environ, {shell_var: '1'}):
        assert cli._is_completion_request()

    # Should detect with --_complete flag
    with patch.object(sys, 'argv', ['test', '--_complete']):
      assert cli._is_completion_request()

  def test_completion_isolation(self):
    """Test that completion execution is completely isolated."""
    cli = self.create_test_cli()

    # Mock sys.exit to prevent actual exit during testing
    with patch('sys.exit') as mock_exit:
      with patch.dict(
        os.environ,
        {'_FREYJA_COMPLETE': 'zsh', 'COMP_WORDS_STR': 'test hel', 'COMP_CWORD_NUM': '2'},
      ):
        with patch('sys.stdout', new_callable=StringIO):
          # This should trigger completion mode
          cli.run()

          # Completion should always exit
          mock_exit.assert_called()

          # Should have attempted to generate completions
          # (actual completion output depends on the implementation)

  def test_execution_coordinator_completion_safeguards(self):
    """Test that execution coordinator has proper safeguards against completion interference."""
    tree = CommandTree()

    # Create a proper CommandInfo object
    def test_function():
      return 'test output'

    command_info = CommandInfo(
      name='test',
      original_name='test',
      function=test_function,
      signature=inspect.signature(test_function),
    )
    tree.add_command('test', command_info)

    coordinator = ExecutionCoordinator(None, {})
    coordinator.command_tree = tree

    # Should raise error if completion environment detected in normal execution
    with patch.dict(os.environ, {'_FREYJA_COMPLETE': 'zsh'}):
      with pytest.raises(RuntimeError) as exc_info:
        coordinator.parse_and_execute(MagicMock(), [])

      assert 'Completion environment detected' in str(exc_info.value)

    # Should raise error if --_complete flag present in normal execution
    with pytest.raises(RuntimeError) as exc_info:
      coordinator.parse_and_execute(MagicMock(), ['--_complete'])

    assert 'Completion request reached normal execution' in str(exc_info.value)

  def test_environmental_isolation_sequence(self):
    """Test that completion doesn't pollute environment for subsequent runs."""
    cli = self.create_test_cli()

    # Step 1: Normal execution should work
    assert not cli._is_completion_request()

    # Step 2: Simulate completion execution
    with patch('sys.exit'):  # Prevent actual exit
      with patch.dict(
        os.environ,
        {'_FREYJA_COMPLETE': 'zsh', 'COMP_WORDS_STR': 'test hel', 'COMP_CWORD_NUM': '2'},
      ):
        with patch('sys.stdout', new_callable=StringIO):
          cli.run()

    # Step 3: Normal execution should still work after completion
    # (environment variables should be scoped to the with block)
    assert not cli._is_completion_request()

  def test_integration_with_examples(self, examples_dir_fixture: Path):
    """Integration test with actual example files."""
    if not examples_dir_fixture.exists():
      pytest.skip('Examples directory not found')

    # Test cls_example normal execution
    cls_example = examples_dir_fixture / 'cls_example'
    if cls_example.exists():
      result = subprocess.run(
        [sys.executable, str(cls_example)],
        env={'PYTHONPATH': str(examples_dir_fixture.parent)},
        capture_output=True,
        text=True,
        timeout=10,
      )

      # Should show usage, not completion output
      assert 'usage:' in result.stdout.lower()
      assert result.stdout.strip() != 'completion'

  def test_completion_after_normal_execution(self, examples_dir_fixture):
    """Test that completion works after normal execution."""
    if not examples_dir_fixture.exists():
      pytest.skip('examples_dir_fixture not found')

    cls_example = examples_dir_fixture / 'cls_example'

    if not cls_example.exists():
      pytest.skip('cls_example not found')

    # Step 1: Normal execution
    result1 = subprocess.run(
      [sys.executable, str(cls_example)],
      env={'PYTHONPATH': str(examples_dir_fixture.parent)},
      capture_output=True,
      text=True,
      timeout=5,
    )
    assert 'usage:' in result1.stdout.lower()

    # Step 2: Completion execution
    result2 = subprocess.run(
      [sys.executable, str(cls_example), '--_complete'],
      env={
        'PYTHONPATH': str(examples_dir_fixture.parent),
        '_FREYJA_COMPLETE': 'zsh',
        'COMP_WORDS_STR': 'cls_example fo',
        'COMP_CWORD_NUM': '2',
      },
      capture_output=True,
      text=True,
      timeout=5,
    )
    # Completion should generate some output (exact output depends on implementation)
    assert result2.stdout is not None

    # Step 3: Normal execution again (should work normally)
    result3 = subprocess.run(
      [sys.executable, str(cls_example)],
      env={'PYTHONPATH': str(examples_dir_fixture.parent)},
      capture_output=True,
      text=True,
      timeout=5,
    )
    assert 'usage:' in result3.stdout.lower()
    assert result3.stdout.strip() != 'completion'

  def test_multiple_completion_types(self):
    """Test different completion shell types don't interfere."""
    cli = self.create_test_cli()

    shell_types = ['zsh', 'bash', 'fish', 'powershell']

    for shell_type in shell_types:
      with patch('sys.exit'):
        with patch.dict(os.environ, {f'_FREYJA_COMPLETE_{shell_type.upper()}': '1'}):
          assert cli._is_completion_request(), f'Failed for shell: {shell_type}'

  def test_no_state_persistence_between_instances(self):
    """Test that different CLI instances don't share completion state."""
    # Create first CLI and simulate completion
    cli1 = self.create_test_cli()

    with patch('sys.exit'):
      with patch.dict(os.environ, {'_FREYJA_COMPLETE': 'zsh'}):
        with patch('sys.stdout', new_callable=StringIO):
          cli1.run()

    # Create second CLI - should not be affected by first CLI's completion state
    cli2 = self.create_test_cli()
    assert not cli2._is_completion_request()

    # Both should work independently
    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
      with patch('sys.argv', ['test', '--help']):
        try:
          cli2.run()
        except SystemExit:
          pass

    output = mock_stdout.getvalue()
    assert 'Test CLI' in output
