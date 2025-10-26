"""Tests for ArgumentPreprocessor class."""

import inspect
from unittest.mock import Mock

import pytest

from freyja.shared.command_info import CommandInfo
from freyja.shared.command_tree import CommandTree
from freyja.parser.argument_preprocessor import ArgumentPreprocessor, PositionalInfo


class TestArgumentPreprocessor:
    """Test ArgumentPreprocessor class functionality."""

    @pytest.fixture
    def simple_command_tree(self):
        """Create a simple command tree for testing."""
        tree = CommandTree()

        # Add a simple function mock
        mock_func = Mock()
        mock_func.__name__ = "test_function"

        # Create CommandInfo for the mock function
        command_info = CommandInfo(
            name="test-command",
            original_name="test_function",
            function=mock_func,
            signature=inspect.signature(lambda: None),
            docstring="Test command",
        )

        tree.add_command("test-command", command_info)

        return tree

    @pytest.fixture
    def hierarchical_command_tree(self):
        """Create hierarchical command tree for testing."""
        tree = CommandTree()

        # Mock inner class with constructor
        class MockInnerClass:
            """Mock inner class for hierarchical testing."""
            def __init__(self, database_url: str = "sqlite:///test.db", timeout: int = 30):
                self.database_url = database_url
                self.timeout = timeout

        # Add group with inner class (this should provide the sub-global options)
        tree.add_group("data-ops", "Data operations group", MockInnerClass)

        # Mock function for hierarchical command
        mock_func = Mock()
        mock_func.__name__ = "process_data"

        # Create CommandInfo for the hierarchical command
        command_info = CommandInfo(
            name="process",
            original_name="process_data",
            function=mock_func,
            signature=inspect.signature(lambda: None),
            docstring="Process data",
        )

        # Add command directly to the group (not subgroup for this test)
        tree.add_command_to_group("data-ops", "process", command_info)

        return tree

    @pytest.fixture
    def target_class_with_params(self):
        """Create target class with constructor parameters."""

        class TestClass:
            """Test class with constructor parameters."""
            def __init__(self, config_file: str = "config.json", debug: bool = False):
                self.config_file = config_file
                self.debug = debug

        return TestClass

    def test_preprocessor_initialization_simple(self, simple_command_tree):
        """Test ArgumentPreprocessor initialization with simple command tree."""
        preprocessor = ArgumentPreprocessor(simple_command_tree)

        assert preprocessor.command_tree == simple_command_tree
        assert preprocessor.target_class is None
        assert isinstance(preprocessor._global_options, set)
        assert isinstance(preprocessor._command_options, dict)
        assert isinstance(preprocessor._positional_params, dict)

    def test_preprocessor_initialization_with_class(
        self, simple_command_tree, target_class_with_params
    ):
        """Test ArgumentPreprocessor initialization with target class."""
        preprocessor = ArgumentPreprocessor(simple_command_tree, target_class_with_params)

        assert preprocessor.target_class == target_class_with_params
        assert "--config-file" in preprocessor._global_options
        assert "--debug" in preprocessor._global_options

    def test_global_options_extraction(self, simple_command_tree, target_class_with_params):
        """Test extraction of global options from target class constructor."""
        preprocessor = ArgumentPreprocessor(simple_command_tree, target_class_with_params)

        # Should extract options from constructor
        assert "--config-file" in preprocessor._global_options
        assert "--debug" in preprocessor._global_options

    def test_command_path_extraction_simple(self, simple_command_tree):
        """Test command path extraction for simple commands."""
        preprocessor = ArgumentPreprocessor(simple_command_tree)

        args = ["test-command", "--option", "value"]
        command_path = preprocessor._extract_command_path(args)

        assert command_path == ["test-command"]

    def test_command_path_extraction_hierarchical(self, hierarchical_command_tree):
        """Test command path extraction for hierarchical commands."""
        preprocessor = ArgumentPreprocessor(hierarchical_command_tree)

        args = ["data-ops", "process", "--option", "value"]
        command_path = preprocessor._extract_command_path(args)

        assert command_path == ["data-ops", "process"]

    def test_command_path_extraction_with_options(self, simple_command_tree):
        """Test command path extraction stops at first option."""
        preprocessor = ArgumentPreprocessor(simple_command_tree)

        args = ["test-command", "--option", "value", "more-args"]
        command_path = preprocessor._extract_command_path(args)

        assert command_path == ["test-command"]

    def test_is_known_option_global(self, simple_command_tree, target_class_with_params):
        """Test recognition of global options."""
        preprocessor = ArgumentPreprocessor(simple_command_tree, target_class_with_params)

        assert preprocessor._is_known_option("--config-file")
        assert preprocessor._is_known_option("--debug")
        assert preprocessor._is_known_option("--help")
        assert not preprocessor._is_known_option("--unknown-option")

    def test_is_known_option_builtin(self, simple_command_tree):
        """Test recognition of built-in options."""
        preprocessor = ArgumentPreprocessor(simple_command_tree)

        assert preprocessor._is_known_option("--help")
        assert preprocessor._is_known_option("-h")
        assert preprocessor._is_known_option("--no-color")
        assert preprocessor._is_known_option("-n")

    def test_validate_arguments_valid(self, simple_command_tree, target_class_with_params):
        """Test argument validation with valid arguments."""
        preprocessor = ArgumentPreprocessor(simple_command_tree, target_class_with_params)

        args = ["test-command", "--config-file", "config.json", "--debug"]
        is_valid, errors = preprocessor.validate_arguments(args)

        assert is_valid
        assert len(errors) == 0

    def test_validate_arguments_invalid(self, simple_command_tree):
        """Test argument validation with invalid arguments."""
        preprocessor = ArgumentPreprocessor(simple_command_tree)

        args = ["test-command", "--unknown-flag", "--another-unknown"]
        is_valid, errors = preprocessor.validate_arguments(args)

        assert not is_valid
        assert len(errors) > 0
        assert any("unknown-flag" in error for error in errors)

    def test_validate_arguments_flag_value_format(
        self, simple_command_tree, target_class_with_params
    ):
        """Test validation handles --flag=value format."""
        preprocessor = ArgumentPreprocessor(simple_command_tree, target_class_with_params)

        args = ["test-command", "--config-file=config.json"]
        is_valid, errors = preprocessor.validate_arguments(args)

        assert is_valid
        assert len(errors) == 0

    def test_preprocess_args_simple_command(self, simple_command_tree):
        """Test argument preprocessing for simple command."""
        preprocessor = ArgumentPreprocessor(simple_command_tree)

        args = ["test-command", "--verbose", "--help"]
        processed = preprocessor.preprocess_args(args)

        # Should have command followed by options in proper order
        assert "test-command" in processed
        assert "--verbose" in processed or "-v" in processed

    def test_preprocess_args_reordering(self, simple_command_tree, target_class_with_params):
        """Test that global options are reordered to come first."""
        preprocessor = ArgumentPreprocessor(simple_command_tree, target_class_with_params)

        # Global options mixed with command
        args = ["test-command", "--debug", "--config-file", "test.json"]
        processed = preprocessor.preprocess_args(args)

        # Global options should be moved to front
        debug_idx = processed.index("--debug")
        config_idx = processed.index("--config-file")
        command_idx = processed.index("test-command")

        assert debug_idx < command_idx
        assert config_idx < command_idx

    def test_subglobal_options_extraction(self, hierarchical_command_tree):
        """Test extraction of sub-global options from inner classes."""
        preprocessor = ArgumentPreprocessor(hierarchical_command_tree)

        # Should extract sub-global options from inner class constructor
        assert "data-ops" in preprocessor._subglobal_options
        subglobal_opts = preprocessor._subglobal_options["data-ops"]
        assert "--database-url" in subglobal_opts
        assert "--timeout" in subglobal_opts

    def test_is_subglobal_option(self, hierarchical_command_tree):
        """Test identification of sub-global options."""
        preprocessor = ArgumentPreprocessor(hierarchical_command_tree)

        command_path = ["data-ops", "process"]
        assert preprocessor._is_subglobal_option("--database-url", command_path)
        assert preprocessor._is_subglobal_option("--timeout", command_path)
        assert not preprocessor._is_subglobal_option("--unknown-option", command_path)

    def test_categorize_arguments_global(self, simple_command_tree, target_class_with_params):
        """Test argument categorization for global options."""
        preprocessor = ArgumentPreprocessor(simple_command_tree, target_class_with_params)

        args = ["test-command", "--config-file", "config.json", "--debug"]
        command_path = ["test-command"]
        categorized = preprocessor._categorize_arguments(args, command_path)

        assert "--config-file" in categorized["global"]
        assert "config.json" in categorized["global"]
        assert "--debug" in categorized["global"]
        assert categorized["positional"] == command_path

    def test_categorize_arguments_mixed(self, hierarchical_command_tree, target_class_with_params):
        """Test argument categorization with mixed option types."""
        preprocessor = ArgumentPreprocessor(hierarchical_command_tree, target_class_with_params)

        args = [
            "data-ops",
            "process",
            "--config-file",
            "global.json",  # global
            "--database-url",
            "sqlite://test.db",  # sub-global
            "--some-command-option",
            "value",  # command
        ]
        command_path = ["data-ops", "process"]
        categorized = preprocessor._categorize_arguments(args, command_path)

        assert "--config-file" in categorized["global"]
        assert "--database-url" in categorized["subglobal"]
        assert "--some-command-option" in categorized["command"]

    def test_reorder_arguments_flat_command(self, simple_command_tree, target_class_with_params):
        """Test argument reordering for flat commands maintains proper hierarchy."""
        preprocessor = ArgumentPreprocessor(simple_command_tree, target_class_with_params)

        categorized = {
            "global": ["--config-file", "config.json"],
            "subglobal": ["--database-url", "sqlite://test.db"],
            "command": ["--option", "value"],
            "positional": ["test-command"],
        }
        command_path = ["test-command"]

        reordered = preprocessor._reorder_arguments(categorized, command_path)

        # Check order for flat commands: global -> positional -> sub-global -> command
        config_idx = reordered.index("--config-file")
        command_idx = reordered.index("test-command")
        option_idx = reordered.index("--option")

        assert config_idx < command_idx < option_idx

    def test_reorder_arguments_hierarchical_command(
        self, hierarchical_command_tree, target_class_with_params
    ):
        """Test arg reordering for hierarchical cmds places sub-global options correctly."""
        preprocessor = ArgumentPreprocessor(hierarchical_command_tree, target_class_with_params)

        categorized = {
            "global": ["--config-file", "config.json"],
            "subglobal": ["--database-url", "sqlite://test.db"],
            "command": ["--option", "value"],
            "positional": ["data-ops", "process"],
        }
        command_path = ["data-ops", "process"]

        reordered = preprocessor._reorder_arguments(categorized, command_path)

        # Check order for hierarchical commands:
        # global -> group -> sub-global -> subcommand -> command
        # Expected order for hierarchical commands
        # ['--config-file', 'config.json', 'data-ops', '--database-url',
        #  'sqlite://test.db', 'process', '--option', 'value']

        config_idx = reordered.index("--config-file")
        group_idx = reordered.index("data-ops")
        subglobal_idx = reordered.index("--database-url")
        subcommand_idx = reordered.index("process")
        option_idx = reordered.index("--option")

        # Verify ordering: global < group < sub-global < subcommand < command
        assert config_idx < group_idx
        assert group_idx < subglobal_idx
        assert subglobal_idx < subcommand_idx
        assert subcommand_idx < option_idx

    def test_preprocess_hierarchical_command_with_trailing_options(
        self, hierarchical_command_tree, target_class_with_params
    ):
        """Test preprocessing hierarchical commands with options after final subcommand."""
        preprocessor = ArgumentPreprocessor(hierarchical_command_tree, target_class_with_params)

        # Test case: sub-global option comes AFTER the final subcommand
        args = ["data-ops", "process", "--database-url", "sqlite://test.db"]
        preprocessed = preprocessor.preprocess_args(args)

        # Should reorder to: data-ops --database-url sqlite://test.db process
        assert preprocessed[0] == "data-ops"
        assert preprocessed[1] == "--database-url"
        assert preprocessed[3] == "process"

    def test_double_dash_separator_handling(self, simple_command_tree):
        """Test handling of -- separator for end of options."""
        preprocessor = ArgumentPreprocessor(simple_command_tree)

        args = ["test-command", "--", "--not-an-option"]
        processed = preprocessor.preprocess_args(args)

        # Should preserve -- separator
        assert "--" in processed
        assert "--not-an-option" in processed

    def test_quoted_arguments_with_spaces(self, simple_command_tree):
        """Test handling of quoted strings with spaces."""
        preprocessor = ArgumentPreprocessor(simple_command_tree)

        # Simulating quoted argument (shell would pass as single arg)
        args = ["test-command", "--message", "hello world", "--name", "John Doe"]
        processed = preprocessor.preprocess_args(args)

        # Should preserve quoted arguments as-is
        assert "hello world" in processed
        assert "John Doe" in processed

    def test_unicode_and_special_characters(self, simple_command_tree):
        """Test handling of Unicode and special characters in arguments."""
        preprocessor = ArgumentPreprocessor(simple_command_tree)

        args = ["test-command", "--text", "Hello 世界", "--emoji", "🚀✨"]
        processed = preprocessor.preprocess_args(args)

        # Should preserve Unicode characters
        assert "Hello 世界" in processed
        assert "🚀✨" in processed

    def test_duplicate_argument_handling(self, simple_command_tree, target_class_with_params):
        """Test handling of duplicate arguments (last one wins)."""
        preprocessor = ArgumentPreprocessor(simple_command_tree, target_class_with_params)

        args = [
            "test-command",
            "--config-file", "first.json",
            "--config-file", "second.json"
        ]
        processed = preprocessor.preprocess_args(args)

        # Both should be present (argparse handles duplicate precedence)
        assert processed.count("--config-file") == 2
        assert "first.json" in processed
        assert "second.json" in processed

    def test_empty_args_list_handling(self, simple_command_tree):
        """Test handling of empty argument list."""
        preprocessor = ArgumentPreprocessor(simple_command_tree)

        args = []
        processed = preprocessor.preprocess_args(args)

        # Should return empty list or minimal structure
        assert isinstance(processed, list)

    def test_args_with_equals_sign_format(self, simple_command_tree, target_class_with_params):
        """Test handling of --flag=value format."""
        preprocessor = ArgumentPreprocessor(simple_command_tree, target_class_with_params)

        args = ["test-command", "--config-file=test.json", "--debug"]
        processed = preprocessor.preprocess_args(args)

        # Should preserve --flag=value format
        assert "--config-file=test.json" in processed or (
            "--config-file" in processed and "test.json" in processed
        )


class TestPositionalInfo:
    """Test PositionalInfo dataclass."""

    def test_positional_info_creation(self):
        """Test creation of PositionalInfo."""
        info = PositionalInfo("test_param", str, True, "Test parameter help")

        assert info.param_name == "test_param"
        assert info.param_type == str
        assert info.is_required is True
        assert info.help_text == "Test parameter help"

    def test_positional_info_without_help(self):
        """Test creation of PositionalInfo without help text."""
        info = PositionalInfo("test_param", int, False)

        assert info.param_name == "test_param"
        assert info.param_type == int
        assert info.is_required is False
        assert info.help_text is None


class TestPositionalParameterExtraction:
    """Test positional parameter extraction functionality."""

    def test_extract_positional_parameter_with_required(self):
        """Test extraction of positional parameter from function with required param."""

        def test_func(required_param: str, optional_param: str = "default"):
            return f"{required_param} {optional_param}"

        tree = CommandTree()
        preprocessor = ArgumentPreprocessor(tree)

        positional_info = preprocessor._extract_positional_parameter(test_func)

        assert positional_info is not None
        assert positional_info.param_name == "required_param"
        assert positional_info.param_type == str
        assert positional_info.is_required is True

    def test_extract_positional_parameter_no_required(self):
        """Test extraction when no required parameters exist."""

        def test_func(optional_param: str = "default", another_optional: int = 42):
            return f"{optional_param} {another_optional}"

        tree = CommandTree()
        preprocessor = ArgumentPreprocessor(tree)

        positional_info = preprocessor._extract_positional_parameter(test_func)

        assert positional_info is None

    def test_extract_positional_parameter_skip_self(self):
        """Test extraction skips 'self' parameter for methods."""

        class TestClass:
            """Test class for positional parameter extraction."""
            def test_method(self, required_param: str, optional_param: str = "default"):
                """Test method with required and optional parameters."""
                return f"{required_param} {optional_param}"

        tree = CommandTree()
        preprocessor = ArgumentPreprocessor(tree)

        positional_info = preprocessor._extract_positional_parameter(TestClass.test_method)

        assert positional_info is not None
        assert positional_info.param_name == "required_param"

    def test_is_first_non_default_param(self):
        """Test identification of first non-default parameter."""

        def test_func(first_required: str, second_required: int, optional: str = "default"):
            return f"{first_required} {second_required} {optional}"

        tree = CommandTree()
        preprocessor = ArgumentPreprocessor(tree)

        assert preprocessor._is_first_non_default_param(test_func, "first_required") is True
        assert preprocessor._is_first_non_default_param(test_func, "second_required") is False
        assert preprocessor._is_first_non_default_param(test_func, "optional") is False

    def test_is_first_non_default_param_with_self(self):
        """Test identification with self parameter."""

        class TestClass:
            """Test class for first non-default param identification."""
            def test_method(self, first_required: str, optional: str = "default"):
                """Test method with first required parameter."""
                return f"{first_required} {optional}"

        tree = CommandTree()
        preprocessor = ArgumentPreprocessor(tree)

        assert (
            preprocessor._is_first_non_default_param(TestClass.test_method, "first_required")
            is True
        )
        assert preprocessor._is_first_non_default_param(TestClass.test_method, "optional") is False


class TestEdgeCases:
    """Test edge cases for ArgumentPreprocessor."""

    def test_empty_command_tree(self):
        """Test preprocessor with empty command tree."""
        tree = CommandTree()
        preprocessor = ArgumentPreprocessor(tree)

        args = ["--help"]
        processed = preprocessor.preprocess_args(args)

        # Should handle gracefully
        assert isinstance(processed, list)

    def test_no_target_class(self):
        """Test preprocessor without target class."""
        tree = CommandTree()
        preprocessor = ArgumentPreprocessor(tree, None)

        # Should use fallback global options (no longer includes verbose)
        assert "--no-color" in preprocessor._global_options or "-n" in preprocessor._global_options
        assert "--help" in preprocessor._global_options or "-h" in preprocessor._global_options

    def test_malformed_arguments(self):
        """Test handling of malformed arguments."""
        tree = CommandTree()
        preprocessor = ArgumentPreprocessor(tree)

        # Test with mixed valid and invalid args
        args = ["--help", "command", "--unknown", "value"]
        processed = preprocessor.preprocess_args(args)

        # Should process without crashing
        assert isinstance(processed, list)

    def test_option_without_value(self):
        """Test handling of boolean options without values."""
        tree = CommandTree()
        preprocessor = ArgumentPreprocessor(tree)

        args = ["command", "--help", "--verbose"]
        processed = preprocessor.preprocess_args(args)

        # Should handle boolean flags correctly
        assert "--help" in processed or "-h" in processed
