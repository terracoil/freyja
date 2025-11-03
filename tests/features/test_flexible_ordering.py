"""Tests for flexible option ordering functionality."""

import pytest
from freyja import FreyjaCLI


class SampleClassForOrdering:
  """Sample class for flexible ordering tests."""

  def __init__(self, config_file: str = 'config.json', debug: bool = False, timeout: int = 30):
    """Initialize with global configuration options."""
    self.config_file = config_file
    self.debug = debug
    self.timeout = timeout

  def process_data(self, data: str = 'test', format_type: str = 'json', validate: bool = True):
    """Process data with various options.

    :param data: Data to process
    :param format_type: Data format
    :param validate: Enable validation
    """
    result = f'Processing: {data} (format: {format_type}, config: {self.config_file})'
    if self.debug:
      result += ' [DEBUG]'
    if validate:
      result += ' [VALIDATED]'
    return result

  def simple_action(self, message: str = 'hello'):
    """Simple action for testing.

    :param message: Message to display
    """
    return f'Action: {message} (timeout: {self.timeout})'


class SampleClassWithInnerClassOrdering:
  """Sample class with inner classes for hierarchical flexible ordering tests."""

  def __init__(self, base_config: str = 'base.json', log_level: str = 'INFO'):
    """Initialize with global options."""
    self.base_config = base_config
    self.log_level = log_level

  class DatabaseOps:
    """Database operations with sub-global options."""

    def __init__(self, connection_string: str = 'sqlite:///test.db', pool_size: int = 5):
      """Initialize database operations."""
      self.connection_string = connection_string
      self.pool_size = pool_size

    def query_data(self, table_name: str, limit: int = 100, order_by: str = 'id'):
      """Query data from table.

      :param table_name: Table to query
      :param limit: Result limit
      :param order_by: Order by field
      """
      return (
        f'Query {table_name}: limit={limit}, order={order_by}, '
        f'pool={self.pool_size}, conn={self.connection_string}'
      )

    def migrate_schema(self, version: str = 'latest'):
      """Migrate database schema.

      :param version: Target version
      """
      return f'Migrating to {version} (conn: {self.connection_string})'

  class FileOps:
    """File operations with different sub-global options."""

    def __init__(self, working_dir: str = './data', backup_enabled: bool = True):
      """Initialize file operations."""
      self.working_dir = working_dir
      self.backup_enabled = backup_enabled

    def process_file(self, filename: str, output_format: str = 'json'):
      """Process a file.

      :param filename: File to process
      :param output_format: Output format
      """
      backup_status = 'with backup' if self.backup_enabled else 'no backup'
      return f'Processing {filename} -> {output_format} in {self.working_dir} ({backup_status})'


class TestFlexibleOrderingClassBased:
  """Test flexible ordering with class-based CLIs."""

  def test_global_options_at_end_class(self):
    """Test global options at end for class CLI."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Class CLI')

    # Global config option at end
    result = cli.run(['process-data', '--data', 'test123', '--config-file', 'prod.json'])
    assert 'Processing: test123' in result
    assert 'config: prod.json' in result

  def test_global_options_mixed_with_command_options(self):
    """Test global options mixed with command options."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Class CLI')

    # Mix global and command options in various positions
    result = cli.run(
      [
        'process-data',
        '--debug',  # global option
        '--data',
        'mixed_test',  # command option
        '--timeout',
        '60',  # global option
        '--format-type',
        'xml',  # command option
      ]
    )
    assert 'Processing: mixed_test' in result
    assert 'format: xml' in result
    assert '[DEBUG]' in result

  def test_all_global_options_at_end(self):
    """Test multiple global options all at the end."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Class CLI')

    result = cli.run(
      [
        'simple-action',
        '--message',
        'test_message',
        '--debug',  # global
        '--timeout',
        '120',  # global
        '--config-file',
        'special.json',  # global
      ]
    )
    assert 'Action: test_message' in result
    assert 'timeout: 120' in result


class TestFlexibleOrderingWithPositional:
  """Test flexible ordering combined with positional parameters."""


class TestFlexibleOrderingErrorHandling:
  """Test error handling with flexible ordering."""

  def test_unknown_options_still_caught(self):
    """Test that unknown options are still caught with flexible ordering."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Test CLI')

    # Unknown option should still cause error regardless of position
    with pytest.raises(SystemExit):
      cli.run(['process-data', '--unknown-option', 'value'])

  # missing required 'text'

  def test_invalid_option_values_still_caught(self):
    """Test that invalid option values are still caught."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Test CLI')

    # Invalid integer value should still cause error
    with pytest.raises(SystemExit):
      cli.run(['process-data', '--timeout', 'not_a_number'])


class TestFlexibleOrderingCompatibility:
  """Test backward compatibility with existing CLI patterns."""

  def test_traditional_ordering_still_works(self):
    """Test that traditional option ordering still works perfectly."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Test CLI')

    # Traditional ordering: global -> command -> command options
    result = cli.run(
      [
        '--config-file',
        'traditional.json',
        '--debug',
        'process-data',
        '--data',
        'traditional_test',
        '--format-type',
        'yaml',
      ]
    )
    assert 'Processing: traditional_test' in result
    assert 'format: yaml' in result
    assert 'config: traditional.json' in result
    assert '[DEBUG]' in result

  def test_help_system_unaffected(self):
    """Test that help system works normally with flexible ordering."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Test CLI')
    parser = cli.create_parser()

    # Help should work normally
    help_text = parser.format_help()
    assert 'Test CLI' in help_text
    assert 'process-data' in help_text
    assert 'simple-action' in help_text

  def test_completion_system_unaffected(self):
    """Test that completion system works with flexible ordering."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Test CLI', completion=True)

    # Should create successfully with completion
    assert cli.enable_completion is True

    # Should still work normally with flexible ordering
    result = cli.run(['simple-action', '--config-file', 'comp.json'])
    assert 'Action: hello' in result


class TestFlexibleOrderingEdgeCases:
  """Test edge cases for flexible ordering."""

  def test_option_value_pairs_stay_together(self):
    """Test that option-value pairs are kept together during reordering."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Test CLI')

    # Options with values should stay together
    result = cli.run(
      [
        'process-data',
        '--data',
        'edge_case_data',  # command option-value pair
        '--config-file',
        'edge.json',  # global option-value pair
        '--format-type',
        'csv',  # command option-value pair
        '--timeout',
        '45',  # global option-value pair
      ]
    )
    assert 'Processing: edge_case_data' in result
    assert 'format: csv' in result
    assert 'config: edge.json' in result

  def test_boolean_flags_flexible_positioning(self):
    """Test boolean flags work in flexible positions."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Test CLI')

    # Boolean flags at various positions
    result = cli.run(
      [
        'process-data',
        '--debug',  # global boolean flag
        '--data',
        'bool_test',
        '--validate',  # command boolean flag at end
      ]
    )
    assert 'Processing: bool_test' in result
    assert '[DEBUG]' in result
    assert '[VALIDATED]' in result

  def test_empty_argument_list_handling(self):
    """Test handling of empty or minimal argument lists."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Test CLI')

    # Should work with minimal arguments
    result = cli.run(['simple-action'])
    assert 'Action: hello' in result
    assert 'timeout: 30' in result

  def test_only_global_options(self):
    """Test commands with only global options work."""
    cli = FreyjaCLI(SampleClassForOrdering, 'Test CLI')

    # Command with only global options
    result = cli.run(['simple-action', '--config-file', 'global_only.json', '--debug'])
    assert 'Action: hello' in result


class TestFlexibleOrderingComplexScenarios:
  """Test complex real-world scenarios with flexible ordering."""
