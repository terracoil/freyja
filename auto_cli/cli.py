"""Auto-generate CLI from function signatures and docstrings."""
import argparse
import enum
import inspect
import sys
import traceback
from collections.abc import Callable
from typing import Any, Union

from .docstring_parser import extract_function_help


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
        """Create argument parser from discovered functions."""
        parser = argparse.ArgumentParser(
            description=self.title,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # Add global verbose flag
        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )

        subparsers = parser.add_subparsers(
            title='Commands',
            dest='command',
            required=False,  # Allow no command to show help
            help='Available commands',
            metavar=''  # Remove the comma-separated list
        )

        for name, fn in self.functions.items():
            # Get function description from docstring
            desc, _ = extract_function_help(fn)

            # Create subparser with kebab-case command name
            command_name = name.replace('_', '-')
            sub = subparsers.add_parser(
                command_name,
                help=desc,
                description=desc
            )

            # Add function arguments
            self._add_function_args(sub, fn)

            # Store function reference for execution
            sub.set_defaults(_cli_function=fn, _function_name=name)

        return parser

    def run(self, args: list | None = None) -> Any:
        """Parse arguments and execute the appropriate function."""
        parser = self.create_parser()

        try:
            parsed = parser.parse_args(args)

            # If no command provided, show help
            if not hasattr(parsed, '_cli_function'):
                parser.print_help()
                return 0

            # Get function and prepare execution
            fn = parsed._cli_function
            sig = inspect.signature(fn)

            # Build kwargs from parsed arguments
            kwargs = {}
            for param_name in sig.parameters:
                # Convert kebab-case back to snake_case for function call
                attr_name = param_name.replace('-', '_')
                if hasattr(parsed, attr_name):
                    value = getattr(parsed, attr_name)
                    kwargs[param_name] = value

            # Execute function and return result
            return fn(**kwargs)

        except SystemExit:
            # Let argparse handle its own exits (help, errors, etc.)
            raise
        except Exception as e:
            # Handle execution errors gracefully
            print(f"Error executing {parsed._function_name}: {e}", file=sys.stderr)
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