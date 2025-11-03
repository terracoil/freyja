"""Positional parameter handling for CLI commands."""

import inspect
from typing import Any

from freyja.utils.text_util import TextUtil
from .docstring_parser import DocStringParser
from .argument_preprocessor import PositionalInfo


class PositionalHandler:
    """Handles positional parameter detection, validation, and conversion."""

    def __init__(self, positional_info: dict[str, PositionalInfo]):
        """Initialize positional handler with discovered positional parameters."""
        # Guard: Ensure positional_info is not None
        if positional_info is None:
            raise ValueError("positional_info cannot be None")
        
        self.positional_info = positional_info

    def identify_positional_value(
        self, args: list[str], command_path: list[str]
    ) -> tuple[str, str] | None:
        """Identify positional value in argument list."""
        # Guard: Ensure args is not None
        if args is None:
            raise ValueError("args cannot be None")
        
        # Guard: Ensure command_path is not None
        if command_path is None:
            raise ValueError("command_path cannot be None")
        if not command_path:
            return None

        # Get the command name
        command_name = self._get_command_name_from_path(command_path)
        if not command_name or command_name not in self.positional_info:
            return None

        pos_info = self.positional_info[command_name]

        # Look for positional value after command path
        search_start = len(command_path)

        for i in range(search_start, len(args)):
            arg = args[i]

            # Skip option flags and their values
            if arg.startswith("-"):
                # Skip this flag and potentially its value
                if self._flag_has_value(arg, args, i):
                    i += 1  # Skip the value too
                continue

            # Found a positional argument
            return (pos_info.param_name, arg)

        return None

    def convert_positional_to_flag(self, param_name: str, param_value: str) -> list[str]:
        """Convert positional parameter to flag format."""
        # Guard: Ensure param_name is not empty
        if not param_name or (isinstance(param_name, str) and not param_name.strip()):
            raise ValueError("param_name cannot be empty")
        
        # Guard: Ensure param_value is not None
        if param_value is None:
            raise ValueError("param_value cannot be None")
        flag_name = TextUtil.kebab_case(param_name)
        return [f"--{flag_name}", param_value]

    def validate_positional_value(
        self, param_name: str, param_value: str, param_type: type
    ) -> tuple[bool, str | None]:
        """Validate positional parameter value matches expected type."""
        # Guard: Ensure param_name is not empty
        if not param_name or (isinstance(param_name, str) and not param_name.strip()):
            raise ValueError("param_name cannot be empty")
        
        # Guard: Ensure param_value is not None
        if param_value is None:
            raise ValueError("param_value cannot be None")
        
        # Guard: Ensure param_type is not None
        if param_type is None:
            raise ValueError("param_type cannot be None")
        if param_type == str:
            return True, None

        if param_type == int:
            try:
                int(param_value)
                return True, None
            except ValueError:
                return False, f"Expected integer for {param_name}, got: {param_value}"

        if param_type == float:
            try:
                float(param_value)
                return True, None
            except ValueError:
                return False, f"Expected float for {param_name}, got: {param_value}"

        if param_type == bool:
            # Boolean positional parameters are tricky - typically they should be flags
            # But if specified, treat common boolean strings
            if param_value.lower() in ("true", "false", "1", "0", "yes", "no"):
                return True, None
            return (
                False,
                f"Expected boolean (true/false, 1/0, yes/no) "
                f"for {param_name}, got: {param_value}",
            )

        # For other types, just accept the string - argparse will handle conversion
        return True, None

    def generate_positional_usage(self, command_name: str) -> str:
        """Generate usage text showing positional parameter."""
        # Guard: Ensure command_name is not empty
        if not command_name or (isinstance(command_name, str) and not command_name.strip()):
            raise ValueError("command_name cannot be empty")
        if command_name not in self.positional_info:
            return ""

        pos_info = self.positional_info[command_name]
        param_display = pos_info.param_name.upper()

        if pos_info.is_required:
            return param_display
        else:
            return f"[{param_display}]"

    def has_positional_parameter(self, command_name: str) -> bool:
        """Check if a command has a positional parameter."""
        return command_name in self.positional_info

    def get_positional_info(self, command_name: str) -> PositionalInfo | None:
        """Get positional parameter info for a command."""
        return self.positional_info.get(command_name)

    def extract_and_convert_positional(
        self, args: list[str], command_path: list[str]
    ) -> tuple[list[str], bool]:
        """Extract positional argument and convert to flag format."""
        if not command_path:
            return args, False

        command_name = self._get_command_name_from_path(command_path)
        if not command_name or command_name not in self.positional_info:
            return args, False

        pos_info = self.positional_info[command_name]
        modified_args = args.copy()
        conversion_made = False

        # Find and convert positional argument
        search_start = len(command_path)

        for i in range(search_start, len(modified_args)):
            arg = modified_args[i]

            # Skip option flags and their values
            if arg.startswith("-"):
                if self._flag_has_value(arg, modified_args, i):
                    i += 1  # Skip the value too
                continue

            # Found positional argument - convert it
            flag_name = TextUtil.kebab_case(pos_info.param_name)

            # Validate before conversion
            is_valid, error_msg = self.validate_positional_value(
                pos_info.param_name, arg, pos_info.param_type
            )

            if not is_valid:
                raise ValueError(error_msg)

            # Replace positional with flag format
            modified_args[i] = f"--{flag_name}"
            modified_args.insert(i + 1, arg)
            conversion_made = True

            break

        return modified_args, conversion_made

    def _get_command_name_from_path(self, command_path: list[str]) -> str | None:
        """Get standardized command name from command path."""
        if not command_path:
            return None

        if len(command_path) == 1:
            return command_path[0]
        elif len(command_path) == 2:
            return f"{command_path[0]}--{command_path[1]}"

        return None

    def _flag_has_value(self, flag: str, args: list[str], flag_index: int) -> bool:
        """Check if a flag expects a value (not a store_true flag)."""
        # Simple heuristic: if next arg exists and doesn't start with '-', it's probably a value
        if flag_index + 1 < len(args):
            next_arg = args[flag_index + 1]
            if not next_arg.startswith("-"):
                return True

        # Check for known store_true flags (flags that don't take values)
        store_true_flags = {
            "--help",
            "-h",
            "--verbose",
            "-v",
            "--no-color",
            "-n",
            "--dry-run",
            "--force",
            "--debug",
            "--quiet",
            "-q",
            "--excited",
            "--backup",
            "--compress",
            "--detailed",
            "--parallel",
            "--preserve-original",
            "--include-metadata",
        }

        return flag not in store_true_flags

    @staticmethod
    def discover_from_function(function: Any) -> PositionalInfo | None:
        """Discover positional parameter from function signature."""
        if not function:
            return None

        try:
            sig = inspect.signature(function)
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                # First parameter without default becomes positional
                if param.default == param.empty:
                    # Get help text from function docstring
                    _, param_help = DocStringParser.extract_function_help(function)
                    help_text = DocStringParser.create_parameter_help(
                        param_name, param_help, param.annotation, param.default
                    )
                    
                    return PositionalInfo(
                        param_name=param_name,
                        param_type=param.annotation if param.annotation != param.empty else str,
                        is_required=True,
                        help_text=help_text,
                    )
        except (ValueError, TypeError):
            # Handle cases where signature inspection fails
            pass

        return None

    @staticmethod
    def discover_from_command_tree(command_tree) -> dict[str, PositionalInfo]:
        """Discover all positional parameters from a command tree."""
        positional_params = {}

        # Discover from flat commands
        if hasattr(command_tree, "flat_commands") and command_tree.flat_commands:
            for cmd_name, cmd_info in command_tree.flat_commands.items():
                if "function" in cmd_info:
                    pos_info = PositionalHandler.discover_from_function(cmd_info["function"])
                    if pos_info:
                        positional_params[cmd_name] = pos_info

        # Discover from grouped commands
        if hasattr(command_tree, "groups") and command_tree.groups:
            for group_name, group_info in command_tree.groups.items():
                if "commands" in group_info:
                    for cmd_name, cmd_info in group_info["commands"].items():
                        full_cmd_name = f"{group_name}--{cmd_name}"
                        if "function" in cmd_info:
                            pos_info = PositionalHandler.discover_from_function(
                                cmd_info["function"]
                            )
                            if pos_info:
                                positional_params[full_cmd_name] = pos_info

        return positional_params
