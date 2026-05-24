"""Integration tests for both positional parameters and flexible ordering features."""

from pathlib import Path

import pytest
from freyja import FreyjaCLI


def integration_function_simple(
  required_text: str, format_type: str = 'json', verbose: bool = False
):
  """Integration function with positional and optional parameters.

  :param required_text: Required text parameter (becomes positional)
  :param format_type: Output format type
  :param verbose: Enable verbose output
  """
  result = f'Processing: {required_text} (format: {format_type})'
  if verbose:
    result += ' [VERBOSE]'
  return result


def integration_function_complex(
  input_file: str,
  output_format: str = 'json',
  batch_size: int = 100,
  validate: bool = True,
  debug: bool = False,
):
  """Complex integration function with multiple parameter types.

  :param input_file: Input file path (becomes positional)
  :param output_format: Output format
  :param batch_size: Processing batch size
  :param validate: Enable validation
  :param debug: Enable debug mode
  """
  result = f'Processing file: {input_file} -> {output_format} (batch: {batch_size})'
  if validate:
    result += ' [VALIDATED]'
  if debug:
    result += ' [DEBUG]'
  return result


def integration_function_path_types(
  source_path: Path, destination: str = 'output/', create_backup: bool = False
):
  """Integration function with Path types and positional parameters.

  :param source_path: Source file path (becomes positional)
  :param destination: Destination directory
  :param create_backup: Create backup copy
  """
  result = f'Copying {source_path} to {destination}'
  if create_backup:
    result += ' (with backup)'
  return result


class IntegrationClassSimple:
  """Simple integration class for testing both features together."""

  def __init__(self, config_file: str = 'config.json', log_level: str = 'INFO'):
    """Initialize with global configuration."""
    self.config_file = config_file
    self.log_level = log_level

  def process_item(self, item_id: str, priority: str = 'medium', urgent: bool = False):
    """Process an item with positional parameter.

    :param item_id: ID of item to process (becomes positional)
    :param priority: Processing priority
    :param urgent: Mark as urgent
    """
    result = (
      f'Processing item {item_id} (priority: {priority}, '
      f'config: {self.config_file}, log: {self.log_level})'
    )
    if urgent:
      result += ' [URGENT]'
    return result

  def batch_process(self, item_count: int = 10, format_type: str = 'json'):
    """Batch processing without positional parameters.

    :param item_count: Number of items to process
    :param format_type: Output format
    """
    return f'Batch processing {item_count} items as {format_type} (config: {self.config_file})'


class IntegrationClassHierarchical:
  """Hierarchical integration class for complex testing scenarios."""

  def __init__(self, base_config: str = 'base.json', environment: str = 'development'):
    """Initialize with global settings."""
    self.base_config = base_config
    self.environment = environment

  class DataProcessing:
    """Data processing operations with sub-global settings."""

    def __init__(self, workspace: str = './data', parallel: bool = True):
      """Initialize data processing."""
      self.workspace = workspace
      self.parallel = parallel

    def transform_data(
      self, dataset_name: str, output_format: str = 'parquet', chunk_size: int = 1000
    ):
      """Transform dataset with positional parameter.

      :param dataset_name: Name of dataset to transform (becomes positional)
      :param output_format: Output format
      :param chunk_size: Processing chunk size
      """
      parallel_info = 'parallel' if self.parallel else 'sequential'
      return (
        f"Transforming dataset '{dataset_name}' -> {output_format} "
        f'(chunks: {chunk_size}, mode: {parallel_info}, workspace: {self.workspace})'
      )

    def validate_schema(self, schema_file: str, strict: bool = True):
      """Validate schema with positional parameter.

      :param schema_file: Schema file to validate (becomes positional)
      :param strict: Use strict validation
      """
      mode = 'strict' if strict else 'lenient'
      return f'Validating schema: {schema_file} ({mode} mode, workspace: {self.workspace})'

  class FileOperations:
    """File operations with different sub-global settings."""

    def __init__(
      self,
      temp_dir: str = '/tmp',  # noqa: S108 # acceptable in tests
      compression: bool = False,
    ):
      """Initialize file operations."""
      self.temp_dir = temp_dir
      self.compression = compression

    def merge_files(
      self, output_filename: str, input_pattern: str = '*.csv', preserve_headers: bool = True
    ):
      """Merge files with positional parameter.

      :param output_filename: Output file name (becomes positional)
      :param input_pattern: Input file pattern
      :param preserve_headers: Preserve CSV headers
      """
      compression_info = 'with compression' if self.compression else 'without compression'
      headers_info = 'preserving headers' if preserve_headers else 'no headers'
      return (
        f'Merging {input_pattern} -> {output_filename} '
        f'({headers_info}, {compression_info}, temp: {self.temp_dir})'
      )


class TestClassBasedIntegration:
  """Test integration with class-based CLIs."""

  def test_class_positional_with_flexible_global_options(self):
    """Test class CLI with positional parameters and flexible global options."""
    cli = FreyjaCLI(IntegrationClassSimple, 'Class Integration CLI')

    # Positional parameter with global options in various positions
    result = cli.run(
      [
        'process-item',
        'ITEM-123',  # positional parameter
        '--log-level',
        'DEBUG',  # global option after positional
        '--priority',
        'high',  # command option
        '--config-file',
        'prod.json',  # global option at end
      ]
    )
    assert 'Processing item ITEM-123' in result
    assert 'priority: high' in result
    assert 'config: prod.json' in result
    assert 'log: DEBUG' in result

  def test_class_mixed_methods_with_flexible_ordering(self):
    """Test class with both positional and non-positional methods with flexible ordering."""
    cli = FreyjaCLI(IntegrationClassSimple, 'Mixed Methods CLI')

    # Method with positional parameter
    result1 = cli.run(
      [
        'process-item',
        'ITEM-456',
        '--config-file',
        'test.json',  # global option mixed in
        '--urgent',  # command boolean flag
      ]
    )
    assert 'Processing item ITEM-456' in result1
    assert 'config: test.json' in result1
    assert '[URGENT]' in result1

    # Method without positional parameters
    result2 = cli.run(
      [
        'batch-process',
        '--log-level',
        'WARN',  # global option
        '--item-count',
        '50',  # command option
        '--format-type',
        'xml',  # command option
      ]
    )
    assert 'Batch processing 50 items as xml' in result2


class TestIntegrationErrorHandling:
  """Test error handling with both integration features."""

  def test_unknown_options_with_positional_parameters(self):
    """Test unknown option errors with positional parameters."""
    cli = FreyjaCLI(IntegrationClassSimple, 'Error Test CLI')

    # Unknown option should cause error regardless of positional parameter
    with pytest.raises(SystemExit):
      cli.run(
        [
          'process-item',
          'ITEM-789',  # valid positional parameter
          '--unknown-option',
          'value',  # invalid option
        ]
      )


class TestIntegrationPerformance:
  """Test performance aspects of integration features."""

  def test_minimal_command_integration(self):
    """Test minimal commands still work with integration features."""
    cli = FreyjaCLI(IntegrationClassSimple, 'Minimal Test CLI')

    # Minimal command should work
    result = cli.run(['batch-process'])
    assert 'Batch processing 10 items as json' in result
    assert 'config: config.json' in result  # default values


class TestIntegrationBackwardCompatibility:
  """Test backward compatibility with existing CLI patterns."""

  def test_help_system_with_integration_features(self):
    """Test that help system works correctly with integration features."""
    cli = FreyjaCLI(IntegrationClassHierarchical, 'Help Test CLI')
    parser = cli.create_parser()

    # Help should work normally
    help_text = parser.format_help()
    assert 'Help Test CLI' in help_text
    assert 'data-processing' in help_text
    assert 'file-operations' in help_text

  def test_completion_system_with_integration_features(self):
    """Test that completion system works with integration features."""
    cli = FreyjaCLI(IntegrationClassSimple, 'Completion Test CLI', completion=True)

    # Should create successfully
    assert cli.enable_completion is True

    # Should work with positional parameters and flexible ordering
    result = cli.run(['process-item', 'COMP-123', '--config-file', 'completion.json'])
    assert 'Processing item COMP-123' in result
    assert 'config: completion.json' in result


class TestIntegrationRealWorldScenarios:
  """Test realistic real-world scenarios combining both features."""

  def test_admin_tool_scenario(self):
    """Test realistic system administration tool scenario."""
    cli = FreyjaCLI(IntegrationClassSimple, 'Admin Tool CLI')

    # Realistic admin task with mixed option positioning
    result = cli.run(
      [
        'process-item',
        'TICKET-2024-001',  # ticket/item ID (positional)
        '--log-level',
        'DEBUG',  # global logging for troubleshooting
        '--config-file',
        'admin.conf',  # global config file
        '--priority',
        'critical',  # command-specific priority
        '--urgent',  # command-specific urgency flag
      ]
    )
    assert 'Processing item TICKET-2024-001' in result
    assert 'priority: critical' in result
    assert 'config: admin.conf' in result
    assert 'log: DEBUG' in result
    assert '[URGENT]' in result
