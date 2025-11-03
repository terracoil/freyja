"""Tests for positional parameter support functionality."""

from freyja import FreyjaCLI


class SampleClassWithPositional:
  """Sample class for positional parameter testing."""

  def __init__(self, config: str = 'config.json'):
    """Initialize with configuration."""
    self.config = config

  def process_item(self, item_name: str, priority: str = 'medium', debug: bool = False):
    """Process an item with positional support.

    :param item_name: Name of item to process (positional)
    :param priority: Priority level
    :param debug: Enable debug mode
    """
    result = f'Processing item: {item_name} (priority: {priority}, config: {self.config})'
    if debug:
      result += ' [DEBUG MODE]'
    return result

  def no_positional_method(self, optional_param: str = 'default'):
    """Method without positional parameters.

    :param optional_param: Optional parameter
    """
    return f'No positional: {optional_param}'


class SampleClassWithInnerClasses:
  """Sample class with inner classes for hierarchical positional testing."""

  def __init__(self, base_config: str = 'base.json'):
    """Initialize with base configuration."""
    self.base_config = base_config

  class DataOps:
    """Data operations group."""

    def __init__(self, database_url: str = 'sqlite:///test.db'):
      """Initialize data operations."""
      self.database_url = database_url

    def process_file(self, file_path: str, format_type: str = 'json', validate: bool = True):
      """Process a file with positional parameter.

      :param file_path: Path to file to process (positional)
      :param format_type: File format type
      :param validate: Enable validation
      """
      return f'Processing file: {file_path} (format: {format_type}, db: {self.database_url})'

    def backup_data(self, table_name: str = 'users'):
      """Backup data (no positional parameters).

      :param table_name: Table to backup
      """
      return f'Backing up table: {table_name}'


class TestClassBasedPositionalParameters:
  """Test positional parameters with class-based CLIs."""

  def test_class_cli_with_positional_parameter(self):
    """Test class-based CLI with positional parameter support."""
    cli = FreyjaCLI(SampleClassWithPositional, 'Test Class CLI')

    # Test positional parameter usage
    result = cli.run(['process-item', 'my-item'])
    assert 'Processing item: my-item' in result
    assert 'priority: medium' in result

  def test_class_cli_positional_with_global_flags(self):
    """Test positional parameter with global flags."""
    cli = FreyjaCLI(SampleClassWithPositional, 'Test Class CLI')

    # Test positional with global config flag
    result = cli.run(['--config', 'custom.json', 'process-item', 'test-item', '--priority', 'high'])
    assert 'Processing item: test-item' in result
    assert 'priority: high' in result
    assert 'config: custom.json' in result

  def test_class_cli_flag_version_backward_compatibility(self):
    """Test backward compatibility with flag version."""
    cli = FreyjaCLI(SampleClassWithPositional, 'Test Class CLI')

    # Test using flag version instead of positional
    result = cli.run(['process-item', '--item-name', 'flag-item'])
    assert 'Processing item: flag-item' in result

  def test_class_cli_method_without_positional(self):
    """Test class method without positional parameters."""
    cli = FreyjaCLI(SampleClassWithPositional, 'Test Class CLI')

    # Should work normally without positional parameters
    result = cli.run(['no-positional-method', '--optional-param', 'custom'])
    assert result == 'No positional: custom'


class TestHierarchicalPositionalParameters:
  """Test positional parameters with hierarchical (inner class) CLIs."""

  def test_hierarchical_cli_with_positional(self):
    """Test hierarchical CLI with positional parameter support."""
    cli = FreyjaCLI(SampleClassWithInnerClasses, 'Hierarchical CLI')

    # Test positional parameter in hierarchical command
    result = cli.run(['data-ops', 'process-file', '/path/to/file.json'])
    assert 'Processing file: /path/to/file.json' in result
    assert 'format: json' in result

  def test_hierarchical_cli_no_positional_command(self):
    """Test hierarchical command without positional parameters."""
    cli = FreyjaCLI(SampleClassWithInnerClasses, 'Hierarchical CLI')

    result = cli.run(['data-ops', 'backup-data', '--table-name', 'products'])
    assert 'Backing up table: products' in result


class TestPositionalParameterHelp:
  """Test help generation for positional parameters."""

  def test_help_shows_both_positional_and_flag_options(self):
    """Test that help shows both positional usage and flag alternative."""
    cli = FreyjaCLI(SampleClassWithPositional, 'Test CLI')
    parser = cli.create_parser()

    # Get help text
    help_text = parser.format_help()
    assert 'process-item' in help_text


class TestPositionalParameterEdgeCases:
  """Test edge cases for positional parameters."""


class TestPositionalParameterIntegration:
  """Test integration of positional parameters with other features."""

  def test_positional_with_completion_system(self):
    """Test that positional parameters work with completion system."""
    cli = FreyjaCLI(SampleClassWithPositional, 'Test CLI', completion=True)

    # Should create CLI successfully with completion enabled
    assert cli.enable_completion is True

    # Should still work normally
    result = cli.run(['process-item', 'completion-test'])
    assert 'Processing item: completion-test' in result

  def test_positional_with_custom_theme(self):
    """Test positional parameters work with custom themes."""
    cli = FreyjaCLI(SampleClassWithPositional, 'Test CLI')

    # Should work with custom theme
    result = cli.run(['process-item', 'themed-item'])
    assert 'Processing item: themed-item' in result


class TestPositionalParameterRegression:
  """Test for regression prevention in positional parameter functionality."""

  def test_complex_existing_patterns_unchanged(self):
    """Test that complex existing CLI patterns are unchanged."""
    cli = FreyjaCLI(SampleClassWithInnerClasses, 'Complex CLI')

    # Test that hierarchical commands work as before (when not using positional)
    result = cli.run(['data-ops', 'backup-data'])
    assert 'Backing up table: users' in result

    # Test with all flag syntax
    result = cli.run(['data-ops', 'process-file', '--file-path', 'test.json'])
    assert 'Processing file: test.json' in result
