"""Argument preprocessor for flexible option ordering and positional parameter support."""

import inspect
from dataclasses import dataclass
from typing import Any

from freyja.shared.command_tree import CommandTree
from freyja.parser.docstring_parser import DocStringParser
from freyja.utils.text_util import TextUtil


@dataclass
class PositionalInfo:
    """Information about a positional parameter."""

    param_name: str
    param_type: type
    is_required: bool
    help_text: str | None = None


class ArgumentPreprocessor:
    """Preprocesses args for flexible option ordering AND positional support."""

    def __init__(self, command_tree: CommandTree, target_class: type | None = None):
        """Initialize the preprocessor with command tree and target class info."""
        # Guard: Ensure command_tree is not None
        if command_tree is None:
            raise ValueError("command_tree cannot be None")
        
        self.command_tree = command_tree
        self.target_class = target_class
        self._global_options: set[str] = set()
        self._subglobal_options: dict[str, set[str]] = {}  # group_name -> set of options
        self._command_options: dict[str, set[str]] = {}  # command_name -> set of options
        self._positional_params: dict[str, PositionalInfo] = (
            {}
        )  # command_name -> positional parameter info
        self._build_option_maps()
        self._build_positional_maps()

    def validate_arguments(self, args: list[str]) -> tuple[bool, list[str]]:
        """Validate arguments before preprocessing."""
        # Guard: Ensure args is not None
        if args is None:
            raise ValueError("args cannot be None")
        
        errors = []

        # Basic validation - check for obviously malformed arguments
        for i, arg in enumerate(args):
            if arg.startswith("--") and "=" in arg:
                # Handle --flag=value format
                flag_part = arg.split("=")[0]
                if not self._is_known_option(flag_part):
                    errors.append(f"Unknown option: {flag_part}")
            elif arg.startswith("--") and not self._is_known_option(arg):
                # Check if next arg exists and isn't a flag (for --flag value format)
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    continue  # This is likely --flag value format, will be validated later
                errors.append(f"Unknown option: {arg}")

        return len(errors) == 0, errors

    def preprocess_args(self, args: list[str]) -> list[str]:
        """Reorder arguments to match argparse hierarchical expectations."""
        # Guard: Ensure args is not None
        if args is None:
            raise ValueError("args cannot be None")
        
        # Parse command structure from positional arguments
        command_path = self._extract_command_path(args)

        # Convert flag-style positional params to positional args (compatibility)
        args_with_converted_positionals = self._convert_positional_flags_to_positional(
            args, command_path
        )

        # Categorize options by scope
        categorized_args = self._categorize_arguments(args_with_converted_positionals, command_path)

        # Reorder arguments: global -> group -> command -> remaining positionals
        return self._reorder_arguments(categorized_args, command_path)

    def _build_option_maps(self) -> None:
        """Build maps of which options belong to which scope."""
        # Build global options from target class constructor
        if self.target_class:
            self._global_options = self._extract_constructor_options(self.target_class)
        else:
            # Fallback global options
            self._global_options = {"-n", "--no-color", "-h", "--help"}

        # Build sub-global options from inner classes and command options
        if self.command_tree:
            for group_name, group_info in self.command_tree.tree.items():
                if group_info.get("type") == "group":
                    # This is a group, check for inner_class
                    if group_info.get("inner_class"):
                        self._subglobal_options[group_name] = self._extract_constructor_options(
                            group_info["inner_class"], skip_params=1
                        )

                    # Process commands within the group
                    if "cmd_tree" in group_info:
                        for cmd_name, cmd_info in group_info["cmd_tree"].items():
                            if cmd_info.get("type") == "command" and cmd_info.get("function"):
                                full_cmd_name = (
                                    f"{group_name}--{cmd_name}"  # Use double-dash format
                                )
                                self._command_options[full_cmd_name] = (
                                    self._extract_function_options(cmd_info["function"])
                                )
                elif group_info.get("type") == "command":
                    # This is a flat command
                    if group_info.get("function"):
                        self._command_options[group_name] = self._extract_function_options(
                            group_info["function"]
                        )

    def _build_positional_maps(self) -> None:
        """Build maps of positional parameters for each command."""
        if not self.command_tree:
            return

        for group_name, group_info in self.command_tree.tree.items():
            if group_info.get("type") == "group":
                # Process commands within the group
                if "cmd_tree" in group_info:
                    for cmd_name, cmd_info in group_info["cmd_tree"].items():
                        if cmd_info.get("type") == "command" and cmd_info.get("function"):
                            full_cmd_name = f"{group_name}--{cmd_name}"  # Use double-dash format
                            positional_info = self._extract_positional_parameter(
                                cmd_info["function"]
                            )
                            if positional_info:
                                self._positional_params[full_cmd_name] = positional_info
            elif group_info.get("type") == "command":
                # This is a flat command
                if group_info.get("function"):
                    positional_info = self._extract_positional_parameter(group_info["function"])
                    if positional_info:
                        self._positional_params[group_name] = positional_info

    def _extract_constructor_options(self, cls: type, skip_params: int = 1) -> set[str]:
        """Extract options from class constructor."""
        # Guard: Ensure cls is not None
        if cls is None:
            raise ValueError("cls cannot be None")
        
        options: set[str] = set()
        if not hasattr(cls, "__init__"):
            return options

        sig = inspect.signature(cls.__init__)
        params = list(sig.parameters.items())

        # Skip 'self' and potentially other params (like 'main' in inner classes)
        for param_name, param in params[skip_params:]:
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            flag_name = f"--{TextUtil.kebab_case(param_name)}"
            options.add(flag_name)

        return options

    def _extract_function_options(self, func: Any) -> set[str]:
        """Extract options from function signature."""
        # Guard: Ensure func is not None
        if func is None:
            raise ValueError("func cannot be None")
        
        options = set()
        sig = inspect.signature(func)

        for param_name, param in sig.parameters.items():
            if param_name == "self" or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            # Skip positional parameters (first param without default)
            if self._is_first_non_default_param(func, param_name):
                continue

            flag_name = f"--{TextUtil.kebab_case(param_name)}"
            options.add(flag_name)

        return options

    def _extract_positional_parameter(self, func: Any) -> PositionalInfo | None:
        """Extract positional parameter info from function signature."""
        # Guard: Ensure func is not None
        if func is None:
            raise ValueError("func cannot be None")
        
        sig = inspect.signature(func)
        _, param_help = DocStringParser.extract_function_help(func)

        for param_name, param in sig.parameters.items():
            if param_name == "self" or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            # First parameter without default value becomes positional
            if param.default == param.empty:
                help_text = DocStringParser.create_parameter_help(
                    param_name, param_help, param.annotation, param.default
                )
                return PositionalInfo(
                    param_name=param_name,
                    param_type=param.annotation if param.annotation != param.empty else str,
                    is_required=True,
                    help_text=help_text,
                )

        return None

    def _is_first_non_default_param(self, func: Any, param_name: str) -> bool:
        """Check if this is the first parameter without a default value."""
        # Guard: Ensure func is not None
        if func is None:
            raise ValueError("func cannot be None")
        
        # Guard: Ensure param_name is not None
        if param_name is None:
            raise ValueError("param_name cannot be None")
        
        sig = inspect.signature(func)

        for name, param in sig.parameters.items():
            if name == "self" or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            if param.default == param.empty:
                return name == param_name  # This is the first non-default param

        return False

    def _extract_command_path(self, args: list[str]) -> list[str]:
        """Extract hierarchical command path from arguments."""
        command_path: list[str] = []

        for arg in args:
            if arg.startswith("-"):
                break  # Stop at first option

            # Check if this arg is a valid command/group name
            if self._is_command_or_group(command_path + [arg]):
                command_path.append(arg)
            else:
                # This might be a positional parameter, stop building command path
                break

        return command_path

    def _is_command_or_group(self, path: list[str]) -> bool:
        """Check if the given path represents a valid command or group."""
        if not self.command_tree or not path:
            return False

        # Check if it's a group
        if len(path) == 1 and path[0] in self.command_tree.tree:
            group_info = self.command_tree.tree[path[0]]
            if group_info.get("type") == "group":
                return True

        # Check if it's a command (full path)
        if len(path) >= 2:
            "--".join(path)  # Inner class commands use double-dash
            # Check in the command tree structure
            group_name = path[0]
            if group_name in self.command_tree.tree:
                group_info = self.command_tree.tree[group_name]
                if group_info.get("type") == "group" and "cmd_tree" in group_info:
                    cmd_name = path[1]
                    if cmd_name in group_info["cmd_tree"]:
                        return True

        # Check if it's a flat command
        if len(path) == 1 and path[0] in self.command_tree.tree:
            cmd_info = self.command_tree.tree[path[0]]
            if cmd_info.get("type") == "command":
                return True

        return False

    def _convert_positional_flags_to_positional(
        self, args: list[str], command_path: list[str]
    ) -> list[str]:
        """Convert flag-style positional parameters back to positional for backward compatibility.

        Example: ['function-with-types', '--text', 'hello'] -> ['function-with-types', 'hello']
        """
        if not command_path:
            return args

        # Get the appropriate command name
        command_name = (
            "--".join(command_path)
            if len(command_path) > 1
            else command_path[0] if command_path else None
        )
        if not command_name:
            return args

        # Check if this command has a positional parameter
        positional_info = self._positional_params.get(command_name)
        if not positional_info:
            return args

        # Look for the flag version of the positional parameter
        flag_name = f"--{TextUtil.kebab_case(positional_info.param_name)}"
        result_args = args.copy()

        # Find flag and its value, convert to positional
        i = 0
        while i < len(result_args) - 1:  # -1 because we need to check next element
            if result_args[i] == flag_name:
                # Found the flag, next element should be the value
                if i + 1 < len(result_args) and not result_args[i + 1].startswith("-"):
                    flag_value = result_args[i + 1]
                    # Remove the flag and its value
                    result_args.pop(i)  # Remove flag
                    result_args.pop(i)  # Remove value (index shifts after first pop)
                    # Find where to insert the positional value (after command path)
                    insert_position = len(command_path)
                    result_args.insert(insert_position, flag_value)
                    break
            i += 1

        return result_args

    def _handle_positional_parameters(self, args: list[str], command_path: list[str]) -> list[str]:
        """Convert positional parameters to flag format for argparse compatibility."""
        if not command_path:
            return args

        # Get command name (for flat commands or hierarchical commands)
        if len(command_path) == 1:
            command_name = command_path[0]
        else:
            command_name = "--".join(command_path)

        # Check if this command has a positional parameter
        positional_info = self._positional_params.get(command_name)
        if not positional_info:
            return args

        # Find the positional value in the args
        result_args = args.copy()
        command_path_end = len(command_path)
        flag_name = f"--{TextUtil.kebab_case(positional_info.param_name)}"

        # Look for positional value after command path
        i = command_path_end
        while i < len(args):
            arg = args[i]

            # Skip options and their values
            if arg.startswith("-"):
                # Check if this is the flag we're looking for
                if arg == flag_name:
                    # The flag already exists, no need to convert positional
                    return args

                # Skip this option and its value if it exists
                i += 1
                if i < len(args) and not args[i].startswith("-"):
                    i += 1  # Skip the option value
                continue

            # This is a potential positional value
            # Replace positional value with flag format
            result_args[i : i + 1] = [flag_name, arg]
            break

        return result_args

    def _categorize_arguments(
        self, args: list[str], command_path: list[str]
    ) -> dict[str, list[str]]:
        """Categorize arguments by scope (global, sub-global, command)."""
        categorized = {
            "global": [],
            "subglobal": [],
            "command": [],
            "positional": command_path.copy(),
        }

        i = 0
        # Skip command path
        while i < len(args) and i < len(command_path):
            if args[i] == command_path[i]:
                i += 1
            else:
                break

        # Categorize remaining arguments
        while i < len(args):
            arg = args[i]

            if not arg.startswith("-"):
                # Non-option argument, probably a value
                categorized["command"].append(arg)
                i += 1
                continue

            # This is an option, determine its scope
            if arg in self._global_options:
                categorized["global"].append(arg)
                # Check if it has a value
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    categorized["global"].append(args[i + 1])
                    i += 2
                else:
                    i += 1
            elif self._is_subglobal_option(arg, command_path):
                categorized["subglobal"].append(arg)
                # Check if it has a value
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    categorized["subglobal"].append(args[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                # Assume it's a command option
                categorized["command"].append(arg)
                # Check if it has a value
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    categorized["command"].append(args[i + 1])
                    i += 2
                else:
                    i += 1

        return categorized

    def _is_subglobal_option(self, option: str, command_path: list[str]) -> bool:
        """Check if an option is a sub-global option for the current command path."""
        if not command_path:
            return False

        group_name = command_path[0]  # First element is the group
        return (
            group_name in self._subglobal_options and option in self._subglobal_options[group_name]
        )

    def _reorder_arguments(
        self, categorized: dict[str, list[str]], command_path: list[str]
    ) -> list[str]:
        """Reorder arguments into hierarchical format for argparse.

        For hierarchical commands, sub-global options must come after the group
        but before the subcommand for argparse to recognize them correctly.

        Examples:
          - Flat command: [global_opts] [command] [sub_global_opts] [command_opts]
          - Hierarchical: [global_opts] [group] [sub_global_opts] [subcommand] [command_opts]
        """
        reordered = []

        # Add global options first
        reordered.extend(categorized["global"])

        # For hierarchical commands (path length > 1), insert sub-global options
        # between the group and subcommand
        if len(command_path) > 1:
            # Add group (first element of path)
            reordered.append(command_path[0])

            # Add sub-global options after group
            reordered.extend(categorized["subglobal"])

            # Add remaining command path elements (subcommands)
            reordered.extend(command_path[1:])
        else:
            # For flat commands, add command path first
            reordered.extend(categorized["positional"])

            # Then sub-global options (if any)
            reordered.extend(categorized["subglobal"])

        # Add command-specific options last
        reordered.extend(categorized["command"])

        return reordered

    def _is_known_option(self, option: str) -> bool:
        """Check if an option is known in any scope."""
        if option in self._global_options:
            return True

        for group_options in self._subglobal_options.values():
            if option in group_options:
                return True

        for command_options in self._command_options.values():
            if option in command_options:
                return True

        # Check for built-in options
        builtin_options = {"--help", "-h", "--no-color", "-n"}
        if option in builtin_options:
            return True

        return False
