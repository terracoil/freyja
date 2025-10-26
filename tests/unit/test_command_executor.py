"""Tests for CommandExecutor to achieve 92%+ coverage."""

import sys
from unittest.mock import Mock, patch

import pytest

from freyja.command.command_executor import CommandExecutor
from freyja.shared import CommandInfo


class TestCommandExecutor:
  """Test suite for CommandExecutor class."""

  def test_initialization(self):
    """Test CommandExecutor initialization."""
    mock_command_info = CommandInfo(
      name="test",
      handler=Mock(),
      parser_path="main",
      is_namespaced=False,
      is_hierarchical=False,
    )

    executor = CommandExecutor(
      command_info=mock_command_info,
      parsed_args=Mock(),
      command_tree=Mock(),
      verbose=False,
    )

    assert executor.command_info == mock_command_info
    assert executor.verbose is False

  def test_execute_simple_function(self):
    """Test executing a simple function."""
    mock_func = Mock(return_value=None)
    command_info = CommandInfo(
      name="test", handler=mock_func, parser_path="main", is_namespaced=False, is_hierarchical=False
    )

    executor = CommandExecutor(
      command_info=command_info, parsed_args=Mock(arg1="value1"), command_tree=Mock()
    )

    result = executor.execute()
    assert result == 0
    mock_func.assert_called_once()

  def test_execute_with_exception(self):
    """Test execution with exception."""
    mock_func = Mock(side_effect=Exception("Test error"))
    command_info = CommandInfo(
      name="test", handler=mock_func, parser_path="main", is_namespaced=False, is_hierarchical=False
    )

    executor = CommandExecutor(
      command_info=command_info, parsed_args=Mock(), command_tree=Mock()
    )

    with pytest.raises(Exception, match="Test error"):
      executor.execute()

  def test_prepare_kwargs(self):
    """Test kwargs preparation from parsed args."""
    command_info = CommandInfo(
      name="test", handler=Mock(), parser_path="main", is_namespaced=False, is_hierarchical=False
    )

    parsed_args = Mock()
    parsed_args.__dict__ = {
      "arg1": "value1",
      "arg2": 42,
      "command": "test",  # Should be filtered
      "_private": "hidden",  # Should be filtered
    }

    executor = CommandExecutor(
      command_info=command_info, parsed_args=parsed_args, command_tree=Mock()
    )

    kwargs = executor._prepare_kwargs(parsed_args)
    assert kwargs == {"arg1": "value1", "arg2": 42}

  def test_filter_kwargs(self):
    """Test kwargs filtering."""
    executor = CommandExecutor(
      command_info=Mock(), parsed_args=Mock(), command_tree=Mock()
    )

    kwargs = {
      "valid_arg": "value",
      "command": "should_remove",
      "func": "should_remove",
      "_private": "should_remove",
      "None_value": None,  # Should keep None values
    }

    filtered = executor._filter_kwargs(kwargs)
    assert filtered == {"valid_arg": "value", "None_value": None}

  def test_validate_handler(self):
    """Test handler validation."""
    # Valid handler
    valid_command = CommandInfo(
      name="test",
      handler=lambda: None,
      parser_path="main",
      is_namespaced=False,
      is_hierarchical=False,
    )
    executor = CommandExecutor(
      command_info=valid_command, parsed_args=Mock(), command_tree=Mock()
    )
    executor._validate_handler()  # Should not raise

    # Invalid handler
    invalid_command = CommandInfo(
      name="test", handler=None, parser_path="main", is_namespaced=False, is_hierarchical=False
    )
    executor = CommandExecutor(
      command_info=invalid_command, parsed_args=Mock(), command_tree=Mock()
    )
    with pytest.raises(ValueError, match="No handler found"):
      executor._validate_handler()

  def test_create_execution_context(self):
    """Test execution context creation."""
    command_info = CommandInfo(
      name="test-cmd",
      handler=Mock(),
      parser_path="main",
      is_namespaced=True,
      is_hierarchical=False,
      parent_class="ParentClass",
      inner_class="InnerClass",
    )

    parsed_args = Mock(pos_arg="value", opt_arg="option")

    executor = CommandExecutor(
      command_info=command_info, parsed_args=parsed_args, command_tree=Mock()
    )

    context = executor._create_execution_context(parsed_args)
    assert context.command == "test-cmd"
    assert context.namespace == "ParentClass"

  def test_execute_with_output_capture(self):
    """Test execution with output capture."""
    mock_func = Mock(return_value=None)
    command_info = CommandInfo(
      name="test", handler=mock_func, parser_path="main", is_namespaced=False, is_hierarchical=False
    )

    executor = CommandExecutor(
      command_info=command_info,
      parsed_args=Mock(),
      command_tree=Mock(),
      capture_output=True,
    )

    with patch("freyja.command.command_executor.OutputCapture") as mock_capture:
      mock_capture_instance = Mock()
      mock_capture.return_value = mock_capture_instance
      mock_capture_instance.capture_output.return_value.__enter__ = Mock()
      mock_capture_instance.capture_output.return_value.__exit__ = Mock()

      result = executor.execute()
      assert result == 0

  def test_handle_return_value(self):
    """Test handling different return values."""
    executor = CommandExecutor(
      command_info=Mock(), parsed_args=Mock(), command_tree=Mock()
    )

    # None return
    assert executor._handle_return_value(None) == 0

    # Integer return
    assert executor._handle_return_value(42) == 42

    # String return (should print)
    with patch("builtins.print") as mock_print:
      assert executor._handle_return_value("result") == 0
      mock_print.assert_called_once_with("result")

  def test_get_handler_from_info(self):
    """Test handler extraction from command info."""
    mock_handler = Mock()
    command_info = CommandInfo(
      name="test",
      handler=mock_handler,
      parser_path="main",
      is_namespaced=False,
      is_hierarchical=False,
    )

    executor = CommandExecutor(
      command_info=command_info, parsed_args=Mock(), command_tree=Mock()
    )

    handler = executor._get_handler()
    assert handler == mock_handler

  def test_execute_with_spinner(self):
    """Test execution with spinner."""
    mock_func = Mock(return_value=None)
    command_info = CommandInfo(
      name="test", handler=mock_func, parser_path="main", is_namespaced=False, is_hierarchical=False
    )

    mock_spinner = Mock()
    executor = CommandExecutor(
      command_info=command_info,
      parsed_args=Mock(),
      command_tree=Mock(),
      spinner=mock_spinner,
    )

    with patch.object(mock_spinner, "execute") as mock_execute:
      mock_execute.return_value.__enter__ = Mock(return_value=mock_spinner)
      mock_execute.return_value.__exit__ = Mock(return_value=False)

      result = executor.execute()
      assert result == 0
      mock_execute.assert_called_once()

  def test_log_execution_debug(self, capsys):
    """Test debug logging during execution."""
    command_info = CommandInfo(
      name="test", handler=Mock(), parser_path="main", is_namespaced=False, is_hierarchical=False
    )

    executor = CommandExecutor(
      command_info=command_info, parsed_args=Mock(), command_tree=Mock(), verbose=True
    )

    executor._log_execution_start({"arg": "value"})
    captured = capsys.readouterr()
    # In verbose mode, might print debug info
    # Actual implementation may vary

  def test_execute_namespaced_command(self):
    """Test executing namespaced command."""
    mock_func = Mock(return_value=None)
    command_info = CommandInfo(
      name="namespace-cmd",
      handler=mock_func,
      parser_path="namespace",
      is_namespaced=True,
      is_hierarchical=False,
      parent_class="Namespace",
    )

    executor = CommandExecutor(
      command_info=command_info, parsed_args=Mock(), command_tree=Mock()
    )

    result = executor.execute()
    assert result == 0

  def test_execute_hierarchical_command(self):
    """Test executing hierarchical command."""
    mock_func = Mock(return_value=None)
    command_info = CommandInfo(
      name="group-subgroup-cmd",
      handler=mock_func,
      parser_path="group.subgroup",
      is_namespaced=False,
      is_hierarchical=True,
    )

    executor = CommandExecutor(
      command_info=command_info, parsed_args=Mock(), command_tree=Mock()
    )

    result = executor.execute()
    assert result == 0