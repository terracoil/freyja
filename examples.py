#!/usr/bin/env python
# Enhanced examples demonstrating auto-cli-py with docstring integration.
import enum
import sys
from pathlib import Path

from auto_cli.cli import CLI


class LogLevel(enum.Enum):
    """Logging level options for output verbosity."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AnimalType(enum.Enum):
    """Different types of animals for counting."""
    ANT = 1
    BEE = 2
    CAT = 3
    DOG = 4


def foo():
    """Simple greeting function with no parameters."""
    print("FOO!")


def hello(name: str = "World", count: int = 1, excited: bool = False):
    """Greet someone with configurable enthusiasm.

    :param name: Name of the person to greet
    :param count: Number of times to repeat the greeting
    :param excited: Add exclamation marks for enthusiasm
    """
    suffix = "!!!" if excited else "."
    for _ in range(count):
        print(f"Hello, {name}{suffix}")


def train(
    data_dir: str = "./data/",
    initial_learning_rate: float = 0.0001,
    seed: int = 2112,
    batch_size: int = 512,
    epochs: int = 20,
    use_gpu: bool = False
):
    """Train a machine learning model with specified parameters.

    :param data_dir: Directory containing training data files
    :param initial_learning_rate: Starting learning rate for optimization
    :param seed: Random seed for reproducible results
    :param batch_size: Number of samples per training batch
    :param epochs: Number of complete passes through the training data
    :param use_gpu: Enable GPU acceleration if available
    """
    gpu_status = "GPU" if use_gpu else "CPU"
    params = {
        "Data directory": data_dir,
        "Learning rate": initial_learning_rate,
        "Random seed": seed,
        "Batch size": batch_size,
        "Epochs": epochs
    }
    print(f"Training model on {gpu_status}:")
    print('\n'.join(f"  {k}: {v}" for k, v in params.items()))


def count_animals(count: int = 20, animal: AnimalType = AnimalType.BEE):
    """Count animals of a specific type.

    :param count: Number of animals to count
    :param animal: Type of animal to count from the available options
    """
    print(f"Counting {count} {animal.name.lower()}s!")
    return count


def process_file(
    input_path: Path,
    output_path: Path | None = None,
    encoding: str = "utf-8",
    log_level: LogLevel = LogLevel.INFO,
    backup: bool = True
):
    """Process a text file with various configuration options.

    :param input_path: Path to the input file to process
    :param output_path: Optional output file path (defaults to input_path.processed)
    :param encoding: Character encoding to use when reading/writing files
    :param log_level: Logging verbosity level for processing output
    :param backup: Create backup of original file before processing
    """
    # Set default output path if not provided
    if output_path is None:
        output_path = input_path.with_suffix(f"{input_path.suffix}.processed")

    config = {
        "Processing file": input_path,
        "Output to": output_path,
        "Encoding": encoding,
        "Log level": log_level.value,
        "Backup enabled": backup
    }
    print('\n'.join(f"{k}: {v}" for k, v in config.items()))

    # Simulate file processing
    if input_path.exists():
        try:
            content = input_path.read_text(encoding=encoding)

            # Create backup if requested
            if backup:
                backup_path = input_path.with_suffix(f"{input_path.suffix}.backup")
                backup_path.write_text(content, encoding=encoding)
                print(f"Backup created: {backup_path}")

            # Process and write output
            processed_content = f"[PROCESSED] {content}"
            output_path.write_text(processed_content, encoding=encoding)
            print("✓ File processing completed successfully")

        except UnicodeDecodeError:
            print(f"✗ Error: Could not read file with {encoding} encoding")
        except Exception as e:
            print(f"✗ Error during processing: {e}")
    else:
        print(f"✗ Error: Input file '{input_path}' does not exist")


def batch_convert(
    pattern: str = "*.txt",
    recursive: bool = False,
    dry_run: bool = False,
    workers: int = 4,
    output_format: str = "processed"
):
    """Convert multiple files matching a pattern in batch mode.

    :param pattern: Glob pattern to match files for processing
    :param recursive: Search directories recursively for matching files
    :param dry_run: Show what would be done without actually modifying files
    :param workers: Number of parallel workers for processing files
    :param output_format: Output format identifier to append to filenames
    """
    search_mode = "recursive" if recursive else "current directory"
    print(f"Batch conversion using pattern: '{pattern}'")
    print(f"Search mode: {search_mode}")
    print(f"Workers: {workers}")
    print(f"Output format: {output_format}")

    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified")

    # Simulate file discovery and processing
    found_files = [
        "document1.txt",
        "readme.txt",
        "notes.txt",
        "subdir/info.txt" if recursive else None
    ]
    found_files = [f for f in found_files if f is not None]

    print(f"\nFound {len(found_files)} files matching pattern:")
    for file_path in found_files:
        action = "Would convert" if dry_run else "Converting"
        output_name = f"{file_path}.{output_format}"
        print(f"  {action}: {file_path} → {output_name}")


def advanced_demo(
    text: str,
    iterations: int = 1,
    config_file: Path | None = None,
    debug_mode: bool = False
):
    """Demonstrate advanced parameter handling and edge cases.

    This function showcases how the CLI handles various parameter types
    including required parameters, optional files, and boolean flags.

    :param text: Required text input for processing
    :param iterations: Number of times to process the input text
    :param config_file: Optional configuration file to load settings from
    :param debug_mode: Enable detailed debug output during processing
    """
    print(f"Processing text: '{text}'")
    print(f"Iterations: {iterations}")

    if config_file:
        if config_file.exists():
            print(f"Loading config from: {config_file}")
        else:
            print(f"Warning: Config file not found: {config_file}")

    if debug_mode:
        print("DEBUG: Advanced demo function called")
        print(f"DEBUG: Text length: {len(text)} characters")

    # Simulate processing
    for i in range(iterations):
        if debug_mode:
            print(f"DEBUG: Processing iteration {i+1}/{iterations}")
        result = text.upper() if i % 2 == 0 else text.lower()
        print(f"Result {i+1}: {result}")


# Database subcommands using double underscore (db__)
def db__create(
    name: str,
    engine: str = "postgres",
    host: str = "localhost",
    port: int = 5432,
    encrypted: bool = False
):
    """Create a new database instance.

    :param name: Name of the database to create
    :param engine: Database engine type (sqlite, postgres, mysql)
    :param host: Database host address
    :param port: Database port number
    :param encrypted: Enable database encryption
    """
    encryption_status = "encrypted" if encrypted else "unencrypted"
    print(f"Creating {encryption_status} {engine} database '{name}'")
    print(f"Host: {host}:{port}")
    print("✓ Database created successfully")


def db__migrate(
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
            print(f"  Running migration {i+1}/{steps}...")
        print("✓ Migrations completed")


def db__backup_restore(
    action: str,
    file_path: Path,
    compress: bool = True,
    exclude_tables: str = ""
):
    """Backup or restore database operations.

    :param action: Action to perform (backup or restore)
    :param file_path: Path to backup file
    :param compress: Compress backup files (backup only)
    :param exclude_tables: Comma-separated list of tables to exclude from backup
    """
    if action == "backup":
        backup_type = "compressed" if compress else "uncompressed"
        print(f"Creating {backup_type} backup at: {file_path}")

        if exclude_tables:
            excluded = exclude_tables.split(',')
            print(f"Excluding tables: {', '.join(excluded)}")
    elif action == "restore":
        print(f"Restoring database from: {file_path}")

    print("✓ Operation completed successfully")


# User management subcommands using double underscore (user__)
def user__create(
    username: str,
    email: str,
    role: str = "user",
    active: bool = True,
    send_welcome: bool = False
):
    """Create a new user account.

    :param username: Unique username for the account
    :param email: User's email address
    :param role: User role (user, admin, moderator)
    :param active: Set account as active immediately
    :param send_welcome: Send welcome email to the user
    """
    status = "active" if active else "inactive"
    print(f"Creating {status} user account:")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print(f"  Role: {role}")

    if send_welcome:
        print(f"📧 Sending welcome email to {email}")

    print("✓ User created successfully")


def user__list(
    role_filter: str = "all",
    active_only: bool = False,
    output_format: str = "table",
    limit: int = 50
):
    """List user accounts with filtering options.

    :param role_filter: Filter by role (all, user, admin, moderator)
    :param active_only: Show only active accounts
    :param output_format: Output format (table, json, csv)
    :param limit: Maximum number of users to display
    """
    filters = []
    if role_filter != "all":
        filters.append(f"role={role_filter}")
    if active_only:
        filters.append("status=active")

    filter_text = f" with filters: {', '.join(filters)}" if filters else ""
    print(f"Listing up to {limit} users in {output_format} format{filter_text}")

    # Simulate user list
    sample_users = [
        ("alice", "alice@example.com", "admin", "active"),
        ("bob", "bob@example.com", "user", "active"),
        ("charlie", "charlie@example.com", "moderator", "inactive")
    ]

    if output_format == "table":
        print("\nUsername | Email              | Role      | Status")
        print("-" * 50)
        for username, email, role, status in sample_users[:limit]:
            if (role_filter == "all" or role == role_filter) and \
               (not active_only or status == "active"):
                print(f"{username:<8} | {email:<18} | {role:<9} | {status}")


def user__delete(
    username: str,
    force: bool = False,
    backup_data: bool = True
):
    """Delete a user account.

    :param username: Username of the account to delete
    :param force: Skip confirmation prompt
    :param backup_data: Create backup of user data before deletion
    """
    if backup_data:
        print(f"📦 Creating backup of data for user '{username}'")

    confirmation = "(forced)" if force else "(with confirmation)"
    print(f"Deleting user '{username}' {confirmation}")
    print("✓ User deleted successfully")


# Multi-level admin operations using triple underscore (admin__*)
def admin__user__reset_password(username: str, notify_user: bool = True):
    """Reset a user's password (admin operation).

    :param username: Username whose password to reset
    :param notify_user: Send notification email to user
    """
    print(f"🔑 Admin operation: Resetting password for user '{username}'")
    if notify_user:
        print("📧 Sending password reset notification")
    print("✓ Password reset completed")


def admin__system__maintenance_mode(enable: bool, message: str = "System maintenance in progress"):
    """Enable or disable system maintenance mode.

    :param enable: Enable (True) or disable (False) maintenance mode
    :param message: Message to display to users during maintenance
    """
    action = "Enabling" if enable else "Disabling"
    print(f"🔧 {action} system maintenance mode")
    if enable:
        print(f"📢 Message: '{message}'")
    print("✓ Maintenance mode updated")






def completion__demo(config_file: str = "config.json", output_dir: str = "./output"):
    """Demonstrate completion for file paths and configuration.

    :param config_file: Configuration file path (demonstrates file completion)
    :param output_dir: Output directory path (demonstrates directory completion)
    """
    print(f"🔧 Using config file: {config_file}")
    print(f"📂 Output directory: {output_dir}")
    print("✨ This command demonstrates file/directory path completion!")
    print("💡 Try: python examples.py completion demo --config-file <TAB>")
    print("💡 Try: python examples.py completion demo --output-dir <TAB>")


if __name__ == '__main__':
    # Import theme functionality
    from auto_cli.theme import create_default_theme

    # Create CLI with colored theme and completion enabled
    theme = create_default_theme()
    cli = CLI(
        sys.modules[__name__],
        title="Enhanced CLI - Hierarchical commands with double underscore delimiter",
        theme=theme,
        theme_tuner=True,
        enable_completion=True  # Enable shell completion
    )

    # Run the CLI and exit with appropriate code
    result = cli.run()
    sys.exit(result if isinstance(result, int) else 0)
