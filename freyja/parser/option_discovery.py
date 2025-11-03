"""Option discovery service for mapping options and identifying positional parameters."""

import inspect
from typing import Any

from freyja.utils.text_util import TextUtil
from .docstring_parser import DocStringParser
from .argument_preprocessor import PositionalInfo


class OptionDiscovery:
    """Discovers and categorizes all possible CLI options AND positional parameters by scope."""

    def __init__(self, command_tree, target_class: type | None = None):
        """Initialize option discovery service."""
        self.command_tree = command_tree
        self.target_class = target_class

    def discover_global_options(self) -> set[str]:
        """Discover global options from main class constructor."""
        if not self.target_class:
            return set()

        return self._analyze_constructor_params(self.target_class)

    def discover_subglobal_options(self) -> dict[str, set[str]]:
        """Discover sub-global options from inner class constructors."""
        subglobal_options: dict[str, set[str]] = {}

        if not hasattr(self.command_tree, "groups") or not self.command_tree.groups:
            return subglobal_options

        for group_name, group_info in self.command_tree.groups.items():
            if "inner_class" in group_info and group_info["inner_class"]:
                inner_class = group_info["inner_class"]
                subglobal_options[group_name] = self._analyze_inner_class_params(inner_class)

        return subglobal_options

    def discover_command_options(self) -> dict[str, set[str]]:
        """Discover command-specific options from function signatures."""
        command_options = {}

        # Discover from flat commands
        if hasattr(self.command_tree, "flat_commands") and self.command_tree.flat_commands:
            for cmd_name, cmd_info in self.command_tree.flat_commands.items():
                if "function" in cmd_info:
                    command_options[cmd_name] = self._analyze_function_params(cmd_info["function"])

        # Discover from grouped commands
        if hasattr(self.command_tree, "groups") and self.command_tree.groups:
            for group_name, group_info in self.command_tree.groups.items():
                if "commands" in group_info:
                    for cmd_name, cmd_info in group_info["commands"].items():
                        full_cmd_name = f"{group_name}--{cmd_name}"
                        if "function" in cmd_info:
                            command_options[full_cmd_name] = self._analyze_function_params(
                                cmd_info["function"]
                            )

        return command_options

    def discover_positional_parameters(self) -> dict[str, PositionalInfo]:
        """Discover positional parameters from function signatures."""
        positional_params = {}

        # Discover from flat commands
        if hasattr(self.command_tree, "flat_commands") and self.command_tree.flat_commands:
            for cmd_name, cmd_info in self.command_tree.flat_commands.items():
                if "function" in cmd_info:
                    pos_info = self._find_positional_parameter(cmd_info["function"])
                    if pos_info:
                        positional_params[cmd_name] = pos_info

        # Discover from grouped commands
        if hasattr(self.command_tree, "groups") and self.command_tree.groups:
            for group_name, group_info in self.command_tree.groups.items():
                if "commands" in group_info:
                    for cmd_name, cmd_info in group_info["commands"].items():
                        full_cmd_name = f"{group_name}--{cmd_name}"
                        if "function" in cmd_info:
                            pos_info = self._find_positional_parameter(cmd_info["function"])
                            if pos_info:
                                positional_params[full_cmd_name] = pos_info

        return positional_params

    def get_all_known_options(self, command_path: list[str] | None = None) -> set[str]:
        """Get all known options for a given command path."""
        all_options = set()

        # Add global options
        all_options.update(self.discover_global_options())

        # Add subglobal options for current path
        if command_path and len(command_path) > 0:
            subglobal_opts = self.discover_subglobal_options()
            group_name = command_path[0]
            if group_name in subglobal_opts:
                all_options.update(subglobal_opts[group_name])

        # Add command options for current command
        if command_path:
            command_opts = self.discover_command_options()
            if len(command_path) == 1:
                cmd_name = command_path[0]
            elif len(command_path) == 2:
                cmd_name = f"{command_path[0]}--{command_path[1]}"
            else:
                return all_options

            if cmd_name in command_opts:
                all_options.update(command_opts[cmd_name])

        # Add built-in options
        built_in_options = {"--help", "-h", "--no-color", "-n", "--verbose", "-v", "--_complete"}
        all_options.update(built_in_options)

        return all_options

    def _analyze_constructor_params(self, target_class: type) -> set[str]:
        """Analyze class constructor parameters to extract option names."""
        options = set()

        try:
            sig = inspect.signature(target_class.__init__)
            for param_name, _param in sig.parameters.items():
                if param_name == "self":
                    continue
                flag_name = TextUtil.kebab_case(param_name)
                options.add(f"--{flag_name}")
        except (ValueError, TypeError):
            # Handle cases where signature inspection fails
            pass

        return options

    def _analyze_inner_class_params(self, inner_class: type) -> set[str]:
        """Analyze inner class constructor parameters to extract sub-global option names."""
        options = set()

        try:
            sig = inspect.signature(inner_class.__init__)
            params = list(sig.parameters.items())
            # Skip self (index 0) and main (index 1), start from index 2
            for param_name, _param in params[2:]:
                flag_name = TextUtil.kebab_case(param_name)
                options.add(f"--{flag_name}")
        except (ValueError, TypeError):
            # Handle cases where signature inspection fails
            pass

        return options

    def _analyze_function_params(self, function: Any) -> set[str]:
        """Analyze function parameters to extract command option names."""
        options: set[str] = set()

        if not function:
            return options

        try:
            sig = inspect.signature(function)
            for param_name, _param in sig.parameters.items():
                if param_name == "self":
                    continue
                flag_name = TextUtil.kebab_case(param_name)
                options.add(f"--{flag_name}")
        except (ValueError, TypeError):
            # Handle cases where signature inspection fails
            pass

        return options

    def _find_positional_parameter(self, function: Any) -> PositionalInfo | None:
        """Find the first non-default parameter as positional parameter."""
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

    def validate_option_conflicts(self) -> dict[str, list[str]]:
        """Detect option name conflicts across different scopes."""
        conflicts = {}

        global_options = self.discover_global_options()
        subglobal_options = self.discover_subglobal_options()
        command_options = self.discover_command_options()

        # Check for conflicts between global and subglobal
        for group_name, group_options in subglobal_options.items():
            overlapping = global_options.intersection(group_options)
            if overlapping:
                conflicts[f"global vs {group_name}"] = list(overlapping)

        # Check for conflicts between subglobal groups
        group_names = list(subglobal_options.keys())
        for i in range(len(group_names)):
            for j in range(i + 1, len(group_names)):
                group1, group2 = group_names[i], group_names[j]
                overlapping = subglobal_options[group1].intersection(subglobal_options[group2])
                if overlapping:
                    conflicts[f"{group1} vs {group2}"] = list(overlapping)

        # Check for conflicts between command options in same scope
        command_conflicts = {}
        for cmd_name, cmd_options in command_options.items():
            for other_cmd, other_options in command_options.items():
                if cmd_name != other_cmd and cmd_name.split("--")[0] == other_cmd.split("--")[0]:
                    # Same group, check for conflicts
                    overlapping = cmd_options.intersection(other_options)
                    if overlapping:
                        pair_key = f"{cmd_name} vs {other_cmd}"
                        if pair_key not in command_conflicts:
                            command_conflicts[pair_key] = list(overlapping)

        conflicts.update(command_conflicts)

        return conflicts

    def suggest_option_corrections(
        self, unknown_option: str, command_path: list[str] | None = None
    ) -> list[str]:
        """Suggest corrections for unknown options using similarity matching."""
        all_options = self.get_all_known_options(command_path)

        suggestions = []

        # Simple string similarity matching
        for option in all_options:
            if self._calculate_similarity(unknown_option, option) > 0.6:
                suggestions.append(option)

        # Sort by similarity score
        suggestions.sort(key=lambda x: self._calculate_similarity(unknown_option, x), reverse=True)

        return suggestions[:3]  # Return top 3 suggestions

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple string similarity score."""
        if not s1 or not s2:
            return 0.0

        # Remove leading dashes for comparison
        s1_clean = s1.lstrip("-")
        s2_clean = s2.lstrip("-")

        if s1_clean == s2_clean:
            return 1.0

        # Simple character overlap scoring
        s1_chars = set(s1_clean.lower())
        s2_chars = set(s2_clean.lower())

        if not s1_chars or not s2_chars:
            return 0.0

        intersection = s1_chars.intersection(s2_chars)
        union = s1_chars.union(s2_chars)

        return len(intersection) / len(union)
