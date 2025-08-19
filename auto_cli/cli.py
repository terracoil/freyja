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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self._console_width = os.get_terminal_size().columns
        except (OSError, ValueError):
            # Fallback for non-TTY environments (pipes, redirects, etc.)
            self._console_width = int(os.environ.get('COLUMNS', 80))
        self._cmd_indent = 2  # Base indentation for commands
        self._arg_indent = 6  # Indentation for arguments
        self._desc_indent = 8  # Indentation for descriptions
        
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
        
        # Add groups with their subcommands
        if groups:
            if flat_commands:
                parts.append("")  # Empty line separator
            
            for choice, subparser in sorted(groups.items()):
                group_section = self._format_group_with_subcommands(choice, subparser, self._cmd_indent)
                parts.extend(group_section)
        
        return "\n".join(parts)
    
    def _format_command_with_args(self, name, parser, base_indent):
        """Format a single command with its arguments in list style."""
        lines = []
        indent_str = " " * base_indent
        
        # Get required and optional arguments
        required_args, optional_args = self._analyze_arguments(parser)
        
        # Command line with required arguments
        if required_args:
            req_args_str = " " + " ".join(required_args)
            lines.append(f"{indent_str}{name}{req_args_str}")
        else:
            lines.append(f"{indent_str}{name}")
        
        # Add description if available
        help_text = parser.description or getattr(parser, 'help', '')
        if help_text:
            wrapped_desc = self._wrap_text(help_text, self._desc_indent, self._console_width)
            lines.extend(wrapped_desc)
        
        # Add optional arguments as a list
        if optional_args:
            for arg_name, arg_help in optional_args:
                arg_line = f"{' ' * self._arg_indent}{arg_name}"
                lines.append(arg_line)
                if arg_help:
                    wrapped_help = self._wrap_text(arg_help, self._desc_indent, self._console_width)
                    lines.extend(wrapped_help)
        
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
                # Required argument - add to inline display
                if hasattr(action, 'metavar') and action.metavar:
                    required_args.append(f"{arg_name} {action.metavar}")
                else:
                    required_args.append(f"{arg_name} {action.dest.upper()}")
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
    
    def _find_subparser(self, parent_parser, subcmd_name):
        """Find a subparser by name in the parent parser."""
        for action in parent_parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                if subcmd_name in action.choices:
                    return action.choices[subcmd_name]
        return None


class CLI:
    """Automatically generates CLI from module functions using introspection."""

    def __init__(self, target_module, title: str, function_filter: Callable | None = None):
        """Initialize CLI generator.

        :param target_module: Module containing functions to expose as CLI commands
        :param title: CLI application title and description
        :param function_filter: Optional filter to select functions (default: non-private callables)
        """
        self.target_module = target_module
        self.title = title
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

    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with hierarchical subcommand support."""
        parser = argparse.ArgumentParser(
            description=self.title,
            formatter_class=HierarchicalHelpFormatter
        )

        # Add global verbose flag
        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
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
        parser = self.create_parser()

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