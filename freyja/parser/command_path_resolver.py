"""Command path resolution for hierarchical command structures."""

from dataclasses import dataclass
from typing import Any

from freyja.utils.guards import guarded, not_none


@dataclass
class CommandPath:
    """Represents a resolved command path."""

    path_elements: list[str]
    is_valid: bool
    is_complete: bool  # True if path leads to an executable command
    is_group: bool  # True if path leads to a command group
    remaining_args: list[str]  # Arguments after command path


class CommandPathResolver:
    """Resolves hierarchical command paths from argument lists."""

    @guarded(not_none("command_tree", 1), implicit_return=False)
    def __init__(self, command_tree):
        """Initialize command path resolver."""
        self.command_tree = command_tree

    @guarded(not_none("args", 1), implicit_return=False)
    def resolve_path(self, args: list[str]) -> CommandPath:
        """Resolve command path and categorize remaining arguments."""
        if not args:
            return CommandPath(
                path_elements=[],
                is_valid=True,
                is_complete=False,
                is_group=False,
                remaining_args=[],
            )

        path_elements: list[str] = []
        remaining_args: list[str] = []
        found_command = False

        for i, arg in enumerate(args):
            # Stop at first option flag
            if arg.startswith("-"):
                remaining_args = args[i:]
                break

            # Check if adding this element creates a valid path
            test_path = path_elements + [arg]

            if self._is_valid_command_path(test_path):
                path_elements = test_path
                if self._is_executable_command(test_path):
                    found_command = True
                    remaining_args = args[i + 1 :]
                    break
            elif self._is_valid_group_path(test_path):
                path_elements = test_path
                # Continue to see if there's a command in this group
            else:
                # This element doesn't form a valid path - it might be a positional arg
                remaining_args = args[i:]
                break

        # If we didn't find remaining args yet, everything after path is remaining
        if not remaining_args and len(path_elements) < len(args):
            remaining_args = args[len(path_elements) :]

        is_valid = len(path_elements) == 0 or self._is_valid_path(path_elements)
        is_complete = found_command
        is_group = self._is_valid_group_path(path_elements) and not is_complete

        return CommandPath(
            path_elements=path_elements,
            is_valid=is_valid,
            is_complete=is_complete,
            is_group=is_group,
            remaining_args=remaining_args,
        )

    @guarded(not_none("path", 1), implicit_return=False)
    def validate_path(self, path: list[str]) -> bool:
        """Validate that a command path exists in the tree."""
        return self._is_valid_path(path)

    def get_available_commands(self, path: list[str] = None) -> list[str]:
        """Get available commands/groups at a given path level."""
        if not path:
            # Root level - return all flat commands and groups
            commands = []

            if hasattr(self.command_tree, "flat_commands") and self.command_tree.flat_commands:
                commands.extend(self.command_tree.flat_commands.keys())

            if hasattr(self.command_tree, "groups") and self.command_tree.groups:
                commands.extend(self.command_tree.groups.keys())

            return sorted(commands)

        if len(path) == 1:
            # Group level - return commands within the group
            group_name = path[0]
            if (
                hasattr(self.command_tree, "groups")
                and self.command_tree.groups
                and group_name in self.command_tree.groups
            ):
                group_info = self.command_tree.groups[group_name]
                if "commands" in group_info:
                    return sorted(group_info["commands"].keys())

        return []

    def get_command_info(self, path: list[str]) -> dict[str, Any] | None:
        """Get information about a command at the given path."""
        if not path:
            return None

        if len(path) == 1:
            # Flat command or group
            cmd_name = path[0]

            # Check flat commands first
            if (
                hasattr(self.command_tree, "flat_commands")
                and self.command_tree.flat_commands
                and cmd_name in self.command_tree.flat_commands
            ):
                return self.command_tree.flat_commands[cmd_name]

            # Check groups
            if (
                hasattr(self.command_tree, "groups")
                and self.command_tree.groups
                and cmd_name in self.command_tree.groups
            ):
                return self.command_tree.groups[cmd_name]

        elif len(path) == 2:
            # Hierarchical command (group + command)
            group_name, cmd_name = path

            if (
                hasattr(self.command_tree, "groups")
                and self.command_tree.groups
                and group_name in self.command_tree.groups
            ):
                group_info = self.command_tree.groups[group_name]
                if "commands" in group_info and cmd_name in group_info["commands"]:
                    return group_info["commands"][cmd_name]

        return None

    def is_command_executable(self, path: list[str]) -> bool:
        """Check if a path leads to an executable command."""
        return self._is_executable_command(path)

    def is_command_group(self, path: list[str]) -> bool:
        """Check if a path leads to a command group."""
        return self._is_valid_group_path(path) and not self._is_executable_command(path)

    def suggest_commands(self, partial_path: list[str]) -> list[str]:
        """Suggest possible commands based on partial path."""
        if not partial_path:
            return self.get_available_commands()

        if len(partial_path) == 1:
            # Partial command/group name
            partial_name = partial_path[0]
            available = self.get_available_commands()

            # Filter commands that start with partial name
            suggestions = [cmd for cmd in available if cmd.startswith(partial_name)]

            # If no exact matches, use fuzzy matching
            if not suggestions:
                suggestions = [cmd for cmd in available if partial_name in cmd]

            return suggestions

        elif len(partial_path) == 2:
            # Partial hierarchical command
            group_name, partial_cmd = partial_path
            available = self.get_available_commands([group_name])

            # Filter commands that start with partial command name
            suggestions = [cmd for cmd in available if cmd.startswith(partial_cmd)]

            # If no exact matches, use fuzzy matching
            if not suggestions:
                suggestions = [cmd for cmd in available if partial_cmd in cmd]

            return suggestions

        return []

    def _is_valid_path(self, path: list[str]) -> bool:
        """Check if a path is valid (could be command or group)."""
        return self._is_valid_command_path(path) or self._is_valid_group_path(path)

    def _is_valid_command_path(self, path: list[str]) -> bool:
        """Check if a path represents a valid executable command."""
        if not path:
            return False

        if len(path) == 1:
            # Flat command
            cmd_name = path[0]
            return (
                hasattr(self.command_tree, "flat_commands")
                and self.command_tree.flat_commands
                and cmd_name in self.command_tree.flat_commands
            )

        elif len(path) == 2:
            # Hierarchical command
            group_name, cmd_name = path
            return (
                hasattr(self.command_tree, "groups")
                and self.command_tree.groups
                and group_name in self.command_tree.groups
                and "commands" in self.command_tree.groups[group_name]
                and cmd_name in self.command_tree.groups[group_name]["commands"]
            )

        return False

    def _is_valid_group_path(self, path: list[str]) -> bool:
        """Check if a path represents a valid command group."""
        if not path or len(path) != 1:
            return False

        group_name = path[0]
        return (
            hasattr(self.command_tree, "groups")
            and self.command_tree.groups
            and group_name in self.command_tree.groups
        )

    def _is_executable_command(self, path: list[str]) -> bool:
        """Check if a path leads to an executable command (has a function)."""
        cmd_info = self.get_command_info(path)
        return cmd_info is not None and "function" in cmd_info

    def extract_command_and_remaining(self, args: list[str]) -> tuple[list[str], list[str]]:
        """Extract command path and remaining arguments separately."""
        resolved = self.resolve_path(args)
        return resolved.path_elements, resolved.remaining_args

    def find_longest_valid_path(self, args: list[str]) -> list[str]:
        """Find the longest valid command path from arguments."""
        longest_path: list[str] = []

        for i in range(1, min(len(args) + 1, 3)):  # Max depth of 2 (group + command)
            test_path = []
            for j in range(i):
                if j < len(args) and not args[j].startswith("-"):
                    test_path.append(args[j])
                else:
                    break

            if test_path and self._is_valid_path(test_path):
                if len(test_path) > len(longest_path):
                    longest_path = test_path

        return longest_path
