#!/usr/bin/env python
"""Multi-class CLI example demonstrating enhanced freyja functionality.

This example shows how to create a CLI from multiple classes, with proper
collision detection, command ordering, and System class integration."""

import enum
import sys
from pathlib import Path
from typing import List

from src.cli import CLI
from src.command.system import System


class ProcessingMode(enum.Enum):

"""Processing modes for data operations."""
    FAST = "fast"
    THOROUGH = "thorough"
    BALANCED = "balanced"


class OutputFormat(enum.Enum):
    """Supported output formats."""
    JSON = "json"
    CSV = "csv"
    XML = "xml"


class DataProcessor:
    """Enhanced data processing utility with comprehensive operations.

    Provides data processing capabilities with configurable settings
    and hierarchical command organization through inner classes."""

    def __init__(self, config_file: str = "data_config.json", debug: bool = False):
        """Initialize data processor with global settings.

        :param config_file: Configuration file for data processing settings
        :param debug: Enable debug mode for detailed logging"""
        self.config_file = config_file
        self.debug = debug
        self.processed_count = 0

        if self.debug:
            print(f"🔧 DataProcessor initialized with config: {self.config_file}")

    def quick_process(self, input_file: str, output_format: OutputFormat = OutputFormat.JSON) -> None:
        """Quick data processing for simple tasks.

        :param input_file: Input file to process
        :param output_format: Output format for processed data"""
        print(f"⚡ Quick processing: {input_file} -> {output_format.value}")
        print(f"Config: {self.config_file}, Debug: {self.debug}")
        self.processed_count += 1

    class BatchOperations:
        """Batch processing operations for large datasets."""

        def __init__(self, main_instance, work_dir: str = "./batch_data", max_workers: int = 4):
            """Initialize batch operations.

            :param main_instance: Main DataProcessor instance
            :param work_dir: Working directory for batch operations
            :param max_workers: Maximum number of parallel workers"""
            self.main_instance = main_instance
            self.work_dir = work_dir
            self.max_workers = max_workers

        def process_directory(self, directory: Path, pattern: str = "*.txt",
                            mode: ProcessingMode = ProcessingMode.BALANCED) -> None:
            """Process all files in a directory matching pattern.

            :param directory: Directory containing files to process
            :param pattern: File pattern to match
            :param mode: Processing mode for performance tuning"""
            print(f"📁 Batch processing directory: {directory}")
            print(f"Pattern: {pattern}, Mode: {mode.value}")
            print(f"Workers: {self.max_workers}, Work dir: {self.work_dir}")
            print(f"Using config: {self.main_instance.config_file}")

        def parallel_process(self, file_list: List[str], chunk_size: int = 10) -> None:
            """Process files in parallel chunks.

            :param file_list: List of file paths to process
            :param chunk_size: Number of files per processing chunk"""
            print(f"⚡ Parallel processing {len(file_list)} files in chunks of {chunk_size}")
            print(f"Workers: {self.max_workers}")

    class ValidationOperations:
        """Data validation and quality assurance operations."""

        def __init__(self, main_instance, strict_mode: bool = True):
            """Initialize validation operations.

            :param main_instance: Main DataProcessor instance
            :param strict_mode: Enable strict validation rules"""
            self.main_instance = main_instance
            self.strict_mode = strict_mode

        def validate_schema(self, schema_file: str, data_file: str) -> None:
            """Validate data file against schema.

            :param schema_file: Path to schema definition file
            :param data_file: Path to data file to validate"""
            mode = "strict" if self.strict_mode else "permissive"
            print(f"✅ Validating {data_file} against {schema_file} ({mode} mode)")

        def check_quality(self, data_file: str, threshold: float = 0.95) -> None:
            """Check data quality metrics.

            :param data_file: Path to data file to check
            :param threshold: Quality threshold (0.0 to 1.0)"""
            print(f"🔍 Checking quality of {data_file} (threshold: {threshold})")
            print(f"Strict mode: {self.strict_mode}")


class FileManager:
    """Advanced file management utility with comprehensive operations.

    Handles file system operations, organization, and maintenance tasks
    with configurable settings and safety features."""

    def __init__(self, base_path: str = "./files", backup_enabled: bool = True):
        """Initialize file manager with base settings.

        :param base_path: Base directory for file operations
        :param backup_enabled: Enable automatic backups before operations"""
        self.base_path = base_path
        self.backup_enabled = backup_enabled

        print(f"📂 FileManager initialized: {self.base_path} (backup: {self.backup_enabled})")

    def list_directory(self, path: str = ".", recursive: bool = False) -> None:
        """List files and directories.

        :param path: Directory path to list
        :param recursive: Enable recursive directory listing"""
        mode = "recursive" if recursive else "flat"
        print(f"📋 Listing {path} ({mode} mode)")
        print(f"Base path: {self.base_path}")

    class OrganizationOperations:
        """File organization and cleanup operations."""

        def __init__(self, main_instance, auto_organize: bool = False):
            """Initialize organization operations.

            :param main_instance: Main FileManager instance
            :param auto_organize: Enable automatic file organization"""
            self.main_instance = main_instance
            self.auto_organize = auto_organize

        def organize_by_type(self, source_dir: str, create_subdirs: bool = True) -> None:
            """Organize files by type into subdirectories.

            :param source_dir: Source directory to organize
            :param create_subdirs: Create subdirectories for each file type"""
            print(f"🗂️  Organizing {source_dir} by file type")
            print(f"Create subdirs: {create_subdirs}")
            print(f"Auto-organize mode: {self.auto_organize}")
            if self.main_instance.backup_enabled:
                print("📋 Backup will be created before organization")

        def cleanup_duplicates(self, directory: str, dry_run: bool = True) -> None:
            """Remove duplicate files from directory.

            :param directory: Directory to clean up
            :param dry_run: Show what would be removed without actual deletion"""
            action = "Simulating" if dry_run else "Performing"
            print(f"🧹 {action} duplicate cleanup in {directory}")
            print(f"Base path: {self.main_instance.base_path}")

    class SyncOperations:
        """File synchronization and backup operations."""

        def __init__(self, main_instance, compression: bool = True):
            """Initialize sync operations.

            :param main_instance: Main FileManager instance
            :param compression: Enable compression for sync operations"""
            self.main_instance = main_instance
            self.compression = compression

        def sync_directories(self, source: str, destination: str,
                           bidirectional: bool = False) -> None:
            """Synchronize directories.

            :param source: Source directory path
            :param destination: Destination directory path
            :param bidirectional: Enable bidirectional synchronization"""
            sync_type = "bidirectional" if bidirectional else "one-way"
            comp_status = "compressed" if self.compression else "uncompressed"
            print(f"🔄 {sync_type.title()} sync: {source} -> {destination} ({comp_status})")

        def create_backup(self, source: str, backup_name: str = None) -> None:
            """Create backup of directory or file.

            :param source: Source path to backup
            :param backup_name: Custom backup name (auto-generated if None)"""
            backup = backup_name or f"backup_{source.replace('/', '_')}"
            print(f"💾 Creating backup: {source} -> {backup}")
            print(f"Compression: {self.compression}")


class ReportGenerator:
    """Comprehensive report generation utility.

    Creates various types of reports from processed data with
    customizable formatting and output options."""

    def __init__(self, output_dir: str = "./reports", template_dir: str = "./templates"):
        """Initialize report generator.

        :param output_dir: Directory for generated reports
        :param template_dir: Directory containing report templates"""
        self.output_dir = output_dir
        self.template_dir = template_dir

        print(f"📊 ReportGenerator initialized: output={output_dir}, templates={template_dir}")

    def generate_summary(self, data_source: str, include_charts: bool = False) -> None:
        """Generate summary report from data source.

        :param data_source: Path to data source file or directory
        :param include_charts: Include visual charts in the report"""
        charts_status = "with charts" if include_charts else "text only"
        print(f"📈 Generating summary report from {data_source} ({charts_status})")
        print(f"Output: {self.output_dir}")

    class AnalyticsReports:
        """Advanced analytics and statistical reports."""

        def __init__(self, main_instance, statistical_confidence: float = 0.95):
            """Initialize analytics reports.

            :param main_instance: Main ReportGenerator instance
            :param statistical_confidence: Statistical confidence level"""
            self.main_instance = main_instance
            self.statistical_confidence = statistical_confidence

        def trend_analysis(self, data_file: str, time_period: int = 30) -> None:
            """Generate trend analysis report.

            :param data_file: Data file for trend analysis
            :param time_period: Analysis time period in days"""
            print(f"📊 Trend analysis: {data_file} ({time_period} days)")
            print(f"Confidence level: {self.statistical_confidence}")
            print(f"Output: {self.main_instance.output_dir}")

        def correlation_matrix(self, dataset: str, variables: List[str] = None) -> None:
            """Generate correlation matrix report.

            :param dataset: Dataset file path
            :param variables: List of variables to analyze (all if None)"""
            var_info = f"({len(variables)} variables)" if variables else "(all variables)"
            print(f"🔗 Correlation matrix: {dataset} {var_info}")
            print(f"Templates: {self.main_instance.template_dir}")


def demonstrate_multi_class_usage():
    """Demonstrate various multi-class CLI usage patterns."""
    print("🎯 MULTI-CLASS CLI DEMONSTRATION")
    print("=" * 50)

    # Example 1: Basic multi-class CLI
    print("\n1️⃣ Basic Multi-Class CLI:")
    try:
        cli_basic = CLI([DataProcessor, FileManager, ReportGenerator])
        print(f"✅ Created CLI with {len(cli_basic.target_classes)} classes")
        print(f"   Target mode: {cli_basic.target_mode.value}")
        print(f"   Title: {cli_basic.title}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 2: Multi-class with System integration
    print("\n2️⃣ Multi-Class CLI with System Integration:")
    try:
        cli_with_system = CLI([System, DataProcessor, FileManager])
        print(f"✅ Created CLI with System + {len(cli_with_system.target_classes)-1} other classes")
        print(f"   System class integrated cleanly without special handling")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 3: Single class in list (backward compatibility)
    print("\n3️⃣ Single Class in List (Backward Compatibility):")
    try:
        cli_single = CLI([DataProcessor])
        print(f"✅ Single class in list behaves like regular class mode")
        print(f"   Target mode: {cli_single.target_mode.value}")
        print(f"   Backward compatible: {cli_single.target_class == DataProcessor}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 4: Collision detection
    print("\n4️⃣ Collision Detection Example:")

    # Create a class with conflicting method name
    class ConflictingClass:
        def __init__(self, setting: str = "default"):
            self.setting = setting

        def quick_process(self, file: str) -> None:  # Conflicts with DataProcessor.quick_process
            """Conflicting quick process method."""
            print(f"Conflicting quick_process: {file}")

    try:
        CLI([DataProcessor, ConflictingClass])
        print("❌ Expected collision error but none occurred")
    except ValueError as e:
        print(f"✅ Collision detected as expected: {str(e)[:80]}...")

    print("\n🎉 Multi-class CLI demonstration completed!")


if __name__ == '__main__':
    # If no arguments provided, show demonstration
    if len(sys.argv) == 1:
        demonstrate_multi_class_usage()
        print(f"\n💡 Try running: python {sys.argv[0]} --help")
        sys.exit(0)

    # Import theme functionality for colored output
    from src.theme import create_default_theme_colorful

    # Create multi-class CLI with all utilities
    theme = create_default_theme_colorful()
    cli = CLI(
        [System, DataProcessor, FileManager, ReportGenerator],
        title="Multi-Class Utility Suite",
        theme=theme,
        enable_completion=True
    )

    # Run the CLI and exit with appropriate code
    result = cli.run()
    sys.exit(result if isinstance(result, int) else 0)
