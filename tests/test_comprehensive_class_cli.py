#!/usr/bin/env python
"""Comprehensive tests for class-based CLI (both inner class and traditional patterns)."""

import enum
import sys
from pathlib import Path
from typing import List, Optional
import pytest
from unittest.mock import patch

from auto_cli.cli import CLI


class ProcessMode(enum.Enum):
    """Test processing modes."""
    FAST = "fast"
    THOROUGH = "thorough"
    BALANCED = "balanced"


class OutputFormat(enum.Enum):
    """Test output formats."""
    JSON = "json"
    CSV = "csv"
    XML = "xml"


# ==================== INNER CLASS PATTERN TESTS ====================

class InnerClassCLI:
    """Test CLI using inner class pattern."""
    
    def __init__(self, config_file: str = "test.json", verbose: bool = False):
        """Initialize with global arguments.
        
        :param config_file: Configuration file path
        :param verbose: Enable verbose output
        """
        self.config_file = config_file
        self.verbose = verbose
        self.state = {"operations": []}
    
    class DataOperations:
        """Data processing operations."""
        
        def __init__(self, work_dir: str = "./data", backup: bool = True):
            """Initialize data operations.
            
            :param work_dir: Working directory for operations
            :param backup: Create backup copies
            """
            self.work_dir = work_dir
            self.backup = backup
        
        def process(self, input_file: Path, mode: ProcessMode = ProcessMode.BALANCED, 
                   dry_run: bool = False) -> dict:
            """Process a data file.
            
            :param input_file: Input file to process
            :param mode: Processing mode
            :param dry_run: Show what would be done without executing
            """
            return {
                "input_file": str(input_file),
                "mode": mode.value,
                "dry_run": dry_run,
                "work_dir": self.work_dir,
                "backup": self.backup
            }
        
        def batch_process(self, pattern: str, max_files: int = 100, 
                         parallel: bool = False) -> dict:
            """Process multiple files.
            
            :param pattern: File pattern to match
            :param max_files: Maximum number of files
            :param parallel: Enable parallel processing
            """
            return {
                "pattern": pattern,
                "max_files": max_files,
                "parallel": parallel,
                "work_dir": self.work_dir,
                "backup": self.backup
            }
    
    class ExportOperations:
        """Export operations."""
        
        def __init__(self, output_dir: str = "./exports"):
            """Initialize export operations.
            
            :param output_dir: Output directory for exports
            """
            self.output_dir = output_dir
        
        def export_data(self, format: OutputFormat = OutputFormat.JSON, 
                       compress: bool = False) -> dict:
            """Export data to specified format.
            
            :param format: Output format
            :param compress: Compress output
            """
            return {
                "format": format.value,
                "compress": compress,
                "output_dir": self.output_dir
            }
    
    class ConfigManagement:
        """Configuration management without sub-global arguments."""
        
        def set_mode(self, mode: ProcessMode) -> dict:
            """Set default processing mode.
            
            :param mode: Processing mode to set
            """
            return {"mode": mode.value}
        
        def show_config(self, detailed: bool = False) -> dict:
            """Show configuration.
            
            :param detailed: Show detailed configuration
            """
            return {"detailed": detailed}


# ==================== TRADITIONAL PATTERN TESTS ====================

class TraditionalCLI:
    """Test CLI using traditional dunder pattern."""
    
    def __init__(self):
        """Initialize CLI."""
        self.state = {"operations": []}
    
    def simple_command(self, name: str, count: int = 5) -> dict:
        """A simple flat command.
        
        :param name: Name parameter
        :param count: Count parameter
        """
        return {"name": name, "count": count}
    
    def data__process(self, input_file: Path, mode: ProcessMode = ProcessMode.BALANCED) -> dict:
        """Process data file.
        
        :param input_file: Input file to process
        :param mode: Processing mode
        """
        return {"input_file": str(input_file), "mode": mode.value}
    
    def data__export(self, format: OutputFormat = OutputFormat.JSON, 
                    output_file: Optional[Path] = None) -> dict:
        """Export data.
        
        :param format: Export format
        :param output_file: Output file path
        """
        return {
            "format": format.value,
            "output_file": str(output_file) if output_file else None
        }
    
    def config__set(self, key: str, value: str) -> dict:
        """Set configuration value.
        
        :param key: Configuration key
        :param value: Configuration value
        """
        return {"key": key, "value": value}
    
    def config__get(self, key: str, default: str = "none") -> dict:
        """Get configuration value.
        
        :param key: Configuration key
        :param default: Default value if key not found
        """
        return {"key": key, "default": default}


# ==================== INNER CLASS PATTERN TESTS ====================

class TestInnerClassCLI:
    """Test inner class CLI pattern."""
    
    def test_inner_class_discovery(self):
        """Test that inner classes are discovered correctly."""
        cli = CLI(InnerClassCLI)
        
        # Should detect inner class pattern
        assert hasattr(cli, 'use_inner_class_pattern')
        assert cli.use_inner_class_pattern
        assert hasattr(cli, 'inner_classes')
        
        # Should have discovered inner classes
        inner_class_names = set(cli.inner_classes.keys())
        expected_names = {'DataOperations', 'ExportOperations', 'ConfigManagement'}
        assert inner_class_names == expected_names
    
    def test_command_structure(self):
        """Test command structure generation."""
        cli = CLI(InnerClassCLI)
        
        # Should have hierarchical commands
        expected_commands = {
            'data-operations', 'export-operations', 'config-management'
        }
        
        # Check if commands exist (may also include cli command from theme tuner)
        for cmd in expected_commands:
            assert cmd in cli.commands
            assert cli.commands[cmd]['type'] == 'group'
    
    def test_global_arguments_parsing(self):
        """Test global arguments from main class constructor."""
        cli = CLI(InnerClassCLI)
        parser = cli.create_parser()
        
        # Test global arguments exist
        args = parser.parse_args([
            '--global-config-file', 'prod.json',
            '--global-verbose',
            'data-operations',
            'process',
            '--input-file', 'test.txt'
        ])
        
        assert hasattr(args, '_global_config_file')
        assert args._global_config_file == 'prod.json'
        assert hasattr(args, '_global_verbose')
        assert args._global_verbose is True
    
    def test_subglobal_arguments_parsing(self):
        """Test sub-global arguments from inner class constructor."""
        cli = CLI(InnerClassCLI)
        parser = cli.create_parser()
        
        # Test sub-global arguments exist
        args = parser.parse_args([
            'data-operations',
            '--work-dir', '/tmp/data',
            '--backup',
            'process',
            '--input-file', 'test.txt'
        ])
        
        assert hasattr(args, '_subglobal_data-operations_work_dir')
        assert getattr(args, '_subglobal_data-operations_work_dir') == '/tmp/data'
        assert hasattr(args, '_subglobal_data-operations_backup')
        assert getattr(args, '_subglobal_data-operations_backup') is True
    
    def test_command_execution_with_all_arguments(self):
        """Test command execution with global, sub-global, and command arguments."""
        cli = CLI(InnerClassCLI)
        
        # Mock sys.argv for testing
        test_args = [
            '--global-config-file', 'test.json',
            '--global-verbose',
            'data-operations',
            '--work-dir', '/tmp/test',
            '--backup',
            'process',
            '--input-file', 'data.txt',
            '--mode', 'FAST',
            '--dry-run'
        ]
        
        result = cli.run(test_args)
        
        # Verify all argument levels were passed correctly
        assert result['input_file'] == 'data.txt'
        assert result['mode'] == 'fast'
        assert result['dry_run'] is True
        assert result['work_dir'] == '/tmp/test'
        assert result['backup'] is True
    
    def test_command_group_without_subglobal_args(self):
        """Test command group without sub-global arguments."""
        cli = CLI(InnerClassCLI)
        
        test_args = ['config-management', 'set-mode', '--mode', 'THOROUGH']
        result = cli.run(test_args)
        
        assert result['mode'] == 'thorough'
    
    def test_enum_parameter_handling(self):
        """Test enum parameters are handled correctly."""
        cli = CLI(InnerClassCLI)
        
        test_args = ['export-operations', 'export-data', '--format', 'XML', '--compress']
        result = cli.run(test_args)
        
        assert result['format'] == 'xml'
        assert result['compress'] is True
    
    def test_help_display(self):
        """Test help display at various levels."""
        cli = CLI(InnerClassCLI)
        parser = cli.create_parser()
        
        # Main help should show command groups
        help_text = parser.format_help()
        assert 'data-operations' in help_text
        assert 'export-operations' in help_text
        assert 'config-management' in help_text
        
        # Should show global arguments
        assert '--global-config-file' in help_text
        assert '--global-verbose' in help_text


# ==================== TRADITIONAL PATTERN TESTS ====================

class TestTraditionalCLI:
    """Test traditional dunder CLI pattern."""
    
    def test_traditional_pattern_detection(self):
        """Test that traditional pattern is detected correctly."""
        cli = CLI(TraditionalCLI)
        
        # Should not use inner class pattern
        assert not hasattr(cli, 'use_inner_class_pattern') or not cli.use_inner_class_pattern
    
    def test_dunder_command_structure(self):
        """Test dunder command structure generation."""
        cli = CLI(TraditionalCLI)
        
        # Should have flat and hierarchical commands
        assert 'simple-command' in cli.commands
        assert cli.commands['simple-command']['type'] == 'flat'
        
        assert 'data' in cli.commands
        assert cli.commands['data']['type'] == 'group'
        assert 'config' in cli.commands
        assert cli.commands['config']['type'] == 'group'
    
    def test_flat_command_execution(self):
        """Test flat command execution."""
        cli = CLI(TraditionalCLI)
        
        test_args = ['simple-command', '--name', 'test', '--count', '10']
        result = cli.run(test_args)
        
        assert result['name'] == 'test'
        assert result['count'] == 10
    
    def test_hierarchical_command_execution(self):
        """Test hierarchical command execution."""
        cli = CLI(TraditionalCLI)
        
        test_args = ['data', 'process', '--input-file', 'test.txt', '--mode', 'FAST']
        result = cli.run(test_args)
        
        assert result['input_file'] == 'test.txt'
        assert result['mode'] == 'fast'
    
    def test_optional_parameters(self):
        """Test optional parameters with defaults."""
        cli = CLI(TraditionalCLI)
        
        # Test with optional parameter
        test_args = ['data', 'export', '--format', 'CSV', '--output-file', 'output.csv']
        result = cli.run(test_args)
        
        assert result['format'] == 'csv'
        assert result['output_file'] == 'output.csv'
        
        # Test without optional parameter
        test_args = ['data', 'export', '--format', 'JSON']
        result = cli.run(test_args)
        
        assert result['format'] == 'json'
        assert result['output_file'] is None


# ==================== COMPATIBILITY TESTS ====================

class TestPatternCompatibility:
    """Test compatibility between patterns."""
    
    def test_both_patterns_coexist(self):
        """Test that both patterns can coexist in the same codebase."""
        # Both should work without interference
        inner_cli = CLI(InnerClassCLI)
        traditional_cli = CLI(TraditionalCLI)
        
        # Inner class CLI should use new pattern
        assert hasattr(inner_cli, 'use_inner_class_pattern')
        assert inner_cli.use_inner_class_pattern
        
        # Traditional CLI should use old pattern
        assert not hasattr(traditional_cli, 'use_inner_class_pattern') or not traditional_cli.use_inner_class_pattern
    
    def test_same_interface_different_implementations(self):
        """Test same CLI interface with different internal implementations."""
        inner_cli = CLI(InnerClassCLI)
        traditional_cli = CLI(TraditionalCLI)
        
        # Both should have the same external interface
        assert hasattr(inner_cli, 'run')
        assert hasattr(traditional_cli, 'run')
        assert hasattr(inner_cli, 'create_parser')
        assert hasattr(traditional_cli, 'create_parser')


# ==================== ERROR HANDLING TESTS ====================

class TestErrorHandling:
    """Test error handling for class-based CLIs."""
    
    def test_missing_required_argument(self):
        """Test handling of missing required arguments."""
        cli = CLI(InnerClassCLI)
        
        # Should raise SystemExit when required argument is missing
        with pytest.raises(SystemExit):
            cli.run(['data-operations', 'process'])  # Missing --input-file
    
    def test_invalid_enum_value(self):
        """Test handling of invalid enum values."""
        cli = CLI(InnerClassCLI)
        
        # Should raise SystemExit when invalid enum value is provided
        with pytest.raises(SystemExit):
            cli.run(['data-operations', 'process', '--input-file', 'test.txt', '--mode', 'INVALID'])
    
    def test_invalid_command(self):
        """Test handling of invalid commands."""
        cli = CLI(InnerClassCLI)
        
        # Should raise SystemExit when invalid command is provided
        with pytest.raises(SystemExit):
            cli.run(['invalid-command'])


# ==================== TYPE ANNOTATION TESTS ====================

class TestTypeAnnotations:
    """Test various type annotations work correctly."""
    
    def test_path_type_annotation(self):
        """Test Path type annotations."""
        cli = CLI(InnerClassCLI)
        
        test_args = ['data-operations', 'process', '--input-file', '/path/to/file.txt']
        result = cli.run(test_args)
        
        # Should handle Path type correctly
        assert result['input_file'] == '/path/to/file.txt'
    
    def test_optional_type_annotation(self):
        """Test Optional type annotations."""
        cli = CLI(TraditionalCLI)
        
        # Test with value
        test_args = ['data', 'export', '--format', 'JSON', '--output-file', 'out.json']
        result = cli.run(test_args)
        assert result['output_file'] == 'out.json'
        
        # Test without value (should be None)
        test_args = ['data', 'export', '--format', 'JSON']
        result = cli.run(test_args)
        assert result['output_file'] is None
    
    def test_boolean_type_annotation(self):
        """Test boolean type annotations."""
        cli = CLI(InnerClassCLI)
        
        # Test boolean flag
        test_args = ['data-operations', 'batch-process', '--pattern', '*.txt', '--parallel']
        result = cli.run(test_args)
        assert result['parallel'] is True
        
        # Test without boolean flag
        test_args = ['data-operations', 'batch-process', '--pattern', '*.txt']
        result = cli.run(test_args)
        assert result['parallel'] is False


if __name__ == '__main__':
    pytest.main([__file__])