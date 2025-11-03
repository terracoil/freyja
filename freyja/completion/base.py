"""Base classes and data structures for shell completion."""

import argparse
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freyja import FreyjaCLI

# Lazy imports to avoid circular dependency
# FreyjaCLI type will be imported lazily to avoid circular dependency


@dataclass
class CompletionContext:
    """Context information for generating completions."""

    words: list[str]  # All words in current command line
    current_word: str  # Word being completed (partial)
    cursor_position: int  # Position in current word
    command_group_path: list[str]  # Path to current command group (e.g., ['db', 'backup'])
    parser: argparse.ArgumentParser  # Current parser context
    cli: "FreyjaCLI"  # FreyjaCLI instance for introspection


class CompletionHandler(ABC):
    """Abstract base class for shell-specific completion handlers."""

    def __init__(self, cli: "FreyjaCLI"):
        """Initialize completion handler with FreyjaCLI instance.

        :param cli: FreyjaCLI instance to provide completion for
        """
        self.cli = cli

    @abstractmethod
    def generate_script(self, prog_name: str) -> str:
        """Generate shell-specific completion script.

        :param prog_name: Program name for completion
        :return: Shell-specific completion script
        """

    @abstractmethod
    def get_completions(self, context: CompletionContext) -> list[str]:
        """Get completions for current context.

        :param context: Completion context with current state
        :return: List of completion suggestions
        """

    @abstractmethod
    def install_completion(self, prog_name: str) -> bool:
        """Install completion for current shell.

        :param prog_name: Program name to install completion for
        :return: True if installation successful
        """

    def detect_shell(self) -> str | None:
        """Detect current shell from environment."""
        shell = os.environ.get("SHELL", "")
        result = None

        if "bash" in shell:
            result = "bash"
        elif "zsh" in shell:
            result = "zsh"
        elif "fish" in shell:
            result = "fish"
        elif os.name == "nt" or "pwsh" in shell or "powershell" in shell:
            result = "powershell"

        return result

    def complete(self) -> None:
        """Handle completion request and output completions."""
        import importlib  # pylint: disable=import-outside-toplevel

        shell = self.detect_shell()

        if shell:
            # Handle shell-specific completion using importlib to avoid cycles
            if shell == "bash":
                bash_module = importlib.import_module("freyja.completion.bash")
                bash_module.handle_bash_completion()
            elif shell == "zsh":
                zsh_module = importlib.import_module("freyja.completion.zsh")
                zsh_module.handle_zsh_completion()
            else:
                # For other shells, we need to implement completion handling
                # For now, just pass to avoid errors
                pass

    def get_command_group_parser(
        self, parser: argparse.ArgumentParser, command_group_path: list[str]
    ) -> argparse.ArgumentParser | None:
        """Navigate to command group parser following the path.

        :param parser: Root parser to start from
        :param command_group_path: Path to target command group
        :return: Target parser or None if not found
        """
        current_parser = parser
        result = current_parser

        for command_group in command_group_path:
            found_parser = None

            # Look for command group in parser actions
            for action in current_parser._actions:
                if isinstance(action, argparse._SubParsersAction):
                    if command_group in action.choices:
                        found_parser = action.choices[command_group]
                        break

            if not found_parser:
                result = None
                break

            current_parser = found_parser
            result = current_parser

        return result

    def get_available_commands(self, parser: argparse.ArgumentParser) -> list[str]:
        """Get list of available cmd_tree from parser.

        :param parser: Parser to extract cmd_tree from
        :return: List of command names
        """
        commands: list[str] = []

        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                commands.extend(action.choices.keys())

        return commands

    def get_available_options(self, parser: argparse.ArgumentParser) -> list[str]:
        """Get list of available options from parser.

        :param parser: Parser to extract options from
        :return: List of option names (with -- prefix)
        """
        options = []

        for action in parser._actions:
            if action.option_strings:
                # Add long options (prefer --option over -o)
                for option_string in action.option_strings:
                    if option_string.startswith("--"):
                        options.append(option_string)
                        break

        return options

    def get_option_values(
        self, parser: argparse.ArgumentParser, option_name: str, partial: str = ""
    ) -> list[str]:
        """Get possible values for a specific option.

        :param parser: Parser containing the option
        :param option_name: Option to get values for (with -- prefix)
        :param partial: Partial value being completed
        :return: List of possible values
        """
        result = []

        for action in parser._actions:
            if option_name in action.option_strings:
                # Handle enum choices
                if hasattr(action, "choices") and action.choices:
                    if hasattr(action.choices, "__iter__"):
                        # For enum types, get the names
                        try:
                            choices = [choice.name for choice in action.choices]
                            result = self.complete_partial_word(choices, partial)
                        except AttributeError:
                            # Regular choices list
                            choices = list(action.choices)
                            result = self.complete_partial_word(choices, partial)
                elif getattr(action, "action", None) == "store_true":
                    # Handle boolean flags
                    result = []  # No completions for boolean flags
                elif getattr(action, "type", None):
                    # Handle file paths
                    type_name = getattr(action.type, "__name__", str(action.type))
                    if "Path" in type_name or action.type == str:
                        result = self._complete_file_path(partial)

                break  # Exit loop once we find the matching action

        return result

    def _complete_file_path(self, partial: str) -> list[str]:
        """Complete file paths.

        :param partial: Partial path being completed
        :return: List of matching paths
        """
        import glob
        import os

        result = []

        if not partial:
            # No partial path, return current directory contents
            try:
                result = sorted([f for f in os.listdir(".") if not f.startswith(".")])[
                    :10
                ]  # Limit results
            except (OSError, PermissionError):
                result = []
        else:
            # Expand partial path with glob
            try:
                # Handle different path patterns
                if partial.endswith("/") or partial.endswith(os.sep):
                    # Complete directory contents
                    pattern = partial + "*"
                else:
                    # Complete partial filename/dirname
                    pattern = partial + "*"

                matches = glob.glob(pattern)

                # Limit and sort results
                matches = sorted(matches)[:10]

                # Add trailing slash for directories
                for match in matches:
                    if os.path.isdir(match):
                        result.append(match + os.sep)
                    else:
                        result.append(match)

            except (OSError, PermissionError):
                result = []

        return result

    def complete_partial_word(self, candidates: list[str], partial: str) -> list[str]:
        """Filter candidates based on partial word match.

        :param candidates: List of possible completions
        :param partial: Partial word to match against
        :return: Filtered list of completions
        """
        if not partial:
            return candidates

        return [candidate for candidate in candidates if candidate.startswith(partial)]

    def _get_generic_completions(self, context: CompletionContext) -> list[str]:
        """Get generic completions that work across shells.

        :param context: Completion context
        :return: List of completion suggestions
        """
        completions: list[str] = []

        # Get the appropriate parser for current context
        parser = context.parser
        if context.command_group_path:
            parser = self.get_command_group_parser(parser, context.command_group_path)

        # Only proceed if we have a valid parser
        if parser:
            # Determine what we're completing
            current_word = context.current_word

            # Check if we're completing an option value
            if len(context.words) >= 2:
                prev_word = context.words[-2]

                # If previous word is an option, complete its values
                if prev_word.startswith("--"):
                    option_values = self.get_option_values(parser, prev_word, current_word)
                    if option_values:
                        completions = option_values

            # Complete options if current word starts with -- and no completions found yet
            if not completions and current_word.startswith("--"):
                options = self.get_available_options(parser)
                completions = self.complete_partial_word(options, current_word)

            # Complete cmd_tree/command groups if no completions found yet
            if not completions:
                commands = self.get_available_commands(parser)
                if commands:
                    completions = self.complete_partial_word(commands, current_word)

        return completions


def get_completion_handler(cli, shell: str | None = None) -> CompletionHandler:
    """Get appropriate completion handler for shell.

    :param cli: FreyjaCLI instance
    :param shell: Target shell (auto-detect if None)
    :return: Completion handler instance
    """
    import importlib  # pylint: disable=import-outside-toplevel

    # Use importlib to avoid static imports and cyclic import warnings
    handlers = {
        "bash": "freyja.completion.bash.BashCompletionHandler",
        "zsh": "freyja.completion.zsh.ZshCompletionHandler",
        "fish": "freyja.completion.fish.FishCompletionHandler",
        "powershell": "freyja.completion.powershell.PowerShellCompletionHandler",
    }

    detected_shell = shell
    if not detected_shell:
        # Detect shell using a temporary bash handler
        bash_module = importlib.import_module("freyja.completion.bash")
        bash_handler_class = bash_module.BashCompletionHandler
        temp_handler = bash_handler_class(cli)
        detected_shell = temp_handler.detect_shell() or "bash"

    # Get the handler class for the detected shell
    handler_path = handlers.get(detected_shell, handlers["bash"])
    module_path, class_name = handler_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    handler_class = getattr(module, class_name)

    return handler_class(cli)
