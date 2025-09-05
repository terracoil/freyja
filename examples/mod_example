#!/usr/bin/env python3
"""Module-based FreyjaCLI example with real functionality."""

import csv
import json
import math
import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional

from freyja import FreyjaCLI


class OutputFormat(Enum):
  """Available output formats."""
  JSON = "json"
  CSV = "csv"
  TEXT = "text"


class HashAlgorithm(Enum):
  """Hash algorithms for file verification."""
  MD5 = "md5"
  SHA1 = "sha1"
  SHA256 = "sha256"


def generate_report(data_file: str, output_format: OutputFormat = OutputFormat.JSON) -> None:
  """Generate a report from data file."""
  data_path = Path(data_file)
  
  if not data_path.exists():
    print(f"Error: Data file not found: {data_file}")
    return
  
  try:
    # Read sample data
    with open(data_path, 'r') as f:
      lines = f.readlines()
    
    report = {
      "file": str(data_path),
      "lines": len(lines),
      "size_bytes": data_path.stat().st_size,
      "non_empty_lines": len([line for line in lines if line.strip()])
    }
    
    if output_format == OutputFormat.JSON:
      print(json.dumps(report, indent=2))
    elif output_format == OutputFormat.CSV:
      print("metric,value")
      for key, value in report.items():
        print(f"{key},{value}")
    else:
      print(f"File Report for {data_path.name}:")
      for key, value in report.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
        
  except Exception as e:
    print(f"Error processing file: {e}")


def calculate_statistics(numbers: List[float], precision: int = 2) -> None:
  """Calculate statistical measures for a list of numbers."""
  if not numbers:
    print("Error: No numbers provided")
    return
  
  try:
    mean = sum(numbers) / len(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = math.sqrt(variance)
    minimum = min(numbers)
    maximum = max(numbers)
    
    print(f"Statistics for {len(numbers)} numbers:")
    print(f"  Mean: {mean:.{precision}f}")
    print(f"  Standard Deviation: {std_dev:.{precision}f}")
    print(f"  Minimum: {minimum:.{precision}f}")
    print(f"  Maximum: {maximum:.{precision}f}")
    print(f"  Range: {maximum - minimum:.{precision}f}")
    
  except Exception as e:
    print(f"Error calculating statistics: {e}")


def process_csv_file(
    input_file: str,
    output_file: str = "processed_data.csv",
    delimiter: str = ",",
    skip_header: bool = True,
    filter_column: Optional[str] = None,
    filter_value: Optional[str] = None
) -> None:
  """Process CSV file with filtering and transformation."""
  input_path = Path(input_file)
  output_path = Path(output_file)
  
  if not input_path.exists():
    print(f"Error: Input file not found: {input_file}")
    return
  
  try:
    processed_rows = []
    total_rows = 0
    
    with open(input_path, 'r', newline='') as infile:
      reader = csv.DictReader(infile, delimiter=delimiter)
      
      if skip_header and reader.fieldnames:
        print(f"Detected columns: {', '.join(reader.fieldnames)}")
      
      for row in reader:
        total_rows += 1
        
        # Apply filter if specified
        if filter_column and filter_value:
          if row.get(filter_column) != filter_value:
            continue
        
        processed_rows.append(row)
    
    # Write processed data
    if processed_rows:
      with open(output_path, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=processed_rows[0].keys())
        writer.writeheader()
        writer.writerows(processed_rows)
      
      print(f"Processed {len(processed_rows)}/{total_rows} rows")
      print(f"Output saved to: {output_path}")
    else:
      print("No data to process after filtering")
      
  except Exception as e:
    print(f"Error processing CSV: {e}")


def verify_file_hash(
    file_path: str,
    algorithm: HashAlgorithm = HashAlgorithm.SHA256,
    expected_hash: Optional[str] = None
) -> None:
  """Verify file integrity using hash algorithms."""
  import hashlib
  
  path = Path(file_path)
  
  if not path.exists():
    print(f"Error: File not found: {file_path}")
    return
  
  try:
    # Select hash algorithm
    hash_func = getattr(hashlib, algorithm.value)()
    
    # Calculate hash
    with open(path, 'rb') as f:
      for chunk in iter(lambda: f.read(4096), b""):
        hash_func.update(chunk)
    
    calculated_hash = hash_func.hexdigest()
    
    print(f"File: {path.name}")
    print(f"Algorithm: {algorithm.value.upper()}")
    print(f"Hash: {calculated_hash}")
    
    if expected_hash:
      if calculated_hash.lower() == expected_hash.lower():
        print("✅ Hash verification PASSED")
      else:
        print("❌ Hash verification FAILED")
        print(f"Expected: {expected_hash}")
    
  except Exception as e:
    print(f"Error calculating hash: {e}")


def analyze_text_file(
    file_path: str,
    word_frequency: bool = False,
    line_stats: bool = True,
    case_sensitive: bool = False,
    output_file: Optional[str] = None
) -> None:
  """Analyze text file and provide detailed statistics."""
  path = Path(file_path)
  
  if not path.exists():
    print(f"Error: File not found: {file_path}")
    return
  
  try:
    with open(path, 'r', encoding='utf-8') as f:
      content = f.read()
    
    lines = content.split('\n')
    words = content.split()
    
    if not case_sensitive:
      content_lower = content.lower()
      words = content_lower.split()
    
    analysis = {
      "file": path.name,
      "total_characters": len(content),
      "total_lines": len(lines),
      "total_words": len(words),
      "blank_lines": len([line for line in lines if not line.strip()])
    }
    
    if line_stats:
      non_empty_lines = [line for line in lines if line.strip()]
      if non_empty_lines:
        line_lengths = [len(line) for line in non_empty_lines]
        analysis.update({
          "avg_line_length": sum(line_lengths) / len(line_lengths),
          "max_line_length": max(line_lengths),
          "min_line_length": min(line_lengths)
        })
    
    if word_frequency:
      from collections import Counter
      word_counts = Counter(words)
      analysis["most_common_words"] = word_counts.most_common(5)
    
    # Output results
    if output_file:
      with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
      print(f"Analysis saved to: {output_file}")
    else:
      print(f"Text Analysis for {path.name}:")
      for key, value in analysis.items():
        if key == "most_common_words":
          print(f"  {key.replace('_', ' ').title()}:")
          for word, count in value:
            print(f"    {word}: {count}")
        else:
          print(f"  {key.replace('_', ' ').title()}: {value}")
          
  except Exception as e:
    print(f"Error analyzing file: {e}")


def backup_directory(
    source_dir: str,
    backup_dir: str = "./backups",
    compress: bool = True,
    exclude_patterns: Optional[List[str]] = None
) -> None:
  """Create backup of directory with compression and filtering."""
  import shutil
  import tarfile
  from datetime import datetime
  
  source_path = Path(source_dir)
  backup_path = Path(backup_dir)
  
  if not source_path.exists():
    print(f"Error: Source directory not found: {source_dir}")
    return
  
  try:
    backup_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if compress:
      archive_name = f"{source_path.name}_{timestamp}.tar.gz"
      archive_path = backup_path / archive_name
      
      with tarfile.open(archive_path, "w:gz") as tar:
        for file_path in source_path.rglob("*"):
          if file_path.is_file():
            # Check exclusion patterns
            should_exclude = False
            if exclude_patterns:
              for pattern in exclude_patterns:
                if pattern in str(file_path):
                  should_exclude = True
                  break
            
            if not should_exclude:
              arcname = file_path.relative_to(source_path)
              tar.add(file_path, arcname=arcname)
      
      print(f"Compressed backup created: {archive_path}")
      print(f"Archive size: {archive_path.stat().st_size} bytes")
    else:
      backup_name = f"{source_path.name}_{timestamp}"
      full_backup_path = backup_path / backup_name
      shutil.copytree(source_path, full_backup_path)
      print(f"Directory backup created: {full_backup_path}")
      
  except Exception as e:
    print(f"Error creating backup: {e}")


def migrate_database(
    direction: str = "up",
    steps: int = 1,
    dry_run: bool = False,
    force: bool = False
):
  """Run database migrations.

  :param direction: Migration direction (up or down)
  :param steps: Number of migration steps to execute
  :param dry_run: Show what would be migrated without applying changes
  :param force: Force migration even if conflicts exist
  """
  action = "Would migrate" if dry_run else "Migrating"
  force_text = " (forced)" if force else ""
  print(f"{action} {steps} step(s) {direction}{force_text}")

  if not dry_run:
    for i in range(steps):
      print(f"  Running migration {i + 1}/{steps}...")
    print("✓ Migrations completed")


def backup_database(
    file_path: Path,
    compress: bool = True,
    exclude_tables: str = ""
):
  """Backup database to file.

  :param file_path: Path to backup file
  :param compress: Compress backup files
  :param exclude_tables: Comma-separated list of tables to exclude from backup
  """
  backup_type = "compressed" if compress else "uncompressed"
  print(f"Creating {backup_type} backup at: {file_path}")

  if exclude_tables:
    excluded = exclude_tables.split(',')
    print(f"Excluding tables: {', '.join(excluded)}")

  print("✓ Backup completed successfully")


def restore_database(
    file_path: Path
):
  """Restore database from backup file.

  :param file_path: Path to backup file
  """
  print(f"Restoring database from: {file_path}")
  print("✓ Restore completed successfully")


# Admin operations (converted from nested command groups to flat cmd_tree)
def reset_user_password(username: str, notify_user: bool = True):
  """Reset a user's password (admin operation).

  :param username: Username whose password to reset
  :param notify_user: Send notification email to user
  """
  print(f"🔑 Admin operation: Resetting password for user '{username}'")
  if notify_user:
    print("📧 Sending password reset notification")
  print("✓ Password reset completed")


def set_maintenance_mode(enable: bool, message: str = "System maintenance in progress"):
  """Enable or disable system maintenance mode.

  :param enable: Enable (True) or disable (False) maintenance mode
  :param message: Message to display to users during maintenance
  """
  action = "Enabling" if enable else "Disabling"
  print(f"🔧 {action} system maintenance mode")
  if enable:
    print(f"📢 Message: '{message}'")
  print("✓ Maintenance mode updated")


def completion_demo(config_file: str = "config.json", output_dir: str = "./output"):
  """Demonstrate completion for file paths and configuration.

  :param config_file: Configuration file path (demonstrates file completion)
  :param output_dir: Output directory path (demonstrates directory completion)
  """
  print(f"🔧 Using config file: {config_file}")
  print(f"📂 Output directory: {output_dir}")
  print("✨ This command demonstrates file/directory path completion!")
  print("💡 Try: python mod_example.py completion-demo --config-file <TAB>")
  print("💡 Try: python mod_example.py completion-demo --output-dir <TAB>")


if __name__ == '__main__':
  # Create FreyjaCLI - descriptions now come from docstrings
  cli = FreyjaCLI(
    sys.modules[__name__],
    title="File Processing Utilities",
  )
  
  # Run FreyjaCLI
  result = cli.run()
  sys.exit(result if isinstance(result, int) else 0)
