# Command parsing functionality extracted from CLI class.
import argparse
from typing import *
from collections import defaultdict

from .command_discovery import CommandInfo
from auto_cli.help.help_formatter import HierarchicalHelpFormatter
from .docstring_parser import extract_function_help
from .argument_parser import ArgumentParserService


class CommandParser:
    """
    Creates and configures ArgumentParser instances for CLI commands.

    Handles both flat command structures and hierarchical command groups
    with proper argument handling and help formatting.
    """

    def __init__(
        self,
        title: str,
        theme=None,
        alphabetize: bool = True,
        enable_completion: bool = False
    ):
        """
        Initialize command parser.

        :param title: CLI application title
        :param theme: Optional theme for colored output
        :param alphabetize: Whether to alphabetize commands and options
        :param enable_completion: Whether to enable shell completion
        """
        self.title = title
        self.theme = theme
        self.alphabetize = alphabetize
        self.enable_completion = enable_completion

    def create_parser(
        self,
        commands: List[CommandInfo],
        target_mode: str,
        target_class: Optional[Type] = None,
        no_color: bool = False
    ) -> argparse.ArgumentParser:
        """
        Create ArgumentParser with all commands and proper configuration.

        :param commands: List of discovered commands
        :param target_mode: Target mode ('module', 'class', or 'multi_class')
        :param target_class: Target class for inner class pattern
        :param no_color: Whether to disable colored output
        :return: Configured ArgumentParser
        """
        # Create effective theme (disable if no_color)
        effective_theme = None if no_color else self.theme

        # For multi-class mode, disable alphabetization to preserve class order
        effective_alphabetize = self.alphabetize and (target_mode != 'multi_class')

        # Create formatter factory
        def create_formatter_with_theme(*args, **kwargs):
            return HierarchicalHelpFormatter(
                *args,
                theme=effective_theme,
                alphabetize=effective_alphabetize,
                **kwargs
            )

        # Create main parser
        parser = argparse.ArgumentParser(
            description=self.title,
            formatter_class=create_formatter_with_theme
        )

        # Add global arguments
        self._add_global_arguments(parser, target_mode, target_class, effective_theme)

        # Group commands by type
        command_groups = self._group_commands(commands)

        # Create subparsers for commands
        subparsers = parser.add_subparsers(
            title='COMMANDS',
            dest='command',
            required=False,
            help='Available commands',
            metavar=''
        )

        # Store theme reference
        subparsers._theme = effective_theme

        # Add commands to parser
        self._add_commands_to_parser(subparsers, command_groups, effective_theme)

        # Apply parser patches for styling and formatter access
        self._apply_parser_patches(parser, effective_theme)

        return parser

    def _add_global_arguments(
        self,
        parser: argparse.ArgumentParser,
        target_mode: str,
        target_class: Optional[Type],
        theme
    ):
        """Add global arguments to the parser."""
        # Add verbose flag for module-based CLIs
        if target_mode == 'module':
            parser.add_argument(
                "-v", "--verbose",
                action="store_true",
                help="Enable verbose output"
            )

        # Add global no-color flag
        parser.add_argument(
            "-n", "--no-color",
            action="store_true",
            help="Disable colored output"
        )

        # Add completion arguments
        if self.enable_completion:
            parser.add_argument(
                "--_complete",
                action="store_true",
                help=argparse.SUPPRESS
            )

        # Add global class arguments for inner class pattern
        if (target_mode == 'class' and
            target_class and
            any(cmd.is_hierarchical for cmd in getattr(self, '_current_commands', []))):
            ArgumentParserService.add_global_class_args(parser, target_class)

    def _group_commands(self, commands: List[CommandInfo]) -> Dict[str, Any]:
        """Group commands by type and hierarchy."""
        groups = {
            'flat': [],
            'hierarchical': defaultdict(list)
        }

        for command in commands:
            if command.is_hierarchical:
                # For multi-class mode, extract group name from command name
                # e.g., "system--completion__handle-completion" -> "system--completion"
                if '--' in command.name and '__' in command.name:
                    # Multi-class hierarchical command
                    group_name = command.name.split('__')[0]  # "system--completion"
                else:
                    # Single-class hierarchical command - convert to kebab-case
                    from auto_cli.utils.string_utils import StringUtils
                    group_name = StringUtils.kebab_case(command.parent_class)  # "Completion" -> "completion"

                groups['hierarchical'][group_name].append(command)
            else:
                groups['flat'].append(command)

        return groups

    def _add_commands_to_parser(
        self,
        subparsers,
        command_groups: Dict[str, Any],
        theme
    ):
        """Add all commands to the parser."""
        # Store current commands for global arg detection
        self._current_commands = []
        for flat_cmd in command_groups['flat']:
            self._current_commands.append(flat_cmd)
        for group_cmds in command_groups['hierarchical'].values():
            self._current_commands.extend(group_cmds)

        # Add flat commands
        for command in command_groups['flat']:
            self._add_flat_command(subparsers, command, theme)

        # Add hierarchical command groups
        for group_name, group_commands in command_groups['hierarchical'].items():
            self._add_command_group(subparsers, group_name, group_commands, theme)

    def _add_flat_command(self, subparsers, command: CommandInfo, theme):
        """Add a flat command to the parser."""
        desc, _ = extract_function_help(command.function)

        def create_formatter_with_theme(*args, **kwargs):
            return HierarchicalHelpFormatter(
                *args,
                theme=theme,
                alphabetize=self.alphabetize,
                **kwargs
            )

        sub = subparsers.add_parser(
            command.name,
            help=desc,
            description=desc,
            formatter_class=create_formatter_with_theme
        )
        sub._command_type = 'command'
        sub._theme = theme

        # Add function arguments
        ArgumentParserService.add_function_args(sub, command.function)

        # Set defaults
        defaults = {
            '_cli_function': command.function,
            '_function_name': command.original_name
        }

        if command.is_system_command:
            defaults['_is_system_command'] = True

        sub.set_defaults(**defaults)

    def _add_command_group(
        self,
        subparsers,
        group_name: str,
        group_commands: List[CommandInfo],
        theme
    ):
        """Add a command group with subcommands."""
        # Get group description from inner class or generate default
        group_help = self._get_group_help(group_name, group_commands)
        inner_class = self._get_inner_class_for_group(group_commands)

        def create_formatter_with_theme(*args, **kwargs):
            return HierarchicalHelpFormatter(
                *args,
                theme=theme,
                alphabetize=self.alphabetize,
                **kwargs
            )

        # Create group parser
        group_parser = subparsers.add_parser(
            group_name,
            help=group_help,
            formatter_class=create_formatter_with_theme
        )

        # Configure group parser
        group_parser._command_type = 'group'
        group_parser._theme = theme
        group_parser._command_group_description = group_help

        # Add sub-global arguments from inner class
        if inner_class:
            ArgumentParserService.add_subglobal_class_args(
                group_parser, inner_class, group_name
            )

        # Store command help information
        command_help = {}
        for command in group_commands:
            desc, _ = extract_function_help(command.function)
            # Remove the group prefix from command name for display
            display_name = command.name.split('__', 1)[-1] if '__' in command.name else command.name
            command_help[display_name] = desc

        group_parser._commands = command_help

        # Create subparsers for group commands
        dest_name = f'{group_name}_command'
        sub_subparsers = group_parser.add_subparsers(
            title=f'{group_name.title().replace("-", " ")} COMMANDS',
            dest=dest_name,
            required=False,
            help=f'Available {group_name} commands',
            metavar=''
        )

        sub_subparsers._enhanced_help = True
        sub_subparsers._theme = theme

        # Add individual commands to the group
        for command in group_commands:
            # Remove group prefix from command name
            command_name = command.name.split('__', 1)[-1] if '__' in command.name else command.name
            self._add_group_command(sub_subparsers, command_name, command, theme)

    def _add_group_command(self, subparsers, command_name: str, command: CommandInfo, theme):
        """Add an individual command within a group."""
        desc, _ = extract_function_help(command.function)

        def create_formatter_with_theme(*args, **kwargs):
            return HierarchicalHelpFormatter(
                *args,
                theme=theme,
                alphabetize=self.alphabetize,
                **kwargs
            )

        sub = subparsers.add_parser(
            command_name,
            help=desc,
            description=desc,
            formatter_class=create_formatter_with_theme
        )
        sub._command_type = 'command'
        sub._theme = theme

        # Add function arguments
        ArgumentParserService.add_function_args(sub, command.function)

        # Set defaults
        # For hierarchical commands, use the full command name so executor can find metadata
        function_name = command.name if command.is_hierarchical else command.original_name
        defaults = {
            '_cli_function': command.function,
            '_function_name': function_name
        }

        if command.command_path:
            defaults['_command_path'] = command.command_path

        if command.is_system_command:
            defaults['_is_system_command'] = True

        sub.set_defaults(**defaults)

    def _get_group_help(self, group_name: str, group_commands: List[CommandInfo]) -> str:
        """Get help text for a command group."""
        # Try to get description from inner class
        for command in group_commands:
            if command.inner_class and hasattr(command.inner_class, '__doc__'):
                if command.inner_class.__doc__:
                    return command.inner_class.__doc__.strip().split('\n')[0]

        # Default description
        return f"{group_name.title().replace('-', ' ')} operations"

    def _get_inner_class_for_group(self, group_commands: List[CommandInfo]) -> Optional[Type]:
        """Get the inner class for a command group."""
        for command in group_commands:
            if command.inner_class:
                return command.inner_class

        return None

    def _apply_parser_patches(self, parser: argparse.ArgumentParser, theme):
        """Apply patches to parser for enhanced functionality."""
        # Patch formatter to have access to parser actions
        def patch_formatter_with_parser_actions():
            original_get_formatter = parser._get_formatter

            def patched_get_formatter():
                formatter = original_get_formatter()
                formatter._parser_actions = parser._actions
                return formatter

            parser._get_formatter = patched_get_formatter

        # Patch help formatting for title styling
        original_format_help = parser.format_help

        def patched_format_help():
            original_help = original_format_help()

            if theme and self.title in original_help:
                from auto_cli.theme import ColorFormatter
                color_formatter = ColorFormatter()
                styled_title = color_formatter.apply_style(self.title, theme.title)
                original_help = original_help.replace(self.title, styled_title)

            return original_help

        parser.format_help = patched_format_help

        # Apply formatter patch
        patch_formatter_with_parser_actions()
