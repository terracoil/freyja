"""Test suite for multi-class CLI functionality."""

import pytest
from unittest.mock import patch

from auto_cli.cli import CLI
from auto_cli.enums import TargetMode
from auto_cli.command.multi_class_handler import MultiClassHandler


class MockDataProcessor:
    """Mock data processor for testing."""

    def __init__(self, config_file: str = "config.json", verbose: bool = False):
        self.config_file = config_file
        self.verbose = verbose

    def process_data(self, input_file: str, format: str = "json") -> str:
        """Process data file."""
        return f"Processed {input_file} as {format} with config {self.config_file}"

    class FileOperations:
        """File operations for data processor."""

        def __init__(self, main_instance, work_dir: str = "./data"):
            self.main_instance = main_instance
            self.work_dir = work_dir

        def cleanup(self, pattern: str = "*") -> str:
            """Clean up files."""
            return f"Cleaned {pattern} in {self.work_dir}"


class MockFileManager:
    """Mock file manager for testing."""

    def __init__(self, base_path: str = "/tmp"):
        self.base_path = base_path

    def list_files(self, directory: str = ".") -> str:
        """List files in directory."""
        return f"Listed files in {directory} from {self.base_path}"

    def process_data(self, input_file: str, format: str = "xml") -> str:
        """Process data file (collision with MockDataProcessor)."""
        return f"FileManager processed {input_file} as {format}"


class MockReportGenerator:
    """Mock report generator for testing."""

    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = output_dir

    def generate_report(self, report_type: str = "summary") -> str:
        """Generate a report."""
        return f"Generated {report_type} report in {output_dir}"


class TestMultiClassHandler:
    """Test MultiClassHandler collision detection and command organization."""

    def test_collision_detection(self):
        """Test collision detection between classes with same command names."""
        handler = MultiClassHandler()

        # Track commands that will collide (same exact command name)
        handler.track_command("process-data", MockDataProcessor)
        handler.track_command("process-data", MockFileManager)

        # Should detect collision
        assert handler.has_collisions()
        collisions = handler.detect_collisions()
        assert len(collisions) == 1
        assert collisions[0][0] == "process-data"  # Command name that has collision
        assert len(collisions[0][1]) == 2

    def test_no_collision_different_names(self):
        """Test no collision when method names are different."""
        handler = MultiClassHandler()

        handler.track_command("process-data", MockDataProcessor)
        handler.track_command("list-files", MockFileManager)

        assert not handler.has_collisions()

    def test_command_ordering(self):
        """Test command ordering preserves class order then alphabetical."""
        handler = MultiClassHandler()

        # Track commands out of order using clean names
        handler.track_command("list-files", MockFileManager)
        handler.track_command("process-data", MockDataProcessor)
        handler.track_command("analyze", MockDataProcessor)
        handler.track_command("cleanup", MockFileManager)

        class_order = [MockDataProcessor, MockFileManager]
        ordered = handler.get_ordered_commands(class_order)

        # Should be: DataProcessor commands first (alphabetical), then FileManager commands (alphabetical)
        expected = [
            "analyze",
            "process-data",
            "cleanup",
            "list-files"
        ]
        assert ordered == expected

    def test_validation_success(self):
        """Test successful validation with no collisions."""
        handler = MultiClassHandler()

        # Should not raise exception
        handler.validate_classes([MockDataProcessor, MockReportGenerator])

    def test_validation_failure_with_collisions(self):
        """Test validation failure when collisions exist."""
        handler = MultiClassHandler()

        # Should raise ValueError due to process_data collision
        with pytest.raises(ValueError) as exc_info:
            handler.validate_classes([MockDataProcessor, MockFileManager])

        assert "Command name collisions detected" in str(exc_info.value)
        assert "process-data" in str(exc_info.value)


class TestMultiClassCLI:
    """Test multi-class CLI functionality."""

    def test_single_class_in_list(self):
        """Test single class in list behaves like regular class mode."""
        cli = CLI([MockDataProcessor])

        assert cli.target_mode == TargetMode.CLASS
        assert cli.target_class == MockDataProcessor
        assert cli.target_classes is None
        assert "process-data" in cli.commands

    def test_multi_class_mode_detection(self):
        """Test multi-class mode is detected correctly."""
        cli = CLI([MockDataProcessor, MockReportGenerator])

        assert cli.target_mode == TargetMode.MULTI_CLASS
        assert cli.target_class is None
        assert cli.target_classes == [MockDataProcessor, MockReportGenerator]

    def test_collision_detection_with_clean_names(self):
        """Test collision detection when classes have same method names."""
        # Should raise exception since both classes have process_data method
        with pytest.raises(ValueError) as exc_info:
            CLI([MockDataProcessor, MockFileManager])

        assert "Command name collisions detected" in str(exc_info.value)
        assert "process-data" in str(exc_info.value)

    def test_multi_class_command_structure(self):
        """Test command structure for multi-class CLI."""
        cli = CLI([MockDataProcessor, MockReportGenerator])

        # Should have commands from both classes
        commands = cli.commands

        # DataProcessor commands (clean names)
        assert "process-data" in commands

        # ReportGenerator commands (clean names)
        assert "generate-report" in commands

        # Commands should be properly structured
        dp_cmd = commands["process-data"]
        assert dp_cmd['type'] == 'command'
        assert dp_cmd['original_name'] == 'process_data'

    def test_multi_class_with_inner_classes(self):
        """Test multi-class CLI with inner classes."""
        cli = CLI([MockDataProcessor])

        # Should detect inner class pattern
        assert hasattr(cli, 'use_inner_class_pattern')
        assert cli.use_inner_class_pattern

        # Should have both direct methods and inner class methods
        commands = cli.commands

        # Direct method should be present (single class doesn't need class prefix)
        assert "process-data" in commands

        # Inner class group should be present
        assert "file-operations" in commands
        inner_group = commands["file-operations"]
        assert inner_group['type'] == 'group'
        assert 'cleanup' in inner_group['commands']

    def test_multi_class_title_generation(self):
        """Test title generation for multi-class CLI."""
        # Two classes - title should come from the last class (MockReportGenerator)
        cli2 = CLI([MockDataProcessor, MockReportGenerator])
        assert "Mock report generator for testing" in cli2.title

        # Single class (should use class name or docstring)
        cli1 = CLI([MockDataProcessor])
        assert "MockDataProcessor" in cli1.title or "mock data processor" in cli1.title.lower()

    @patch('sys.argv', ['test_cli', 'process-data', '--input-file', 'test.txt'])
    def test_multi_class_command_execution(self):
        """Test executing commands in multi-class mode."""
        cli = CLI([MockDataProcessor, MockReportGenerator])

        # In multi-class mode, command_executor should be None and we should have command_executors list
        assert cli.command_executor is None
        assert cli.command_executors is not None
        assert len(cli.command_executors) == 2

        # For now, just test that the CLI structure is correct for multi-class mode
        assert cli.target_mode.value == 'multi_class'

    def test_backward_compatibility_single_class(self):
        """Test backward compatibility with single class (non-list)."""
        cli = CLI(MockDataProcessor)

        assert cli.target_mode == TargetMode.CLASS
        assert cli.target_class == MockDataProcessor
        assert cli.target_classes is None

    def test_empty_list_validation(self):
        """Test validation of empty class list."""
        with pytest.raises((ValueError, IndexError)):
            CLI([])

    def test_invalid_list_items(self):
        """Test validation of list with non-class items."""
        with pytest.raises(ValueError) as exc_info:
            CLI([MockDataProcessor, "not_a_class"])

        assert "must be classes" in str(exc_info.value)


class TestCommandExecutorMultiClass:
    """Test CommandExecutor multi-class functionality."""

    def test_multi_class_executor_initialization(self):
        """Test that multi-class CLIs initialize command executors correctly."""
        cli = CLI([MockDataProcessor, MockReportGenerator])

        # Should have multiple executors (one per class)
        assert cli.command_executors is not None
        assert len(cli.command_executors) == 2
        assert cli.command_executor is None

        # Each executor should be properly initialized
        for executor in cli.command_executors:
            assert executor.target_class is not None

    def test_single_class_executor_compatibility(self):
        """Test that single class mode still uses single command executor."""
        cli = CLI(MockDataProcessor)

        # Should have single executor
        assert cli.command_executor is not None
        assert cli.command_executors is None
        assert cli.command_executor.target_class == MockDataProcessor


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
