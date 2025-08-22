#!/usr/bin/env python
"""Class-based CLI example demonstrating method introspection."""

import enum
import sys
from pathlib import Path
from auto_cli.cli import CLI


class ProcessingMode(enum.Enum):
    """Processing modes for data operations."""
    FAST = "fast"
    THOROUGH = "thorough" 
    BALANCED = "balanced"


class DataProcessor:
    """Data processing utility with various operations.
    
    This class demonstrates how auto-cli-py can generate CLI commands
    from class methods using the same introspection techniques applied
    to module functions.
    """
    
    def __init__(self):
        """Initialize the data processor."""
        self.processed_count = 0
    
    def process_file(self, input_file: Path, output_dir: str = "./processed", 
                    mode: ProcessingMode = ProcessingMode.BALANCED, 
                    dry_run: bool = False):
        """Process a single file with specified parameters.
        
        :param input_file: Path to the input file to process
        :param output_dir: Directory to save processed files
        :param mode: Processing mode affecting speed vs quality
        :param dry_run: Show what would be processed without actual processing
        """
        action = "Would process" if dry_run else "Processing"
        print(f"{action} file: {input_file}")
        print(f"Mode: {mode.value}")
        print(f"Output directory: {output_dir}")
        
        if not dry_run:
            self.processed_count += 1
            print(f"✓ File processed successfully (total: {self.processed_count})")
        
        return {"file": str(input_file), "mode": mode.value, "dry_run": dry_run}
    
    def batch_process(self, pattern: str, max_files: int = 100, 
                     parallel: bool = False, verbose: bool = False):
        """Process multiple files matching a pattern.
        
        :param pattern: File pattern to match (e.g., '*.txt')
        :param max_files: Maximum number of files to process
        :param parallel: Enable parallel processing for better performance
        :param verbose: Enable detailed output during processing
        """
        processing_mode = "parallel" if parallel else "sequential"
        print(f"Batch processing {max_files} files matching '{pattern}'")
        print(f"Processing mode: {processing_mode}")
        
        if verbose:
            print("Verbose mode enabled - showing detailed progress")
            
        # Simulate processing
        for i in range(min(3, max_files)):  # Demo with just 3 files
            if verbose:
                print(f"  Processing file {i+1}: example_{i+1}.txt")
            self.processed_count += 1
            
        print(f"✓ Processed {min(3, max_files)} files (total: {self.processed_count})")
        return {"pattern": pattern, "files_processed": min(3, max_files), "parallel": parallel}
    
    def export_results(self, format: str = "json", compress: bool = True,
                      include_metadata: bool = False):
        """Export processing results in specified format.
        
        :param format: Output format (json, csv, xml)
        :param compress: Compress the output file
        :param include_metadata: Include processing metadata in export
        """
        compression_status = "compressed" if compress else "uncompressed"
        metadata_status = "with metadata" if include_metadata else "without metadata"
        
        print(f"Exporting {self.processed_count} results to {compression_status} {format} {metadata_status}")
        print(f"✓ Export completed: results.{format}{'.gz' if compress else ''}")
        return {"format": format, "compressed": compress, "metadata": include_metadata, "count": self.processed_count}
    
    # Hierarchical commands using double underscore
    def config__set_default_mode(self, mode: ProcessingMode):
        """Set the default processing mode for future operations.
        
        :param mode: Default processing mode to use
        """
        print(f"🔧 Setting default processing mode to: {mode.value}")
        print("✓ Configuration updated")
        return {"default_mode": mode.value}
    
    def config__show_settings(self):
        """Display current configuration settings."""
        print("📋 Current Configuration:")
        print(f"  Processed files: {self.processed_count}")
        print(f"  Default mode: balanced")  # Would be dynamic in real implementation
        print("✓ Settings displayed")
        return {"processed_count": self.processed_count, "default_mode": "balanced"}
    
    def stats__summary(self, detailed: bool = False):
        """Show processing statistics summary.
        
        :param detailed: Include detailed statistics breakdown
        """
        print(f"📊 Processing Statistics:")
        print(f"  Total files processed: {self.processed_count}")
        
        if detailed:
            print("  Detailed breakdown:")
            print("    - Successful: 100%")
            print("    - Average time: 0.5s per file") 
            print("    - Memory usage: 45MB peak")
            
        return {"total_files": self.processed_count, "detailed": detailed}


if __name__ == '__main__':
    # Import theme functionality  
    from auto_cli.theme import create_default_theme
    
    # Create CLI from class with colored theme
    theme = create_default_theme()
    cli = CLI.from_class(
        DataProcessor,
        theme=theme,
        theme_tuner=True,
        enable_completion=True
    )
    
    # Run the CLI and exit with appropriate code
    result = cli.run()
    sys.exit(result if isinstance(result, int) else 0)