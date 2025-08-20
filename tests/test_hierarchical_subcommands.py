"""Tests for hierarchical subcommands functionality with double underscore delimiter."""

import enum
import sys
from unittest.mock import patch

import pytest

from auto_cli.cli import CLI


class UserRole(enum.Enum):
    """Test role enumeration."""
    USER = "user"
    ADMIN = "admin"


# Test functions for hierarchical commands
def flat_hello(name: str = "World"):
    """Simple flat command.

    :param name: Name to greet
    """
    return f"Hello, {name}!"


def user__create(username: str, email: str, role: UserRole = UserRole.USER):
    """Create a new user.

    :param username: Username for the account
    :param email: Email address
    :param role: User role
    """
    return f"Created user {username} ({email}) with role {role.value}"


def user__list(active_only: bool = False, limit: int = 10):
    """List users with filtering.

    :param active_only: Show only active users
    :param limit: Maximum number of users to show
    """
    return f"Listing users (active_only={active_only}, limit={limit})"


def user__delete(username: str, force: bool = False):
    """Delete a user account.

    :param username: Username to delete
    :param force: Skip confirmation
    """
    return f"Deleted user {username} (force={force})"


def db__migrate(steps: int = 1, direction: str = "up"):
    """Run database migrations.

    :param steps: Number of steps
    :param direction: Migration direction
    """
    return f"Migrating {steps} steps {direction}"


def admin__user__reset_password(username: str, notify: bool = True):
    """Reset user password (admin operation).

    :param username: Username to reset
    :param notify: Send notification
    """
    return f"Admin reset password for {username} (notify={notify})"


def admin__system__backup(compress: bool = True):
    """Create system backup.

    :param compress: Compress backup
    """
    return f"System backup (compress={compress})"


# Create test module
test_module = sys.modules[__name__]


class TestHierarchicalSubcommands:
    """Test hierarchical subcommand functionality."""

    def setup_method(self):
        """Set up test CLI instance."""
        self.cli = CLI(test_module, "Test CLI with Hierarchical Commands")

    def test_function_discovery_and_grouping(self):
        """Test that functions are correctly discovered and grouped."""
        commands = self.cli.commands

        # Check flat command
        assert "flat-hello" in commands
        assert commands["flat-hello"]["type"] == "flat"
        assert commands["flat-hello"]["function"] == flat_hello

        # Check user group
        assert "user" in commands
        assert commands["user"]["type"] == "group"
        user_subcommands = commands["user"]["subcommands"]

        assert "create" in user_subcommands
        assert "list" in user_subcommands
        assert "delete" in user_subcommands

        assert user_subcommands["create"]["function"] == user__create
        assert user_subcommands["list"]["function"] == user__list
        assert user_subcommands["delete"]["function"] == user__delete

        # Check db group
        assert "db" in commands
        assert commands["db"]["type"] == "group"
        db_subcommands = commands["db"]["subcommands"]

        assert "migrate" in db_subcommands
        assert db_subcommands["migrate"]["function"] == db__migrate

        # Check nested admin group
        assert "admin" in commands
        assert commands["admin"]["type"] == "group"
        admin_subcommands = commands["admin"]["subcommands"]

        assert "user" in admin_subcommands
        assert "system" in admin_subcommands

        # Check deeply nested commands
        admin_user = admin_subcommands["user"]["subcommands"]
        assert "reset-password" in admin_user
        assert admin_user["reset-password"]["function"] == admin__user__reset_password

        admin_system = admin_subcommands["system"]["subcommands"]
        assert "backup" in admin_system
        assert admin_system["backup"]["function"] == admin__system__backup

    def test_parser_creation_hierarchical(self):
        """Test parser creation with hierarchical commands."""
        parser = self.cli.create_parser()

        # Test that parser has subparsers
        subparsers_action = None
        for action in parser._actions:
            if hasattr(action, 'choices') and action.choices:
                subparsers_action = action
                break

        assert subparsers_action is not None
        choices = list(subparsers_action.choices.keys())

        # Should have flat and grouped commands
        assert "flat-hello" in choices
        assert "user" in choices
        assert "db" in choices
        assert "admin" in choices

    def test_flat_command_execution(self):
        """Test execution of flat commands."""
        result = self.cli.run(["flat-hello", "--name", "Alice"])
        assert result == "Hello, Alice!"

    def test_two_level_subcommand_execution(self):
        """Test execution of two-level subcommands."""
        # Test user create
        result = self.cli.run([
            "user", "create",
            "--username", "alice",
            "--email", "alice@test.com",
            "--role", "ADMIN"
        ])
        assert result == "Created user alice (alice@test.com) with role admin"

        # Test user list
        result = self.cli.run(["user", "list", "--active-only", "--limit", "5"])
        assert result == "Listing users (active_only=True, limit=5)"

        # Test db migrate
        result = self.cli.run(["db", "migrate", "--steps", "3", "--direction", "down"])
        assert result == "Migrating 3 steps down"

    def test_three_level_subcommand_execution(self):
        """Test execution of three-level nested subcommands."""
        # Test admin user reset-password (notify is True by default)
        result = self.cli.run([
            "admin", "user", "reset-password",
            "--username", "bob"
        ])
        assert result == "Admin reset password for bob (notify=True)"

        # Test admin system backup (compress is True by default)
        result = self.cli.run([
            "admin", "system", "backup"
        ])
        assert result == "System backup (compress=True)"

    def test_help_display_main(self):
        """Test main help displays hierarchical structure."""
        with patch('sys.stdout') as mock_stdout:
            with pytest.raises(SystemExit):
                self.cli.run(["--help"])

        # Should have called print_help
        assert mock_stdout.write.called

    def test_help_display_group(self):
        """Test group help shows subcommands."""
        with patch('builtins.print') as mock_print:
            result = self.cli.run(["user"])

        # Should return 0 and show group help
        assert result == 0

    def test_help_display_nested_group(self):
        """Test nested group help."""
        with patch('builtins.print') as mock_print:
            result = self.cli.run(["admin"])

        assert result == 0

    def test_missing_subcommand_handling(self):
        """Test handling of missing subcommands."""
        with patch('builtins.print') as mock_print:
            result = self.cli.run(["user"])

        # Should show help and return 0
        assert result == 0

    def test_invalid_command_handling(self):
        """Test handling of invalid commands."""
        with patch('builtins.print') as mock_print:
            with patch('sys.stderr'):
                with pytest.raises(SystemExit):
                    result = self.cli.run(["nonexistent"])

    def test_underscore_to_dash_conversion(self):
        """Test that underscores are converted to dashes in CLI names."""
        commands = self.cli.commands

        # Check that function names with underscores become dashed
        assert "flat-hello" in commands  # flat_hello -> flat-hello

        # Check nested commands
        user_subcommands = commands["user"]["subcommands"]
        admin_user_subcommands = commands["admin"]["subcommands"]["user"]["subcommands"]

        assert "reset-password" in admin_user_subcommands  # reset_password -> reset-password

    def test_command_path_storage(self):
        """Test that command paths are stored correctly for nested commands."""
        commands = self.cli.commands

        # Check nested command path
        reset_cmd = commands["admin"]["subcommands"]["user"]["subcommands"]["reset-password"]
        assert reset_cmd["command_path"] == ["admin", "user", "reset-password"]

    def test_mixed_flat_and_hierarchical(self):
        """Test CLI with mix of flat and hierarchical commands."""
        # Should be able to execute both types
        flat_result = self.cli.run(["flat-hello", "--name", "Test"])
        assert flat_result == "Hello, Test!"

        hierarchical_result = self.cli.run(["user", "create", "--username", "test", "--email", "test@test.com"])
        assert "Created user test" in hierarchical_result

    def test_error_handling_with_verbose(self):
        """Test error handling with verbose flag."""
        # Create a CLI with a function that will raise an error
        def error_function():
            """Function that raises an error."""
            raise ValueError("Test error")

        # Add the function to the test module temporarily
        test_module.error_function = error_function

        try:
            error_cli = CLI(test_module, "Error Test CLI")

            with patch('builtins.print') as mock_print:
                with patch('sys.stderr'):
                    result = error_cli.run(["--verbose", "error-function"])

            # Should return error code
            assert result == 1

        finally:
            # Clean up
            if hasattr(test_module, 'error_function'):
                delattr(test_module, 'error_function')


class TestHierarchicalEdgeCases:
    """Test edge cases for hierarchical subcommands."""

    def test_empty_double_underscore(self):
        """Test handling of functions with empty parts in double underscore."""
        # This would be malformed: user__  or __create
        # The function discovery should handle gracefully
        def malformed__function():
            """Malformed function name."""
            return "test"

        # Should not crash during discovery
        cli = CLI(sys.modules[__name__], "Test CLI")
        # The function shouldn't be included in normal discovery due to naming

    def test_single_vs_double_underscore_distinction(self):
        """Test that single underscores don't create groups."""
        def single_underscore_func():
            """Function with single underscore."""
            return "single"

        def double__underscore__func():
            """Function with double underscore."""
            return "double"

        # Add to module temporarily
        test_module.single_underscore_func = single_underscore_func
        test_module.double__underscore__func = double__underscore__func

        try:
            cli = CLI(test_module, "Test CLI")
            commands = cli.commands

            # Single underscore should be flat command with dash
            assert "single-underscore-func" in commands
            assert commands["single-underscore-func"]["type"] == "flat"

            # Double underscore should create groups
            assert "double" in commands
            assert commands["double"]["type"] == "group"

        finally:
            # Clean up
            delattr(test_module, 'single_underscore_func')
            delattr(test_module, 'double__underscore__func')

    def test_deep_nesting_support(self):
        """Test support for deep nesting levels."""
        def level1__level2__level3__level4__deep_command():
            """Very deeply nested command."""
            return "deep"

        # Add to module temporarily
        test_module.level1__level2__level3__level4__deep_command = level1__level2__level3__level4__deep_command

        try:
            cli = CLI(test_module, "Test CLI")
            commands = cli.commands

            # Should create proper nesting
            assert "level1" in commands
            level2 = commands["level1"]["subcommands"]["level2"]
            level3 = level2["subcommands"]["level3"]
            level4 = level3["subcommands"]["level4"]

            assert "deep-command" in level4["subcommands"]

        finally:
            # Clean up
            delattr(test_module, 'level1__level2__level3__level4__deep_command')
