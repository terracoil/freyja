"""Comprehensive tests for ExecutionSpinner to achieve 80%+ coverage."""

from io import StringIO
from unittest.mock import Mock, patch

import pytest
from freyja.utils.spinner import CommandContext, ExecutionSpinner


class TestCommandContext:
  """Test suite for CommandContext dataclass."""

  def test_command_context_defaults(self):
    """Test CommandContext with default values."""
    context = CommandContext()
    assert context.namespace is None
    assert context.command == ''
    assert context.subcommand is None
    assert context.global_args == {}
    assert context.group_args == {}
    assert context.command_args == {}
    assert context.positional_args == []
    assert context.custom_status is None

  def test_command_context_with_values(self):
    """Test CommandContext with custom values."""
    context = CommandContext(
      namespace='system',
      command='process',
      subcommand='run',
      global_args={'verbose': True},
      group_args={'config': 'test.cfg'},
      command_args={'file': 'input.txt'},
      positional_args=['arg1', 'arg2'],
      custom_status='Processing...',
    )

    assert context.namespace == 'system'
    assert context.command == 'process'
    assert context.subcommand == 'run'
    assert context.global_args == {'verbose': True}
    assert context.group_args == {'config': 'test.cfg'}
    assert context.command_args == {'file': 'input.txt'}
    assert context.positional_args == ['arg1', 'arg2']
    assert context.custom_status == 'Processing...'


class TestExecutionSpinner:
  """Test suite for ExecutionSpinner class."""

  def test_initialization_default(self):
    """Test ExecutionSpinner initialization with defaults."""
    spinner = ExecutionSpinner()
    assert spinner.color_formatter is None
    assert spinner.verbose is False
    assert spinner.spinner_chars == ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    assert spinner.current == 0
    assert spinner.running is False
    assert spinner.thread is None
    assert spinner.command_context is None
    assert spinner.status_line == ''

  def test_initialization_with_params(self):
    """Test ExecutionSpinner initialization with parameters."""
    mock_formatter = Mock()
    spinner = ExecutionSpinner(color_formatter=mock_formatter, verbose=True)
    assert spinner.color_formatter is mock_formatter
    assert spinner.verbose is True

  def test_augment_status(self):
    """Test augment_status method."""
    spinner = ExecutionSpinner()
    context = CommandContext(command='test')
    spinner.command_context = context

    spinner.augment_status('Custom message')
    assert spinner.command_context.custom_status == 'Custom message'

  def test_augment_status_no_context(self):
    """Test augment_status with no context."""
    spinner = ExecutionSpinner()
    # Should not raise error
    spinner.augment_status('Custom message')

  def test_format_command_name_simple(self):
    """Test _format_command_name with simple command."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(command='run')
    assert spinner._format_command_name() == 'run'

  def test_format_command_name_with_namespace(self):
    """Test _format_command_name with namespace."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(namespace='system', command='check')
    assert spinner._format_command_name() == 'system:check'

  def test_format_command_name_with_subcommand(self):
    """Test _format_command_name with subcommand."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(namespace='db', command='migrate', subcommand='up')
    assert spinner._format_command_name() == 'db:migrate:up'

  def test_format_command_name_no_context(self):
    """Test _format_command_name with no context."""
    spinner = ExecutionSpinner()
    assert spinner._format_command_name() == ''

  def test_format_options_empty(self):
    """Test _format_options with no options."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(command='test')
    assert spinner._format_options() == []

  def test_format_options_positional(self):
    """Test _format_options with positional arguments."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(
      command='test', positional_args=['file1.txt', 'file2.txt']
    )
    options = spinner._format_options()
    assert options == ['positional:0:file1.txt', 'positional:1:file2.txt']

  def test_format_options_global(self):
    """Test _format_options with global arguments."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(
      command='test', global_args={'verbose': True, 'debug': False}
    )
    options = spinner._format_options()
    assert 'global:verbose:True' in options
    assert 'global:debug:False' in options

  def test_format_options_all_types(self):
    """Test _format_options with all argument types."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(
      namespace='ns',
      command='cmd',
      positional_args=['pos1'],
      global_args={'global1': 'val1'},
      group_args={'group1': 'val2'},
      command_args={'cmd1': 'val3'},
    )
    options = spinner._format_options()
    assert 'positional:0:pos1' in options
    assert 'global:global1:val1' in options
    assert 'ns:group1:val2' in options
    assert 'cmd:cmd1:val3' in options

  def test_update_status_line_simple(self):
    """Test _update_status_line with simple command."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(command='process')
    spinner._update_status_line()
    assert spinner.status_line == 'Executing process'

  def test_update_status_line_with_options(self):
    """Test _update_status_line with options."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(
      command='run', command_args={'input': 'file.txt', 'output': 'result.txt'}
    )
    spinner._update_status_line()
    assert 'Executing run' in spinner.status_line
    assert '[' in spinner.status_line
    assert ']' in spinner.status_line

  def test_update_status_line_many_options(self):
    """Test _update_status_line with many options (truncation)."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(
      command='run',
      command_args={'opt1': 'val1', 'opt2': 'val2', 'opt3': 'val3', 'opt4': 'val4'},
    )
    spinner._update_status_line()
    assert 'Executing run' in spinner.status_line
    assert '... +' in spinner.status_line

  def test_update_status_line_custom_status(self):
    """Test _update_status_line with custom status."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(command='process', custom_status='50% complete')
    spinner._update_status_line()
    assert 'Executing process' in spinner.status_line
    assert '→ 50% complete' in spinner.status_line

  def test_start_verbose_mode(self, capsys):
    """Test start in verbose mode."""
    spinner = ExecutionSpinner(verbose=True)
    context = CommandContext(command='test')
    spinner.start(context)

    captured = capsys.readouterr()
    assert 'Executing test' in captured.out
    assert spinner.running is False  # Should not start thread in verbose mode

  def test_start_verbose_mode_with_formatter(self):
    """Test start in verbose mode with color formatter."""
    mock_formatter = Mock()
    mock_formatter.apply_style = Mock(return_value='[styled]Executing test[/styled]')

    spinner = ExecutionSpinner(color_formatter=mock_formatter, verbose=True)
    context = CommandContext(command='test')

    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
      spinner.start(context)
      output = mock_stdout.getvalue()

    assert '[styled]' in output or 'Executing test' in output

  @patch('time.sleep', return_value=None)
  @patch('sys.stdout', new_callable=StringIO)
  def test_start_non_verbose_mode(self, mock_stdout, mock_sleep):
    """Test start in non-verbose mode."""
    spinner = ExecutionSpinner(verbose=False)
    context = CommandContext(command='test')

    spinner.start(context)
    assert spinner.running is True
    assert spinner.thread is not None
    assert spinner.thread.daemon is True

    # Stop the spinner
    spinner.running = False
    if spinner.thread:
      spinner.thread.join(timeout=0.1)

  def test_spin_method(self):
    """Test _spin method behavior."""
    spinner = ExecutionSpinner()
    spinner.status_line = 'Test status'
    spinner.running = True

    # Mock _can_write_to_stdout to return True so output is captured
    with patch.object(spinner, '_can_write_to_stdout', return_value=True):
      # Mock stdout to capture output
      with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
        with patch('time.sleep', side_effect=[None, None, KeyboardInterrupt]):
          # Run spin for a short time
          try:
            spinner._spin()
          except KeyboardInterrupt:
            pass

      output = mock_stdout.getvalue()
      assert 'Test status' in output

  def test_stop_success(self):
    """Test stop method with success."""
    spinner = ExecutionSpinner()
    spinner.running = True
    spinner.status_line = 'Test command'

    # Mock _can_write_to_stdout to return True so output is captured
    with patch.object(spinner, '_can_write_to_stdout', return_value=True):
      with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
        spinner.stop(success=True)

      assert spinner.running is False
      output = mock_stdout.getvalue()
      assert '✓' in output or 'Test command' in output

  def test_stop_failure(self):
    """Test stop method with failure."""
    spinner = ExecutionSpinner()
    spinner.running = True
    spinner.status_line = 'Test command'

    # Mock _can_write_to_stdout to return True so output is captured
    with patch.object(spinner, '_can_write_to_stdout', return_value=True):
      with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
        spinner.stop(success=False)

      assert spinner.running is False
      output = mock_stdout.getvalue()
      assert '✗' in output or 'Test command' in output

  def test_stop_with_thread(self):
    """Test stop method with active thread."""
    spinner = ExecutionSpinner()
    spinner.running = True
    mock_thread = Mock()
    mock_thread.join = Mock()
    spinner.thread = mock_thread

    spinner.stop()
    mock_thread.join.assert_called_once_with(timeout=1.0)

  def test_execute_context_manager_success(self):
    """Test execute context manager with successful execution."""
    spinner = ExecutionSpinner(verbose=True)
    context = CommandContext(command='test')

    with spinner.execute(context) as s:
      assert s is spinner
      # Command executes successfully

  def test_execute_context_manager_exception(self):
    """Test execute context manager with exception."""
    spinner = ExecutionSpinner(verbose=True)
    context = CommandContext(command='test')

    with pytest.raises(ValueError):
      with spinner.execute(context):
        raise ValueError('Test error')

  def test_execute_context_manager_augment_status(self):
    """Test execute context manager with status augmentation."""
    spinner = ExecutionSpinner(verbose=True)
    context = CommandContext(command='test')

    with spinner.execute(context) as s:
      s.augment_status('Processing...')
      assert s.command_context.custom_status == 'Processing...'

  def test_format_command_name_empty_parts(self):
    """Test _format_command_name with empty command."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext()  # Empty command
    assert spinner._format_command_name() == ''

  def test_format_options_no_namespace(self):
    """Test _format_options with group args but no namespace."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(command='cmd', group_args={'key': 'value'})
    options = spinner._format_options()
    assert 'group:key:value' in options

  def test_format_options_no_command_name(self):
    """Test _format_options with command args but empty command."""
    spinner = ExecutionSpinner()
    spinner.command_context = CommandContext(command='', command_args={'key': 'value'})
    options = spinner._format_options()
    assert 'command:key:value' in options

  def test_update_status_line_no_context(self):
    """Test _update_status_line with no context."""
    spinner = ExecutionSpinner()
    spinner._update_status_line()
    assert spinner.status_line == ''

  def test_verbose_mode_formatter_exception(self):
    """Test verbose mode when formatter raises exception."""
    mock_formatter = Mock()
    mock_formatter.apply_style = Mock(side_effect=Exception('Style error'))

    spinner = ExecutionSpinner(color_formatter=mock_formatter, verbose=True)
    context = CommandContext(command='test')

    # Should fall back to plain output
    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
      spinner.start(context)
      output = mock_stdout.getvalue()

    assert 'Executing test' in output

  def test_stop_verbose_mode(self):
    """Test stop in verbose mode (should not clear line)."""
    spinner = ExecutionSpinner(verbose=True)
    spinner.status_line = 'Test command'

    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
      spinner.stop(success=True)

    # In verbose mode, should not output anything
    output = mock_stdout.getvalue()
    assert output == ''  # No output in verbose mode
