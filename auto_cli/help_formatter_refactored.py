# Refactored Help Formatter with reduced duplication and single return points
import argparse
import os
import re
import textwrap
from typing import List, Optional, Tuple, Dict, Any

from .help_formatting_engine import HelpFormattingEngine


class FormatPatterns:
    """Common formatting patterns extracted to eliminate duplication."""
    
    @staticmethod
    def format_section_title(title: str, style_func=None) -> str:
        """Format section title consistently."""
        formatted_title = style_func(title) if style_func else title
        return formatted_title
    
    @staticmethod
    def format_indented_line(content: str, indent: int) -> str:
        """Format line with consistent indentation."""
        return f"{' ' * indent}{content}"
    
    @staticmethod
    def calculate_spacing(name_width: int, target_column: int, min_spacing: int = 4) -> int:
        """Calculate spacing needed to reach target column."""
        if name_width >= target_column:
            return min_spacing
        return target_column - name_width
    
    @staticmethod
    def wrap_text(text: str, width: int, initial_indent: str = "", subsequent_indent: str = "") -> List[str]:
        """Wrap text with consistent parameters."""
        wrapper = textwrap.TextWrapper(
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent
        )
        return wrapper.wrap(text)


class HierarchicalHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Refactored formatter with reduced duplication and single return points."""
    
    def __init__(self, *args, theme=None, alphabetize=True, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._console_width = self._get_console_width()
        self._cmd_indent = 2
        self._arg_indent = 4
        self._desc_indent = 8
        
        self._formatting_engine = HelpFormattingEngine(
            console_width=self._console_width,
            theme=theme,
            color_formatter=getattr(self, '_color_formatter', None)
        )
        
        self._theme = theme
        self._color_formatter = self._init_color_formatter(theme)
        self._alphabetize = alphabetize
        self._global_desc_column = None
        self._parser_actions = []
    
    def _get_console_width(self) -> int:
        """Get console width with fallback."""
        width = 80
        
        try:
            width = os.get_terminal_size().columns
        except (OSError, ValueError):
            width = int(os.environ.get('COLUMNS', 80))
        
        return width
    
    def _init_color_formatter(self, theme):
        """Initialize color formatter if theme is provided."""
        result = None
        
        if theme:
            from .theme import ColorFormatter
            result = ColorFormatter()
        
        return result
    
    def _format_actions(self, actions):
        """Override to capture parser actions for unified column calculation."""
        self._parser_actions = actions
        return super()._format_actions(actions)
    
    def _format_action(self, action):
        """Format actions with proper indentation."""
        result = ""
        
        if isinstance(action, argparse._SubParsersAction):
            result = self._format_command_groups(action)
        elif action.option_strings and not isinstance(action, argparse._SubParsersAction):
            result = self._format_global_option(action)
        else:
            result = super()._format_action(action)
        
        return result
    
    def _ensure_global_column_calculated(self) -> int:
        """Calculate and cache the unified description column."""
        if self._global_desc_column is not None:
            return self._global_desc_column
        
        column = 40  # Default fallback
        
        # Find subparsers action from parser actions
        subparsers_action = None
        for act in self._parser_actions:
            if isinstance(act, argparse._SubParsersAction):
                subparsers_action = act
                break
        
        if subparsers_action:
            column = self._calculate_unified_command_description_column(subparsers_action)
        
        self._global_desc_column = column
        return column
    
    def _format_global_option(self, action) -> str:
        """Format global options with consistent alignment."""
        result = ""
        
        if not action.option_strings:
            result = super()._format_action(action)
        else:
            option_display = self._build_option_display(action)
            help_text = self._build_option_help(action)
            global_desc_column = self._ensure_global_column_calculated()
            
            formatted_lines = self._format_inline_description(
                name=option_display,
                description=help_text,
                name_indent=self._arg_indent + 2,
                description_column=global_desc_column + 4,
                style_name='option_name',
                style_description='option_description',
                add_colon=False
            )
            
            result = '\n'.join(formatted_lines) + '\n'
        
        return result
    
    def _build_option_display(self, action) -> str:
        """Build option display string with metavar."""
        option_name = action.option_strings[-1] if action.option_strings else ""
        result = option_name
        
        if action.nargs != 0:
            if hasattr(action, 'metavar') and action.metavar:
                result = f"{option_name} {action.metavar}"
            elif not (hasattr(action, 'choices') and action.choices):
                metavar = action.dest.upper().replace('_', '-')
                result = f"{option_name} {metavar}"
        
        return result
    
    def _build_option_help(self, action) -> str:
        """Build help text for option including choices."""
        help_text = action.help or ""
        
        if (hasattr(action, 'choices') and action.choices and action.nargs != 0):
            choices_str = ", ".join(str(c) for c in action.choices)
            help_text = f"{help_text} (choices: {choices_str})"
        
        return help_text
    
    def _calculate_unified_command_description_column(self, action) -> int:
        """Calculate unified description column for all elements."""
        max_width = self._cmd_indent
        
        # Include global options
        max_width = self._update_max_width_with_global_options(max_width)
        
        # Include commands and their options
        max_width = self._update_max_width_with_commands(action, max_width)
        
        # Calculate description column with padding and limits
        desc_column = max_width + 4  # 4 spaces padding
        result = min(desc_column, self._console_width // 2)
        
        return result
    
    def _update_max_width_with_global_options(self, current_max: int) -> int:
        """Update max width considering global options."""
        max_width = current_max
        
        for act in self._parser_actions:
            if (act.option_strings and act.dest != 'help' and 
                not isinstance(act, argparse._SubParsersAction)):
                
                opt_display = self._build_option_display(act)
                global_opt_width = len(opt_display) + self._arg_indent
                max_width = max(max_width, global_opt_width)
        
        return max_width
    
    def _update_max_width_with_commands(self, action, current_max: int) -> int:
        """Update max width considering commands and their options."""
        max_width = current_max
        
        for choice, subparser in action.choices.items():
            # Command width
            cmd_width = self._cmd_indent + len(choice) + 1  # +1 for colon
            max_width = max(max_width, cmd_width)
            
            # Option widths
            max_width = self._update_max_width_with_parser_options(subparser, max_width)
            
            # Group command options
            if (hasattr(subparser, '_command_type') and 
                subparser._command_type == 'group' and 
                hasattr(subparser, '_commands')):
                
                max_width = self._update_max_width_with_group_commands(subparser, max_width)
        
        return max_width
    
    def _update_max_width_with_parser_options(self, parser, current_max: int) -> int:
        """Update max width with options from a parser."""
        max_width = current_max
        
        _, optional_args = self._analyze_arguments(parser)
        for arg_name, _ in optional_args:
            opt_width = len(arg_name) + self._arg_indent
            max_width = max(max_width, opt_width)
        
        return max_width
    
    def _update_max_width_with_group_commands(self, group_parser, current_max: int) -> int:
        """Update max width with group command options."""
        max_width = current_max
        
        for cmd_name in group_parser._commands.keys():
            cmd_parser = self._find_subparser(group_parser, cmd_name)
            if cmd_parser:
                max_width = self._update_max_width_with_parser_options(cmd_parser, max_width)
        
        return max_width
    
    def _format_command_groups(self, action) -> str:
        """Format command groups with unified column alignment."""
        result = ""
        
        if not action.choices:
            return result
        
        unified_cmd_desc_column = self._calculate_unified_command_description_column(action)
        global_option_column = self._calculate_global_option_column(action)
        sections = []
        
        # Sort choices if alphabetization is enabled
        choices = self._get_sorted_choices(action.choices)
        
        # Group and format commands
        groups, commands = self._separate_groups_and_commands(choices)
        
        # Add command groups
        for name, parser in groups:
            group_section = self._format_command_group(
                name, parser, self._cmd_indent, unified_cmd_desc_column, global_option_column
            )
            sections.append(group_section)
        
        # Add flat commands
        for name, parser in commands:
            command_section = self._format_flat_command(
                name, parser, self._cmd_indent, unified_cmd_desc_column, global_option_column
            )
            sections.append(command_section)
        
        result = '\n'.join(sections)
        return result
    
    def _get_sorted_choices(self, choices) -> List[Tuple[str, Any]]:
        """Get sorted choices based on alphabetization setting."""
        choice_items = list(choices.items())
        
        if self._alphabetize:
            choice_items.sort(key=lambda x: x[0])
        
        return choice_items
    
    def _separate_groups_and_commands(self, choices) -> Tuple[List[Tuple[str, Any]], List[Tuple[str, Any]]]:
        """Separate command groups from flat commands."""
        groups = []
        commands = []
        
        for name, parser in choices:
            if hasattr(parser, '_command_type') and parser._command_type == 'group':
                groups.append((name, parser))
            else:
                commands.append((name, parser))
        
        return groups, commands
    
    def _format_command_group(self, name: str, parser, base_indent: int, 
                             unified_cmd_desc_column: int, global_option_column: int) -> str:
        """Format a command group with subcommands."""
        lines = []
        
        # Group header
        group_description = getattr(parser, '_command_group_description', f"{name} operations")
        formatted_lines = self._format_inline_description(
            name=name,
            description=group_description,
            name_indent=base_indent,
            description_column=unified_cmd_desc_column,
            style_name='group_command_name',
            style_description='subcommand_description',
            add_colon=True
        )
        lines.extend(formatted_lines)
        
        # Subcommands
        if hasattr(parser, '_commands'):
            subcommand_lines = self._format_subcommands(
                parser, base_indent + 2, unified_cmd_desc_column, global_option_column
            )
            lines.extend(subcommand_lines)
        
        result = '\n'.join(lines)
        return result
    
    def _format_subcommands(self, parser, indent: int, unified_cmd_desc_column: int, 
                           global_option_column: int) -> List[str]:
        """Format subcommands within a group."""
        lines = []
        
        commands = getattr(parser, '_commands', {})
        command_items = list(commands.items())
        
        if self._alphabetize:
            command_items.sort(key=lambda x: x[0])
        
        for cmd_name, cmd_desc in command_items:
            cmd_parser = self._find_subparser(parser, cmd_name)
            
            if cmd_parser:
                cmd_lines = self._format_single_command(
                    cmd_name, cmd_desc, cmd_parser, indent, 
                    unified_cmd_desc_column, global_option_column
                )
                lines.extend(cmd_lines)
        
        return lines
    
    def _format_single_command(self, name: str, description: str, parser,
                              indent: int, unified_cmd_desc_column: int, 
                              global_option_column: int) -> List[str]:
        """Format a single command with its options."""
        lines = []
        
        # Command name and description
        formatted_lines = self._format_inline_description(
            name=name,
            description=description,
            name_indent=indent,
            description_column=unified_cmd_desc_column,
            style_name='subcommand_name',
            style_description='subcommand_description',
            add_colon=False
        )
        lines.extend(formatted_lines)
        
        # Command options
        option_lines = self._format_command_options(
            parser, indent + 2, global_option_column
        )
        lines.extend(option_lines)
        
        return lines
    
    def _format_flat_command(self, name: str, parser, base_indent: int,
                            unified_cmd_desc_column: int, global_option_column: int) -> str:
        """Format a flat command."""
        lines = []
        
        # Get command description
        description = getattr(parser, 'description', '') or ''
        
        # Command header
        formatted_lines = self._format_inline_description(
            name=name,
            description=description,
            name_indent=base_indent,
            description_column=unified_cmd_desc_column,
            style_name='command_name',
            style_description='command_description',
            add_colon=False
        )
        lines.extend(formatted_lines)
        
        # Command options
        option_lines = self._format_command_options(
            parser, base_indent + 2, global_option_column
        )
        lines.extend(option_lines)
        
        result = '\n'.join(lines)
        return result
    
    def _format_command_options(self, parser, indent: int, global_option_column: int) -> List[str]:
        """Format options for a command."""
        lines = []
        
        _, optional_args = self._analyze_arguments(parser)
        
        for arg_name, arg_help in optional_args:
            opt_lines = self._format_inline_description(
                name=arg_name,
                description=arg_help,
                name_indent=indent,
                description_column=global_option_column,
                style_name='option_name',
                style_description='option_description',
                add_colon=False
            )
            lines.extend(opt_lines)
        
        return lines
    
    def _format_inline_description(self, name: str, description: str, name_indent: int,
                                  description_column: int, style_name: str, 
                                  style_description: str, add_colon: bool = False) -> List[str]:
        """Format name and description inline with consistent wrapping."""
        lines = []
        
        if not description:
            # No description case
            styled_name = self._apply_style(name, style_name)
            display_name = f"{styled_name}:" if add_colon else styled_name
            lines = [FormatPatterns.format_indented_line(display_name, name_indent)]
        else:
            # With description case
            lines = self._format_with_description(
                name, description, name_indent, description_column,
                style_name, style_description, add_colon
            )
        
        return lines
    
    def _format_with_description(self, name: str, description: str, name_indent: int,
                                description_column: int, style_name: str,
                                style_description: str, add_colon: bool) -> List[str]:
        """Format name with description, handling wrapping."""
        lines = []
        
        styled_name = self._apply_style(name, style_name)
        styled_description = self._apply_style(description, style_description)
        
        display_name = f"{styled_name}:" if add_colon else styled_name
        name_part = FormatPatterns.format_indented_line(display_name, name_indent)
        name_display_width = name_indent + self._get_display_width(name) + (1 if add_colon else 0)
        
        spacing_needed = FormatPatterns.calculate_spacing(name_display_width, description_column)
        
        # Try single line first
        first_line = f"{name_part}{' ' * spacing_needed}{styled_description}"
        
        if self._get_display_width(first_line) <= self._console_width:
            lines = [first_line]
        else:
            # Need to wrap
            lines = self._wrap_description(
                name_part, description, name_display_width, spacing_needed,
                description_column, style_description
            )
        
        return lines
    
    def _wrap_description(self, name_part: str, description: str, name_display_width: int,
                         spacing_needed: int, description_column: int, style_description: str) -> List[str]:
        """Wrap description text when it doesn't fit on one line."""
        lines = []
        available_width_first_line = self._console_width - name_display_width - spacing_needed
        
        if available_width_first_line >= 20:  # Minimum readable width
            desc_lines = FormatPatterns.wrap_text(description, available_width_first_line)
            
            if desc_lines:
                # First line with name and description start
                styled_first_desc = self._apply_style(desc_lines[0], style_description)
                lines = [f"{name_part}{' ' * spacing_needed}{styled_first_desc}"]
                
                # Continuation lines
                if len(desc_lines) > 1:
                    desc_start_position = name_display_width + spacing_needed
                    continuation_indent = " " * desc_start_position
                    
                    for desc_line in desc_lines[1:]:
                        styled_desc_line = self._apply_style(desc_line, style_description)
                        lines.append(f"{continuation_indent}{styled_desc_line}")
        
        if not lines:  # Fallback
            lines = [name_part]
            desc_indent = description_column
            available_width = max(20, self._console_width - desc_indent)
            
            desc_lines = FormatPatterns.wrap_text(description, available_width)
            for desc_line in desc_lines:
                styled_desc_line = self._apply_style(desc_line, style_description)
                lines.append(FormatPatterns.format_indented_line(styled_desc_line, desc_indent))
        
        return lines
    
    def _analyze_arguments(self, parser) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        """Analyze parser arguments and return positional and optional arguments."""
        positional_args = []
        optional_args = []
        
        for action in parser._actions:
            if action.option_strings:
                # Optional argument
                if action.dest != 'help':
                    arg_display = self._build_option_display(action)
                    arg_help = self._build_option_help(action)
                    optional_args.append((arg_display, arg_help))
            elif action.dest != argparse.SUPPRESS:
                # Positional argument
                arg_name = action.dest.upper()
                arg_help = action.help or ''
                positional_args.append((arg_name, arg_help))
        
        return positional_args, optional_args
    
    def _find_subparser(self, group_parser, cmd_name: str):
        """Find subparser for a command within a group."""
        result = None
        
        for action in group_parser._actions:
            if (isinstance(action, argparse._SubParsersAction) and 
                cmd_name in action.choices):
                result = action.choices[cmd_name]
                break
        
        return result
    
    def _calculate_global_option_column(self, action) -> int:
        """Calculate global option description column."""
        max_opt_width = self._arg_indent
        
        # Scan all commands for their options
        for choice, subparser in action.choices.items():
            max_opt_width = self._update_max_width_with_parser_options(subparser, max_opt_width)
            
            # Also check group commands
            if (hasattr(subparser, '_command_type') and 
                subparser._command_type == 'group' and 
                hasattr(subparser, '_commands')):
                max_opt_width = self._update_max_width_with_group_commands(subparser, max_opt_width)
        
        # Add padding and limit
        global_opt_desc_column = max_opt_width + 4
        result = min(global_opt_desc_column, self._console_width // 2)
        
        return result
    
    def _apply_style(self, text: str, style_name: str) -> str:
        """Apply theme styling to text."""
        result = text
        
        if self._color_formatter and self._theme:
            style = getattr(self._theme, style_name, None)
            if style:
                result = self._color_formatter.apply_style(text, style)
        
        return result
    
    def _get_display_width(self, text: str) -> int:
        """Get display width of text (excluding ANSI escape sequences)."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_text = ansi_escape.sub('', text)
        return len(clean_text)