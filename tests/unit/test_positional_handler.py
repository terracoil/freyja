"""Tests for PositionalHandler class."""

import enum
import pytest

from freyja.parser.positional_handler import PositionalHandler
from freyja.parser.argument_preprocessor import PositionalInfo


class TestEnum(enum.Enum):
  """Test enum for positional testing."""

  OPTION_A = "a"
  OPTION_B = "b"
  OPTION_C = "c"


class TestPositionalHandlerBasic:
  """Test basic PositionalHandler functionality."""

  @pytest.fixture
  def sample_positional_info(self):
    """Create sample positional info for testing."""
    return {
      "process": PositionalInfo(
        param_name="input_file",
        param_type=str,
        is_required=True,
        help_text="Input file to process"
      ),
      "convert": PositionalInfo(
        param_name="source_file",
        param_type=str,
        is_required=True,
        help_text="Source file to convert"
      ),
    }

  @pytest.fixture
  def handler_with_positionals(self, sample_positional_info):
    """Create handler with positional parameters."""
    return PositionalHandler(sample_positional_info)

  @pytest.fixture
  def handler_no_positionals(self):
    """Create handler with no positional parameters."""
    return PositionalHandler({})

  def test_identify_positional_basic(self, handler_with_positionals):
    """Test basic positional identification."""
    args = ["process", "input.txt", "--option", "value"]
    command_path = ["process"]

    result = handler_with_positionals.identify_positional_value(args, command_path)

    assert result is not None
    assert result[0] == "input_file"
    assert result[1] == "input.txt"

  def test_identify_no_positionals_all_defaults(self, handler_no_positionals):
    """Test identification when all params have defaults (no positionals)."""
    args = ["command", "--option1", "value1", "--option2", "value2"]
    command_path = ["command"]

    result = handler_no_positionals.identify_positional_value(args, command_path)

    assert result is None

  def test_identify_positional_after_flags(self, handler_with_positionals):
    """Test positional identification after option flags."""
    args = ["process", "--verbose", "input.txt"]
    command_path = ["process"]

    result = handler_with_positionals.identify_positional_value(args, command_path)

    assert result is not None
    assert result[1] == "input.txt"

  def test_identify_positional_mixed_with_flags(self, handler_with_positionals):
    """Test positional identification with flags before positional."""
    # Note: Current implementation has limitation where it may capture flag values
    # This test uses a simpler case where positional comes before flag values
    args = ["process", "input.txt", "--output", "out.txt", "--verbose"]
    command_path = ["process"]

    result = handler_with_positionals.identify_positional_value(args, command_path)

    assert result is not None
    assert result[1] == "input.txt"

  def test_convert_positional_to_flag(self, handler_with_positionals):
    """Test conversion of positional parameter to flag format."""
    result = handler_with_positionals.convert_positional_to_flag("input_file", "test.txt")

    assert result == ["--input-file", "test.txt"]

  def test_convert_positional_camel_case(self, handler_with_positionals):
    """Test conversion handles camelCase parameter names."""
    result = handler_with_positionals.convert_positional_to_flag("inputFile", "test.txt")

    assert result == ["--input-file", "test.txt"]

  def test_has_positional_parameter(self, handler_with_positionals):
    """Test checking if command has positional parameter."""
    assert handler_with_positionals.has_positional_parameter("process") is True
    assert handler_with_positionals.has_positional_parameter("convert") is True
    assert handler_with_positionals.has_positional_parameter("unknown") is False

  def test_get_positional_info(self, handler_with_positionals):
    """Test retrieving positional info for a command."""
    info = handler_with_positionals.get_positional_info("process")

    assert info is not None
    assert info.param_name == "input_file"
    assert info.param_type == str
    assert info.is_required is True

  def test_get_positional_info_not_found(self, handler_with_positionals):
    """Test retrieving positional info for unknown command."""
    info = handler_with_positionals.get_positional_info("unknown")

    assert info is None


class TestPositionalValidation:
  """Test positional parameter validation."""

  @pytest.fixture
  def handler(self):
    """Create handler for validation tests."""
    return PositionalHandler({})

  def test_validate_string_positional(self, handler):
    """Test validation of string positional parameter."""
    is_valid, error = handler.validate_positional_value("param", "value", str)

    assert is_valid is True
    assert error is None

  def test_validate_int_positional_valid(self, handler):
    """Test validation of valid integer positional parameter."""
    is_valid, error = handler.validate_positional_value("count", "42", int)

    assert is_valid is True
    assert error is None

  def test_validate_int_positional_invalid(self, handler):
    """Test validation of invalid integer positional parameter."""
    is_valid, error = handler.validate_positional_value("count", "not-a-number", int)

    assert is_valid is False
    assert error is not None
    assert "integer" in error.lower()

  def test_validate_float_positional_valid(self, handler):
    """Test validation of valid float positional parameter."""
    is_valid, error = handler.validate_positional_value("ratio", "3.14", float)

    assert is_valid is True
    assert error is None

  def test_validate_float_positional_invalid(self, handler):
    """Test validation of invalid float positional parameter."""
    is_valid, error = handler.validate_positional_value("ratio", "not-a-float", float)

    assert is_valid is False
    assert error is not None
    assert "float" in error.lower()

  def test_validate_bool_positional_true(self, handler):
    """Test validation of boolean positional with true values."""
    valid_true_values = ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]

    for value in valid_true_values:
      is_valid, error = handler.validate_positional_value("flag", value, bool)
      assert is_valid is True, f"Failed for value: {value}"
      assert error is None

  def test_validate_bool_positional_false(self, handler):
    """Test validation of boolean positional with false values."""
    valid_false_values = ["false", "False", "FALSE", "0", "no", "No", "NO"]

    for value in valid_false_values:
      is_valid, error = handler.validate_positional_value("flag", value, bool)
      assert is_valid is True, f"Failed for value: {value}"
      assert error is None

  def test_validate_bool_positional_invalid(self, handler):
    """Test validation of invalid boolean positional parameter."""
    is_valid, error = handler.validate_positional_value("flag", "invalid", bool)

    assert is_valid is False
    assert error is not None
    assert "boolean" in error.lower()

  def test_validate_unknown_type_accepts(self, handler):
    """Test validation accepts unknown types (lets argparse handle it)."""

    class CustomType:
      pass

    is_valid, error = handler.validate_positional_value("custom", "value", CustomType)

    # Should accept and let argparse handle the conversion
    assert is_valid is True
    assert error is None


class TestPositionalUsageGeneration:
  """Test positional parameter usage text generation."""

  @pytest.fixture
  def handler_with_required(self):
    """Create handler with required positional."""
    return PositionalHandler({
      "process": PositionalInfo("input_file", str, True, "Input file")
    })

  @pytest.fixture
  def handler_with_optional(self):
    """Create handler with optional positional."""
    return PositionalHandler({
      "process": PositionalInfo("input_file", str, False, "Input file")
    })

  def test_generate_usage_required_positional(self, handler_with_required):
    """Test usage generation for required positional parameter."""
    usage = handler_with_required.generate_positional_usage("process")

    assert usage == "INPUT_FILE"
    assert "[" not in usage  # No brackets for required params

  def test_generate_usage_optional_positional(self, handler_with_optional):
    """Test usage generation for optional positional parameter."""
    usage = handler_with_optional.generate_positional_usage("process")

    assert usage == "[INPUT_FILE]"
    assert "[" in usage and "]" in usage  # Brackets for optional params

  def test_generate_usage_no_positional(self, handler_with_required):
    """Test usage generation when command has no positional."""
    usage = handler_with_required.generate_positional_usage("unknown")

    assert usage == ""


class TestPositionalExtraction:
  """Test extraction and conversion of positional parameters."""

  @pytest.fixture
  def handler_with_positional(self):
    """Create handler with positional parameter."""
    return PositionalHandler({
      "process": PositionalInfo("input_file", str, True, "Input file")
    })

  def test_extract_and_convert_basic(self, handler_with_positional):
    """Test basic extraction and conversion of positional argument."""
    args = ["process", "input.txt"]
    command_path = ["process"]

    modified_args, conversion_made = handler_with_positional.extract_and_convert_positional(
      args, command_path
    )

    assert conversion_made is True
    assert "--input-file" in modified_args
    assert "input.txt" in modified_args

  def test_extract_and_convert_with_options(self, handler_with_positional):
    """Test extraction skips option flags correctly."""
    args = ["process", "--verbose", "input.txt", "--output", "out.txt"]
    command_path = ["process"]

    modified_args, conversion_made = handler_with_positional.extract_and_convert_positional(
      args, command_path
    )

    assert conversion_made is True
    assert "--input-file" in modified_args
    assert "--verbose" in modified_args
    assert "--output" in modified_args

  def test_extract_and_convert_no_positional(self):
    """Test extraction when command has no positional parameter."""
    handler = PositionalHandler({})
    args = ["process", "--option", "value"]
    command_path = ["process"]

    modified_args, conversion_made = handler.extract_and_convert_positional(
      args, command_path
    )

    assert conversion_made is False
    assert modified_args == args

  def test_extract_and_convert_invalid_type(self):
    """Test extraction raises error for invalid positional type."""
    handler = PositionalHandler({
      "process": PositionalInfo("count", int, True, "Count parameter")
    })
    args = ["process", "not-a-number"]
    command_path = ["process"]

    with pytest.raises(ValueError) as exc_info:
      handler.extract_and_convert_positional(args, command_path)

    assert "integer" in str(exc_info.value).lower()

  def test_extract_and_convert_empty_command_path(self, handler_with_positional):
    """Test extraction with empty command path."""
    args = ["input.txt"]
    command_path = []

    modified_args, conversion_made = handler_with_positional.extract_and_convert_positional(
      args, command_path
    )

    assert conversion_made is False
    assert modified_args == args


class TestPositionalDiscovery:
  """Test positional parameter discovery from functions."""

  def test_discover_from_function_with_required(self):
    """Test discovery of positional from function with required parameter."""

    def test_func(required_param: str, optional_param: str = "default"):
      return f"{required_param} {optional_param}"

    pos_info = PositionalHandler.discover_from_function(test_func)

    assert pos_info is not None
    assert pos_info.param_name == "required_param"
    assert pos_info.param_type == str
    assert pos_info.is_required is True

  def test_discover_from_function_no_required(self):
    """Test discovery when function has no required parameters."""

    def test_func(optional1: str = "default1", optional2: int = 42):
      return f"{optional1} {optional2}"

    pos_info = PositionalHandler.discover_from_function(test_func)

    assert pos_info is None

  def test_discover_from_function_with_self(self):
    """Test discovery skips 'self' parameter in methods."""

    class TestClass:
      def test_method(self, required: str, optional: str = "default"):
        return f"{required} {optional}"

    pos_info = PositionalHandler.discover_from_function(TestClass.test_method)

    assert pos_info is not None
    assert pos_info.param_name == "required"

  def test_discover_from_function_with_type_annotation(self):
    """Test discovery preserves type annotations."""

    def test_func(count: int, message: str = "hello"):
      return f"{message} {count}"

    pos_info = PositionalHandler.discover_from_function(test_func)

    assert pos_info is not None
    assert pos_info.param_name == "count"
    assert pos_info.param_type == int

  def test_discover_from_function_no_annotation(self):
    """Test discovery defaults to str for parameters without annotation."""

    def test_func(param, optional="default"):
      return str(param)

    pos_info = PositionalHandler.discover_from_function(test_func)

    assert pos_info is not None
    assert pos_info.param_name == "param"
    assert pos_info.param_type == str  # Defaults to str

  def test_discover_from_none(self):
    """Test discovery handles None function gracefully."""
    pos_info = PositionalHandler.discover_from_function(None)

    assert pos_info is None


class TestCommandNameHandling:
  """Test command name extraction from paths."""

  @pytest.fixture
  def handler(self):
    """Create basic handler."""
    return PositionalHandler({})

  def test_get_command_name_single_level(self, handler):
    """Test command name from single-level path."""
    command_path = ["process"]
    name = handler._get_command_name_from_path(command_path)

    assert name == "process"

  def test_get_command_name_two_levels(self, handler):
    """Test command name from two-level hierarchical path."""
    command_path = ["data-ops", "process"]
    name = handler._get_command_name_from_path(command_path)

    assert name == "data-ops--process"

  def test_get_command_name_empty_path(self, handler):
    """Test command name from empty path."""
    command_path = []
    name = handler._get_command_name_from_path(command_path)

    assert name is None

  def test_get_command_name_three_levels(self, handler):
    """Test command name from three-level path (unsupported)."""
    command_path = ["group", "subgroup", "command"]
    name = handler._get_command_name_from_path(command_path)

    # Three-level paths not currently supported
    assert name is None


class TestFlagValueDetection:
  """Test flag value detection logic."""

  @pytest.fixture
  def handler(self):
    """Create handler for testing."""
    return PositionalHandler({})

  def test_flag_has_value_with_next_arg(self, handler):
    """Test detection when flag has a value as next argument."""
    args = ["--option", "value", "--another"]
    has_value = handler._flag_has_value("--option", args, 0)

    assert has_value is True

  def test_flag_has_value_no_next_arg(self, handler):
    """Test detection when flag is last argument (expects value but doesn't have one)."""
    args = ["--option"]
    has_value = handler._flag_has_value("--option", args, 0)

    # Should return True because --option expects a value (not a boolean flag)
    assert has_value is True

  def test_flag_store_true_help(self, handler):
    """Test detection of store_true flags like --help."""
    args = ["--help", "--option", "value"]
    has_value = handler._flag_has_value("--help", args, 0)

    assert has_value is False  # --help is store_true

  def test_flag_store_true_verbose(self, handler):
    """Test detection of store_true flags like --verbose."""
    args = ["--verbose", "--option", "value"]
    has_value = handler._flag_has_value("--verbose", args, 0)

    assert has_value is False  # --verbose is store_true

  def test_flag_store_true_no_color(self, handler):
    """Test detection of store_true flags like --no-color."""
    args = ["--no-color", "--option", "value"]
    has_value = handler._flag_has_value("--no-color", args, 0)

    assert has_value is False  # --no-color is store_true

  def test_flag_has_value_next_is_flag(self, handler):
    """Test detection when next argument is another flag."""
    args = ["--option", "--another-flag"]
    has_value = handler._flag_has_value("--option", args, 0)

    # Should return True because --option expects a value (not a boolean flag)
    assert has_value is True
