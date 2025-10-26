"""Tests for ExecutionCoordinator to achieve 85%+ coverage."""

from unittest.mock import Mock, patch

import pytest

from freyja.cli.execution_coordinator import ExecutionCoordinator
from freyja.shared import CommandInfo


class TestExecutionCoordinator:
  """Test suite for ExecutionCoordinator class."""

  def test_initialization(self):
    """Test ExecutionCoordinator initialization."""
    coordinator = ExecutionCoordinator(
      command_tree=Mock(),
      parsers={"main": Mock()},
      function_opts={},
      theme_name="universal",
      no_color=False,
      capture_output=False,
    )
    assert coordinator.command_tree is not None
    assert coordinator.parsers is not None
    assert coordinator.theme_name == "universal"
    assert coordinator.no_color is False

  @patch("freyja.cli.execution_coordinator.ColorFormatter")
  @patch("freyja.cli.execution_coordinator.create_default_theme")
  def test_setup_theme(self, mock_create_theme, mock_formatter):
    """Test theme setup."""
    mock_theme = Mock()
    mock_create_theme.return_value = mock_theme

    coordinator = ExecutionCoordinator(
      command_tree=Mock(),
      parsers={"main": Mock()},
      function_opts={},
      theme_name="colorful",
      no_color=False,
    )
    coordinator._setup_theme()

    mock_create_theme.assert_called_once_with("colorful")
    mock_formatter.assert_called_once()

  def test_get_parser_for_command_path(self):
    """Test getting parser for command path."""
    mock_parser = Mock()
    coordinator = ExecutionCoordinator(
      command_tree=Mock(),
      parsers={"main": mock_parser, "subcmd": Mock()},
      function_opts={},
    )

    # Test getting main parser
    assert coordinator._get_parser_for_command_path(None) == mock_parser
    assert coordinator._get_parser_for_command_path("") == mock_parser

    # Test getting subparser
    assert coordinator._get_parser_for_command_path("subcmd") is not None

  def test_determine_command_path_simple(self):
    """Test determining command path."""
    mock_tree = Mock()
    mock_tree.get_all_command_names.return_value = ["cmd1", "cmd2"]

    coordinator = ExecutionCoordinator(
      command_tree=mock_tree, parsers={"main": Mock()}, function_opts={}
    )

    # Test with matching command
    path = coordinator._determine_command_path(["cmd1"])
    assert path == "cmd1"

    # Test with no matching command
    path = coordinator._determine_command_path(["unknown"])
    assert path is None

  @patch("sys.argv", ["prog", "--help"])
  def test_run_help_flag(self):
    """Test run with help flag."""
    mock_parser = Mock()
    mock_parser.parse_args.side_effect = SystemExit(0)

    coordinator = ExecutionCoordinator(
      command_tree=Mock(), parsers={"main": mock_parser}, function_opts={}
    )

    with pytest.raises(SystemExit):
      coordinator.run()

  @patch("freyja.cli.execution_coordinator.CommandExecutor")
  def test_execute_command(self, mock_executor_class):
    """Test command execution."""
    mock_executor = Mock()
    mock_executor_class.return_value = mock_executor

    mock_tree = Mock()
    mock_command_info = CommandInfo(
      name="test_cmd",
      handler=lambda: None,
      parser_path="main",
      is_namespaced=False,
      is_hierarchical=False,
    )
    mock_tree.find_command.return_value = mock_command_info

    coordinator = ExecutionCoordinator(
      command_tree=mock_tree, parsers={"main": Mock()}, function_opts={}
    )

    args = Mock()
    coordinator._execute_command("test_cmd", args)

    mock_executor.execute.assert_called_once()

  def test_handle_command_exception(self, capsys):
    """Test exception handling during command execution."""
    coordinator = ExecutionCoordinator(
      command_tree=Mock(), parsers={"main": Mock()}, function_opts={}
    )

    error_msg = "Test error"
    coordinator._handle_command_exception(Exception(error_msg), "test_cmd", False)

    captured = capsys.readouterr()
    assert "Error executing" in captured.out

  def test_parse_arguments(self):
    """Test argument parsing."""
    mock_parser = Mock()
    mock_parser.parse_args.return_value = Mock(command="test")

    coordinator = ExecutionCoordinator(
      command_tree=Mock(), parsers={"main": mock_parser}, function_opts={}
    )

    args = coordinator._parse_arguments(["test"], "main")
    assert args is not None

  @patch("sys.argv", ["prog", "test-cmd"])
  def test_run_with_command(self):
    """Test run with valid command."""
    mock_tree = Mock()
    mock_tree.get_all_command_names.return_value = ["test-cmd"]
    mock_command_info = CommandInfo(
      name="test-cmd",
      handler=Mock(return_value=None),
      parser_path="main",
      is_namespaced=False,
      is_hierarchical=False,
    )
    mock_tree.find_command.return_value = mock_command_info

    mock_parser = Mock()
    mock_parser.parse_args.return_value = Mock(command="test-cmd")

    coordinator = ExecutionCoordinator(
      command_tree=mock_tree, parsers={"main": mock_parser}, function_opts={}
    )

    result = coordinator.run()
    assert result == 0

  def test_should_show_help(self):
    """Test help detection logic."""
    coordinator = ExecutionCoordinator(
      command_tree=Mock(), parsers={"main": Mock()}, function_opts={}
    )

    assert coordinator._should_show_help([])
    assert coordinator._should_show_help(["--help"])
    assert coordinator._should_show_help(["-h"])
    assert not coordinator._should_show_help(["cmd"])

  def test_extract_verbose_flag(self):
    """Test verbose flag extraction."""
    coordinator = ExecutionCoordinator(
      command_tree=Mock(), parsers={"main": Mock()}, function_opts={}
    )

    # Test with verbose flag
    remaining = coordinator._extract_verbose_flag(["--verbose", "cmd"])
    assert remaining == ["cmd"]
    assert coordinator.verbose is True

    # Reset and test without verbose
    coordinator.verbose = False
    remaining = coordinator._extract_verbose_flag(["cmd"])
    assert remaining == ["cmd"]
    assert coordinator.verbose is False

  def test_get_command_from_args(self):
    """Test command extraction from parsed args."""
    coordinator = ExecutionCoordinator(
      command_tree=Mock(), parsers={"main": Mock()}, function_opts={}
    )

    # Test with command attribute
    args = Mock(command="test-cmd")
    assert coordinator._get_command_from_args(args) == "test-cmd"

    # Test without command attribute
    args = Mock(spec=[])
    assert coordinator._get_command_from_args(args) is None

  @patch("freyja.cli.execution_coordinator.ExecutionSpinner")
  def test_create_spinner(self, mock_spinner_class):
    """Test spinner creation."""
    coordinator = ExecutionCoordinator(
      command_tree=Mock(), parsers={"main": Mock()}, function_opts={}
    )
    coordinator.color_formatter = Mock()

    spinner = coordinator._create_spinner(verbose=False)
    assert spinner is not None
    mock_spinner_class.assert_called_once()

  def test_clean_argv_for_parsing(self):
    """Test argv cleaning for parsing."""
    coordinator = ExecutionCoordinator(
      command_tree=Mock(), parsers={"main": Mock()}, function_opts={}
    )

    # Test removing verbose flag
    cleaned = coordinator._clean_argv_for_parsing(["--verbose", "cmd", "--arg"])
    assert "--verbose" not in cleaned
    assert "cmd" in cleaned

  def test_format_exception_message(self):
    """Test exception message formatting."""
    coordinator = ExecutionCoordinator(
      command_tree=Mock(), parsers={"main": Mock()}, function_opts={}
    )
    coordinator.color_formatter = Mock()
    coordinator.color_formatter.format_error.return_value = "Formatted error"

    msg = coordinator._format_exception_message(Exception("Test"), "cmd")
    assert "Formatted error" in msg or "Test" in msg