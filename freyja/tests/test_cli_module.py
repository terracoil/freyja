"""Tests for the modernized FreyjaCLI class functionality."""
from pathlib import Path

import pytest

from freyja import FreyjaCLI
from freyja.parser import DocStringParser


class TestDocStringParser:
  """Test docstring parsing functionality."""

  def test_parse_empty_docstring(self):
    """Test parsing empty or None docstring."""
    main, params = DocStringParser.parse_docstring("")
    assert main == ""
    assert params == {}

    main, params = DocStringParser.parse_docstring(None)
    assert main == ""
    assert params == {}

  def test_parse_simple_docstring(self):
    """Test parsing docstring with only main description."""
    docstring = "This is a simple function."
    main, params = DocStringParser.parse_docstring(docstring)
    assert main == "This is a simple function."
    assert params == {}

  def test_parse_docstring_with_params(self):
    """Test parsing docstring with parameter descriptions."""
    docstring = """
        This is a function with parameters.

        :param name: The name parameter
        :param count: The count parameter
        """
    main, params = DocStringParser.parse_docstring(docstring)
    assert main == "This is a function with parameters."
    assert len(params) == 2
    assert params['name'].name == 'name'
    assert params['name'].description == 'The name parameter'
    assert params['count'].name == 'count'
    assert params['count'].description == 'The count parameter'

  def test_extract_function_help(self, sample_module):
    """Test extracting help from actual function."""
    desc, param_help = DocStringParser.extract_function_help(sample_module.sample_function)
    assert "Sample function with docstring parameters" in desc
    assert param_help['name'] == "The name to greet in the message"
    assert param_help['count'] == "Number of times to repeat the greeting"


class TestModernizedCLI:
  """Test modernized FreyjaCLI functionality without function_opts."""

  def test_cli_creation_without_function_opts(self, sample_module):
    """Test FreyjaCLI can be created without function_opts parameter."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")
    assert cli.title == "Test FreyjaCLI"
    assert 'sample-function' in cli.commands
    assert 'function-with-types' in cli.commands
    assert cli.target_module == sample_module

  def test_function_discovery(self, sample_module):
    """Test automatic function discovery."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    # Should include public functions (converted to kebab-case)
    assert 'sample-function' in cli.commands
    assert 'function-with-types' in cli.commands
    assert 'function-without-docstring' in cli.commands

    # Should not include private functions or classes
    command_names = list(cli.commands.keys())
    assert not any(name.startswith('_') for name in command_names)
    # Classes should not appear as cmd_tree

  def test_custom_function_filter(self, sample_module):
    """Test custom function filter."""

    def only_sample_function(name, obj):
      return name == 'sample_function'

    cli = FreyjaCLI(sample_module, "Test FreyjaCLI", function_filter=only_sample_function)
    # Should only have sample-function (converted to kebab-case)
    assert 'sample-function' in cli.commands
    command_count = len([k for k, v in cli.commands.items() if v.get('type') == 'command'])
    assert command_count == 1

  def test_parser_creation_with_docstrings(self, sample_module):
    """Test parser creation using docstring descriptions."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")
    parser = cli.create_parser()

    # Check that help contains docstring descriptions
    help_text = parser.format_help()
    assert "Test FreyjaCLI" in help_text

    # Commands should use kebab-case
    assert "sample-function" in help_text
    assert "function-with-types" in help_text

  def test_argument_parsing_with_docstring_help(self, sample_module):
    """Test that arguments get help from docstrings."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")
    parser = cli.create_parser()

    # Get subparser for sample_function
    subparsers_actions = [
      action for action in parser._actions
      if hasattr(action, 'choices') and action.choices is not None
    ]
    if subparsers_actions:
      sub = subparsers_actions[0].choices['sample-function']
      help_text = sub.format_help()

      # Should contain parameter help from docstring
      assert "The name to greet" in help_text
      assert "Number of times to repeat" in help_text

  def test_type_handling(self, sample_module):
    """Test various type annotations work correctly."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    # Test basic execution with defaults
    result = cli.run(['function-with-types', '--text', 'hello'])
    assert result['text'] == 'hello'
    assert result['number'] == 42  # default
    assert result['active'] is False  # default

  def test_enum_handling(self, sample_module):
    """Test enum parameter handling."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    # Test enum choice
    result = cli.run(['function-with-types', '--text', 'test', '--choice', 'OPTION_B'])
    from freyja.tests.conftest import TestEnum
    assert result['choice'] == TestEnum.OPTION_B

  def test_boolean_flags(self, sample_module):
    """Test boolean flag handling."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    # Test boolean flag - should be store_true action
    result = cli.run(['function-with-types', '--text', 'test', '--active'])
    assert result['active'] is True

  def test_path_handling(self, sample_module):
    """Test Path type handling."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    # Test Path parameter
    result = cli.run(['function-with-types', '--text', 'test', '--file-path', '/tmp/test.txt'])
    assert isinstance(result['file_path'], Path)
    assert str(result['file_path']) == '/tmp/test.txt'

  def test_args_kwargs_exclusion(self, sample_module):
    """Test that *args and **kwargs are excluded from FreyjaCLI."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")
    parser = cli.create_parser()

    # Get help for function_with_args_kwargs
    help_text = parser.format_help()

    # Should only show 'required' parameter, not args/kwargs
    subparsers_actions = [
      action for action in parser._actions
      if hasattr(action, 'choices') and action.choices is not None
    ]
    if subparsers_actions and 'function-with-args-kwargs' in subparsers_actions[0].choices:
      sub = subparsers_actions[0].choices['function-with-args-kwargs']
      sub_help = sub.format_help()
      assert '--required' in sub_help
      # Should not contain --args or --kwargs as FreyjaCLI options
      assert '--args' not in sub_help
      assert '--kwargs' not in sub_help
      # But should only show the required parameter
      assert '--required' in sub_help

  def test_function_execution(self, sample_module):
    """Test function execution through FreyjaCLI."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    result = cli.run(['sample-function', '--name', 'Alice', '--count', '3'])
    assert result == "Hello Alice! Hello Alice! Hello Alice! "

  def test_function_execution_with_defaults(self, sample_module):
    """Test function execution with default parameters."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    result = cli.run(['sample-function'])
    assert result == "Hello world! "

  def test_kebab_case_conversion(self, sample_module):
    """Test snake_case to kebab-case conversion for FreyjaCLI."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")
    parser = cli.create_parser()

    help_text = parser.format_help()

    # Function names should be kebab-case
    assert 'function-with-types' in help_text
    assert 'function_with_types' not in help_text

  def test_error_handling(self, sample_module):
    """Test error handling in FreyjaCLI execution."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    # Test missing required argument
    with pytest.raises(SystemExit):
      cli.run(['function-with-types'])  # Missing required --text

  def test_verbose_flag(self, sample_module):
    """Test global verbose flag is available."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")
    parser = cli.create_parser()

    help_text = parser.format_help()
    assert '--verbose' in help_text or '-v' in help_text

  def test_run_method_functionality(self, sample_module):
    """Test run method works (display method was removed)."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    # Should have run method for FreyjaCLI execution
    assert hasattr(cli, 'run')
    assert callable(cli.run)
    
    # Should be able to create parser
    parser = cli.create_parser()
    assert parser is not None


class TestBackwardCompatibility:
  """Test backward compatibility with existing code patterns."""

  def test_function_execution_methods_still_exist(self, sample_module):
    """Test that old method names still work if needed."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    # Core functionality should work the same way
    result = cli.run(['sample-function', '--name', 'test'])
    assert "Hello test!" in result


class TestColorOptions:
  """Test color-related FreyjaCLI options."""

  def test_no_color_option_exists(self, sample_module):
    """Test that --no-color/-n option is available."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")
    parser = cli.create_parser()

    help_text = parser.format_help()
    assert '--no-color' in help_text or '-n' in help_text

  def test_no_color_parser_creation(self, sample_module):
    """Test creating parser with no_color parameter."""
    from freyja.theme import create_default_theme
    theme = create_default_theme()

    cli = FreyjaCLI(sample_module, "Test FreyjaCLI", theme=theme)

    # Test that no_color parameter works
    parser_with_color = cli.create_parser(no_color=False)
    parser_no_color = cli.create_parser(no_color=True)

    # Both should generate help without errors
    help_with_color = parser_with_color.format_help()
    help_no_color = parser_no_color.format_help()

    assert "Test FreyjaCLI" in help_with_color
    assert "Test FreyjaCLI" in help_no_color

  def test_no_color_flag_detection(self, sample_module):
    """Test that --no-color flag is properly detected in run method."""
    cli = FreyjaCLI(sample_module, "Test FreyjaCLI")

    # Test command execution with --no-color (global flag comes first)
    result = cli.run(['--no-color', 'sample-function'])
    assert "Hello world!" in result

    # Test with short form
    result = cli.run(['-n', 'sample-function'])
    assert "Hello world!" in result
