"""Auto-generate CLI from function signatures and docstrings."""
import argparse
import enum
import inspect
import os
import sys
import textwrap
import traceback
from collections.abc import Callable
from typing import Any, Union

from .docstring_parser import extract_function_help


class HierarchicalHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter that shows command hierarchy with clean list-based argument display."""
    
    def __init__(self, *args, theme=None, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self._console_width = os.get_terminal_size().columns
        except (OSError, ValueError):
            # Fallback for non-TTY environments (pipes, redirects, etc.)
            self._console_width = int(os.environ.get('COLUMNS', 80))
        self._cmd_indent = 2  # Base indentation for commands
        self._arg_indent = 6  # Indentation for arguments
        self._desc_indent = 8  # Indentation for descriptions
        
        # Theme support
        self._theme = theme
        if theme:
            from .theme import ColorFormatter
            self._color_formatter = ColorFormatter()
        else:
            self._color_formatter = None
        
    def _format_action(self, action):
        """Format actions with proper indentation for subcommands."""
        if isinstance(action, argparse._SubParsersAction):
            return self._format_subcommands(action)
        return super()._format_action(action)
    
    def _format_subcommands(self, action):
        """Format subcommands with clean list-based display."""
        parts = []
        groups = {}
        flat_commands = {}
        has_required_args = False
        
        # Separate groups from flat commands
        for choice, subparser in action.choices.items():
            if hasattr(subparser, '_command_type'):
                if subparser._command_type == 'group':
                    groups[choice] = subparser
                else:
                    flat_commands[choice] = subparser
            else:
                flat_commands[choice] = subparser
        
        # Add flat commands with clean argument lists
        for choice, subparser in sorted(flat_commands.items()):
            command_section = self._format_command_with_args(choice, subparser, self._cmd_indent)
            parts.extend(command_section)
            # Check if this command has required args
            required_args, _ = self._analyze_arguments(subparser)
            if required_args:
                has_required_args = True
        
        # Add groups with their subcommands
        if groups:
            if flat_commands:
                parts.append("")  # Empty line separator
            
            for choice, subparser in sorted(groups.items()):
                group_section = self._format_group_with_subcommands(choice, subparser, self._cmd_indent)
                parts.extend(group_section)
                # Check subcommands for required args too
                if hasattr(subparser, '_subcommand_details'):
                    for subcmd_info in subparser._subcommand_details.values():
                        if subcmd_info.get('type') == 'command' and 'function' in subcmd_info:
                            # This is a bit tricky - we'd need to check the function signature
                            # For now, assume nested commands might have required args
                            has_required_args = True
        
        # Add footnote if there are required arguments
        if has_required_args:
            parts.append("")  # Empty line before footnote
            parts.append("* - required")
        
        return "\n".join(parts)
    
    def _format_command_with_args(self, name, parser, base_indent):
        """Format a single command with its arguments in list style."""
        lines = []
        
        # Get required and optional arguments
        required_args, optional_args = self._analyze_arguments(parser)
        
        # Command line (keep name only, move required args to separate lines)
        command_name = name
        
        # Determine if this is a subcommand based on indentation
        is_subcommand = base_indent > self._cmd_indent
        name_style = 'subcommand_name' if is_subcommand else 'command_name'
        desc_style = 'subcommand_description' if is_subcommand else 'command_description'
        
        # Add description inline with command if available
        help_text = parser.description or getattr(parser, 'help', '')
        if help_text:
            # Use inline description formatting
            formatted_lines = self._format_inline_description(
                name=command_name,
                description=help_text,
                name_indent=base_indent,
                description_column=40,  # Fixed column for consistency
                style_name=name_style,
                style_description=desc_style
            )
            lines.extend(formatted_lines)
        else:
            # Just the command name with styling
            styled_name = self._apply_style(command_name, name_style)
            lines.append(f"{' ' * base_indent}{styled_name}")
        
        # Add required arguments as a list (now on separate lines)
        if required_args:
            for arg_name in required_args:
                styled_req = self._apply_style(arg_name, 'required_option_name')
                lines.append(f"{' ' * self._arg_indent}{styled_req}")
        
        # Add optional arguments as a list
        if optional_args:
            for arg_name, arg_help in optional_args:
                if arg_help:
                    # Use inline formatting for options too
                    opt_lines = self._format_inline_description(
                        name=arg_name,
                        description=arg_help,
                        name_indent=self._arg_indent,
                        description_column=50,  # Slightly wider for options
                        style_name='option_name',
                        style_description='option_description'
                    )
                    lines.extend(opt_lines)
                else:
                    # Just the option name with styling
                    styled_opt = self._apply_style(arg_name, 'option_name')
                    lines.append(f"{' ' * self._arg_indent}{styled_opt}")
        
        return lines
    
    def _format_group_with_subcommands(self, name, parser, base_indent):
        """Format a command group with its subcommands."""
        lines = []
        indent_str = " " * base_indent
        
        # Group header
        lines.append(f"{indent_str}{name}")
        
        # Group description
        help_text = parser.description or getattr(parser, 'help', '')
        if help_text:
            wrapped_desc = self._wrap_text(help_text, self._desc_indent, self._console_width)
            lines.extend(wrapped_desc)
        
        # Find and format subcommands
        if hasattr(parser, '_subcommands'):
            subcommand_indent = base_indent + 2
            
            for subcmd, subcmd_help in sorted(parser._subcommands.items()):
                # Find the actual subparser
                subcmd_parser = self._find_subparser(parser, subcmd)
                if subcmd_parser:
                    subcmd_section = self._format_command_with_args(subcmd, subcmd_parser, subcommand_indent)
                    lines.extend(subcmd_section)
                else:
                    # Fallback for cases where we can't find the parser
                    lines.append(f"{' ' * subcommand_indent}{subcmd}")
                    if subcmd_help:
                        wrapped_help = self._wrap_text(subcmd_help, subcommand_indent + 2, self._console_width)
                        lines.extend(wrapped_help)
        
        return lines
    
    def _analyze_arguments(self, parser):
        """Analyze parser arguments and return required and optional separately."""
        if not parser:
            return [], []
            
        required_args = []
        optional_args = []
        
        for action in parser._actions:
            if action.dest == 'help':
                continue
                
            arg_name = f"--{action.dest.replace('_', '-')}"
            arg_help = getattr(action, 'help', '')
            
            if hasattr(action, 'required') and action.required:
                # Required argument - add asterisk to denote required
                if hasattr(action, 'metavar') and action.metavar:
                    required_args.append(f"{arg_name} {action.metavar} *")
                else:
                    required_args.append(f"{arg_name} {action.dest.upper()} *")
            elif action.option_strings:
                # Optional argument - add to list display
                if action.nargs == 0 or getattr(action, 'action', None) == 'store_true':
                    # Boolean flag
                    optional_args.append((arg_name, arg_help))
                else:
                    # Value argument
                    if hasattr(action, 'metavar') and action.metavar:
                        arg_display = f"{arg_name} {action.metavar}"
                    else:
                        arg_display = f"{arg_name} {action.dest.upper()}"
                    optional_args.append((arg_display, arg_help))
        
        return required_args, optional_args
    
    def _wrap_text(self, text, indent, width):
        """Wrap text with proper indentation using textwrap."""
        if not text:
            return []
            
        # Calculate available width for text
        available_width = max(width - indent, 20)  # Minimum 20 chars
        
        # Use textwrap to handle the wrapping
        wrapper = textwrap.TextWrapper(
            width=available_width,
            initial_indent=" " * indent,
            subsequent_indent=" " * indent,
            break_long_words=False,
            break_on_hyphens=False
        )
        
        return wrapper.wrap(text)
    
    def _apply_style(self, text: str, style_name: str) -> str:
        """Apply theme style to text if theme is available."""
        if not self._theme or not self._color_formatter:
            return text
        
        # Map style names to theme attributes
        style_map = {
            'title': self._theme.title,
            'subtitle': self._theme.subtitle,
            'command_name': self._theme.command_name,
            'command_description': self._theme.command_description,
            'subcommand_name': self._theme.subcommand_name,
            'subcommand_description': self._theme.subcommand_description,
            'option_name': self._theme.option_name,
            'option_description': self._theme.option_description,
            'required_option_name': self._theme.required_option_name,
            'required_option_description': self._theme.required_option_description
        }
        
        style = style_map.get(style_name)
        if style:
            return self._color_formatter.apply_style(text, style)
        return text
    
    def _get_display_width(self, text: str) -> int:
        """Get display width of text, handling ANSI color codes."""
        if not text:
            return 0
        
        # Strip ANSI escape sequences for width calculation
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_text = ansi_escape.sub('', text)
        return len(clean_text)
    
    def _format_inline_description(
        self, 
        name: str, 
        description: str, 
        name_indent: int,
        description_column: int,
        style_name: str,
        style_description: str
    ) -> list[str]:
        """Format name and description inline with consistent wrapping.
        
        :param name: The command/option name to display
        :param description: The description text
        :param name_indent: Indentation for the name
        :param description_column: Column where description should start
        :param style_name: Theme style for the name
        :param style_description: Theme style for the description
        :return: List of formatted lines
        """
        if not description:
            # No description, just return the styled name
            styled_name = self._apply_style(name, style_name)
            return [f"{' ' * name_indent}{styled_name}"]
        
        styled_name = self._apply_style(name, style_name)
        styled_description = self._apply_style(description, style_description)
        
        # Create the full line with proper spacing
        name_part = f"{' ' * name_indent}{styled_name}"
        name_display_width = name_indent + self._get_display_width(name)
        
        # Calculate spacing needed to reach description column
        spacing_needed = description_column - name_display_width
        spacing = description_column
        
        if name_display_width >= description_column:
            # Name is too long, use minimum spacing (4 spaces)
            spacing_needed = 4
            spacing = name_display_width + spacing_needed
        
        # Try to fit everything on first line
        first_line = f"{name_part}{' ' * spacing_needed}{styled_description}"
        
        # Check if first line fits within console width
        if self._get_display_width(first_line) <= self._console_width:
            # Everything fits on one line
            return [first_line]
        
        # Need to wrap - start with name and first part of description on same line
        available_width_first_line = self._console_width - name_display_width - spacing_needed
        
        if available_width_first_line >= 20:  # Minimum readable width for first line
            # Wrap description, keeping some on first line
            wrapper = textwrap.TextWrapper(
                width=available_width_first_line,
                break_long_words=False,
                break_on_hyphens=False
            )
            desc_lines = wrapper.wrap(styled_description)
            
            if desc_lines:
                # First line with name and first part of description
                lines = [f"{name_part}{' ' * spacing_needed}{desc_lines[0]}"]
                
                # Continuation lines with remaining description
                if len(desc_lines) > 1:
                    continuation_indent = " " * spacing
                    for desc_line in desc_lines[1:]:
                        lines.append(f"{continuation_indent}{desc_line}")
                
                return lines
        
        # Fallback: put description on separate lines (name too long or not enough space)
        lines = [name_part]
        
        available_width = self._console_width - spacing
        if available_width < 20:  # Minimum readable width
            available_width = 20
            spacing = self._console_width - available_width
        
        # Wrap the description text
        wrapper = textwrap.TextWrapper(
            width=available_width,
            break_long_words=False,
            break_on_hyphens=False
        )
        
        desc_lines = wrapper.wrap(styled_description)
        indent_str = " " * spacing
        
        for desc_line in desc_lines:
            lines.append(f"{indent_str}{desc_line}")
        
        return lines
    
    def _format_usage(self, usage, actions, groups, prefix):
        """Override to add color to usage line and potentially title."""
        usage_text = super()._format_usage(usage, actions, groups, prefix)
        
        # If this is the main parser (not a subparser), prepend styled title
        if prefix == 'usage: ' and hasattr(self, '_root_section'):
            # Try to get the parser description (title)
            parser = getattr(self._root_section, 'formatter', None)
            if parser:
                parser_obj = getattr(parser, '_parser', None)
                if parser_obj and hasattr(parser_obj, 'description') and parser_obj.description:
                    styled_title = self._apply_style(parser_obj.description, 'title')
                    return f"{styled_title}\n\n{usage_text}"
        
        return usage_text
    
    def _find_subparser(self, parent_parser, subcmd_name):
        """Find a subparser by name in the parent parser."""
        for action in parent_parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                if subcmd_name in action.choices:
                    return action.choices[subcmd_name]
        return None


class CLI:
    """Automatically generates CLI from module functions using introspection."""

    def __init__(self, target_module, title: str, function_filter: Callable | None = None, theme=None):
        """Initialize CLI generator.

        :param target_module: Module containing functions to expose as CLI commands
        :param title: CLI application title and description
        :param function_filter: Optional filter to select functions (default: non-private callables)
        :param theme: Optional ColorTheme for styling output
        """
        self.target_module = target_module
        self.title = title
        self.theme = theme
        self.function_filter = function_filter or self._default_function_filter
        self._discover_functions()

    def _default_function_filter(self, name: str, obj: Any) -> bool:
        """Default filter: include non-private callable functions."""
        return (
            not name.startswith('_') and
            callable(obj) and
            not inspect.isclass(obj) and
            inspect.isfunction(obj)
        )

    def _discover_functions(self):
        """Auto-discover functions from module using the filter."""
        self.functions = {}
        for name, obj in inspect.getmembers(self.target_module):
            if self.function_filter(name, obj):
                self.functions[name] = obj
        
        # Build hierarchical command structure
        self.commands = self._build_command_tree()

    def _build_command_tree(self) -> dict[str, dict]:
        """Build hierarchical command tree from discovered functions."""
        commands = {}
        
        for func_name, func_obj in self.functions.items():
            if '__' in func_name:
                # Parse hierarchical command: user__create or admin__user__reset
                self._add_to_command_tree(commands, func_name, func_obj)
            else:
                # Flat command: hello, count_animals → hello, count-animals
                cli_name = func_name.replace('_', '-')
                commands[cli_name] = {
                    'type': 'flat',
                    'function': func_obj,
                    'original_name': func_name
                }
        
        return commands

    def _add_to_command_tree(self, commands: dict, func_name: str, func_obj):
        """Add function to command tree, creating nested structure as needed."""
        # Split by double underscore: admin__user__reset_password → [admin, user, reset_password]
        parts = func_name.split('__')
        
        # Navigate/create tree structure
        current_level = commands
        path = []
        
        for i, part in enumerate(parts[:-1]):  # All but the last part are groups
            cli_part = part.replace('_', '-')  # Convert underscores to dashes
            path.append(cli_part)
            
            if cli_part not in current_level:
                current_level[cli_part] = {
                    'type': 'group',
                    'subcommands': {}
                }
            
            current_level = current_level[cli_part]['subcommands']
        
        # Add the final command
        final_command = parts[-1].replace('_', '-')
        current_level[final_command] = {
            'type': 'command',
            'function': func_obj,
            'original_name': func_name,
            'command_path': path + [final_command]
        }

    def _get_arg_type_config(self, annotation: type) -> dict[str, Any]:
        """Convert type annotation to argparse configuration."""
        from pathlib import Path
        from typing import get_args, get_origin

        # Handle Optional[Type] -> get the actual type
        # Handle both typing.Union and types.UnionType (Python 3.10+)
        origin = get_origin(annotation)
        if origin is Union or str(origin) == "<class 'types.UnionType'>":
            args = get_args(annotation)
            # Optional[T] is Union[T, NoneType]
            if len(args) == 2 and type(None) in args:
                annotation = next(arg for arg in args if arg is not type(None))

        if annotation in (str, int, float):
            return {'type': annotation}
        elif annotation == bool:
            return {'action': 'store_true'}
        elif annotation == Path:
            return {'type': Path}
        elif inspect.isclass(annotation) and issubclass(annotation, enum.Enum):
            return {
                'type': lambda x: annotation[x.split('.')[-1]],
                'choices': list(annotation),
                'metavar': f"{{{','.join(e.name for e in annotation)}}}"
            }
        return {}

    def _add_function_args(self, parser: argparse.ArgumentParser, fn: Callable):
        """Add function parameters as CLI arguments with help from docstring."""
        sig = inspect.signature(fn)
        _, param_help = extract_function_help(fn)

        for name, param in sig.parameters.items():
            # Skip *args and **kwargs - they can't be CLI arguments
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            arg_config: dict[str, Any] = {
                'dest': name,
                'help': param_help.get(name, f"{name} parameter")
            }

            # Handle type annotations
            if param.annotation != param.empty:
                type_config = self._get_arg_type_config(param.annotation)
                arg_config.update(type_config)

            # Handle defaults - determine if argument is required
            if param.default != param.empty:
                arg_config['default'] = param.default
                # Don't set required for optional args
            else:
                arg_config['required'] = True

            # Add argument with kebab-case flag name
            flag = f"--{name.replace('_', '-')}"
            parser.add_argument(flag, **arg_config)

    def create_parser(self, no_color: bool = False) -> argparse.ArgumentParser:
        """Create argument parser with hierarchical subcommand support."""
        # Create a custom formatter class that includes the theme (or no theme if no_color)
        effective_theme = None if no_color else self.theme
        def create_formatter_with_theme(*args, **kwargs):
            formatter = HierarchicalHelpFormatter(*args, theme=effective_theme, **kwargs)
            return formatter
        
        parser = argparse.ArgumentParser(
            description=self.title,
            formatter_class=create_formatter_with_theme
        )
        
        # Monkey-patch the parser to style the title
        original_format_help = parser.format_help
        
        def patched_format_help():
            # Get original help
            original_help = original_format_help()
            
            # Apply title styling if we have a theme
            if effective_theme and self.title in original_help:
                from .theme import ColorFormatter
                color_formatter = ColorFormatter()
                styled_title = color_formatter.apply_style(self.title, effective_theme.title)
                # Replace the plain title with the styled version
                original_help = original_help.replace(self.title, styled_title)
            
            return original_help
        
        parser.format_help = patched_format_help

        # Add global verbose flag
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

        # Main subparsers
        subparsers = parser.add_subparsers(
            title='Commands',
            dest='command',
            required=False,  # Allow no command to show help
            help='Available commands',
            metavar=''  # Remove the comma-separated list
        )

        # Add commands (flat, groups, and nested groups)
        self._add_commands_to_parser(subparsers, self.commands, [])

        return parser

    def _add_commands_to_parser(self, subparsers, commands: dict, path: list):
        """Recursively add commands to parser, supporting arbitrary nesting."""
        for name, info in commands.items():
            if info['type'] == 'flat':
                self._add_flat_command(subparsers, name, info)
            elif info['type'] == 'group':
                self._add_command_group(subparsers, name, info, path + [name])
            elif info['type'] == 'command':
                self._add_leaf_command(subparsers, name, info)

    def _add_flat_command(self, subparsers, name: str, info: dict):
        """Add a flat command to subparsers."""
        func = info['function']
        desc, _ = extract_function_help(func)
        
        sub = subparsers.add_parser(name, help=desc, description=desc)
        sub._command_type = 'flat'
        self._add_function_args(sub, func)
        sub.set_defaults(_cli_function=func, _function_name=info['original_name'])

    def _add_command_group(self, subparsers, name: str, info: dict, path: list):
        """Add a command group with subcommands (supports nesting)."""
        # Create group parser
        group_help = f"{name.title().replace('-', ' ')} operations"
        group_parser = subparsers.add_parser(name, help=group_help)
        group_parser._command_type = 'group'
        
        # Store subcommand info for help formatting  
        subcommand_help = {}
        for subcmd_name, subcmd_info in info['subcommands'].items():
            if subcmd_info['type'] == 'command':
                func = subcmd_info['function'] 
                desc, _ = extract_function_help(func)
                subcommand_help[subcmd_name] = desc
            elif subcmd_info['type'] == 'group':
                # For nested groups, show as group with subcommands
                subcommand_help[subcmd_name] = f"{subcmd_name.title().replace('-', ' ')} operations"
        
        group_parser._subcommands = subcommand_help
        group_parser._subcommand_details = info['subcommands']
        
        # Create subcommand parsers with enhanced help
        dest_name = '_'.join(path) + '_subcommand' if len(path) > 1 else 'subcommand'
        sub_subparsers = group_parser.add_subparsers(
            title=f'{name.title().replace("-", " ")} Commands',
            dest=dest_name,
            required=False,
            help=f'Available {name} commands',
            metavar=''
        )
        
        # Store reference for enhanced help formatting
        sub_subparsers._enhanced_help = True
        sub_subparsers._subcommand_details = info['subcommands']
        
        # Recursively add subcommands
        self._add_commands_to_parser(sub_subparsers, info['subcommands'], path)

    def _add_leaf_command(self, subparsers, name: str, info: dict):
        """Add a leaf command (actual executable function).""" 
        func = info['function']
        desc, _ = extract_function_help(func)
        
        sub = subparsers.add_parser(name, help=desc, description=desc)
        sub._command_type = 'command'
        
        self._add_function_args(sub, func)
        sub.set_defaults(
            _cli_function=func,
            _function_name=info['original_name'],
            _command_path=info['command_path']
        )

    def run(self, args: list | None = None) -> Any:
        """Parse arguments and execute the appropriate function."""
        # First, do a preliminary parse to check for --no-color flag
        # This allows us to disable colors before any help output is generated
        no_color = False
        if args:
            no_color = '--no-color' in args or '-n' in args
        
        parser = self.create_parser(no_color=no_color)

        try:
            parsed = parser.parse_args(args)

            # Handle missing command/subcommand scenarios
            if not hasattr(parsed, '_cli_function'):
                return self._handle_missing_command(parser, parsed)

            # Execute the command
            return self._execute_command(parsed)

        except SystemExit:
            # Let argparse handle its own exits (help, errors, etc.)
            raise
        except Exception as e:
            # Handle execution errors gracefully
            return self._handle_execution_error(parsed, e)

    def _handle_missing_command(self, parser: argparse.ArgumentParser, parsed) -> int:
        """Handle cases where no command or subcommand was provided."""
        # Analyze parsed arguments to determine what level of help to show
        command_parts = []
        
        # Check for command and nested subcommands
        if hasattr(parsed, 'command') and parsed.command:
            command_parts.append(parsed.command)
            
            # Check for nested subcommands
            for attr_name in dir(parsed):
                if attr_name.endswith('_subcommand') and getattr(parsed, attr_name):
                    # Extract command path from attribute names
                    if attr_name == 'subcommand':
                        # Simple case: user subcommand
                        subcommand = getattr(parsed, attr_name)
                        if subcommand:
                            command_parts.append(subcommand)
                    else:
                        # Complex case: user_subcommand for nested groups
                        path_parts = attr_name.replace('_subcommand', '').split('_')
                        command_parts.extend(path_parts)
                        subcommand = getattr(parsed, attr_name)
                        if subcommand:
                            command_parts.append(subcommand)
        
        if command_parts:
            # Show contextual help for partial command
            return self._show_contextual_help(parser, command_parts)
        
        # No command provided - show main help
        parser.print_help()
        return 0

    def _show_contextual_help(self, parser: argparse.ArgumentParser, command_parts: list) -> int:
        """Show help for a specific command level."""
        # Navigate to the appropriate subparser
        current_parser = parser
        
        for part in command_parts:
            # Find the subparser for this command part
            found_parser = None
            for action in current_parser._actions:
                if isinstance(action, argparse._SubParsersAction):
                    if part in action.choices:
                        found_parser = action.choices[part]
                        break
            
            if found_parser:
                current_parser = found_parser
            else:
                print(f"Unknown command: {' '.join(command_parts[:command_parts.index(part)+1])}", file=sys.stderr)
                parser.print_help()
                return 1
        
        current_parser.print_help()
        return 0

    def _execute_command(self, parsed) -> Any:
        """Execute the parsed command with its arguments."""
        fn = parsed._cli_function
        sig = inspect.signature(fn)

        # Build kwargs from parsed arguments
        kwargs = {}
        for param_name in sig.parameters:
            # Skip *args and **kwargs - they can't be CLI arguments
            param = sig.parameters[param_name]
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue
                
            # Convert kebab-case back to snake_case for function call
            attr_name = param_name.replace('-', '_')
            if hasattr(parsed, attr_name):
                value = getattr(parsed, attr_name)
                kwargs[param_name] = value

        # Execute function and return result
        return fn(**kwargs)

    def _handle_execution_error(self, parsed, error: Exception) -> int:
        """Handle execution errors gracefully."""
        function_name = getattr(parsed, '_function_name', 'unknown')
        print(f"Error executing {function_name}: {error}", file=sys.stderr)
        
        if getattr(parsed, 'verbose', False):
            traceback.print_exc()
        
        return 1

    def display(self):
        """Legacy method for backward compatibility - runs the CLI."""
        try:
            result = self.run()
            if isinstance(result, int):
                sys.exit(result)
        except SystemExit:
            # Argparse already handled the exit
            pass
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)