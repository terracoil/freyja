"""Argument parsing utilities for FreyjaCLI generation."""

import argparse
import enum
import inspect
from pathlib import Path
from typing import Any, Union, get_args, get_origin

from .docstring_parser import DocStringParser


class ArgumentParser:
    """Centralized service for handling argument parser configuration and setup."""

    @staticmethod
    def _bool_converter(value: str) -> bool:
        """Convert string value to boolean with flexible parsing.
        
        For true values: 'true' (any case) or any non-zero numeric value
        For false values: 'false' (any case) or '0'
        """
        if isinstance(value, bool):
            return value
        
        # Handle string representations
        lower_value = str(value).lower()
        
        # True values: 'true' (any case) or any non-zero numeric value
        if lower_value == 'true':
            return True
        
        # False values: 'false' (any case) or '0'
        if lower_value == 'false' or lower_value == '0':
            return False
            
        # Try to parse as a number (non-zero = True, zero = False)
        try:
            numeric_value = float(lower_value)
            return numeric_value != 0.0
        except ValueError:
            pass
        
        # Default to True for any other non-empty string
        return bool(value)

    @staticmethod
    def get_arg_type_config(annotation: type) -> dict[str, Any]:
        """Configure argparse arguments based on Python type annotations.

        Maps Python types from function signatures to argparse behavior.
        """
        # Handle Optional[Type] -> get the actual type
        # Handle both typing.Union and types.UnionType (Python 3.10+)
        origin = get_origin(annotation)
        if origin is Union or str(origin) == "<class 'types.UnionType'>":
            args = get_args(annotation)
            # Optional[T] is Union[T, NoneType]
            if len(args) == 2 and type(None) in args:
                annotation = next(arg for arg in args if arg is not type(None))

        if annotation in (str, int, float):
            return {"type": annotation}
        elif annotation == bool:
            return {"action": "store_true"}
        elif annotation == Path:
            return {"type": Path}
        elif inspect.isclass(annotation) and issubclass(annotation, enum.Enum):

            def enum_converter(x):
                try:
                    return annotation[x.split(".")[-1]]
                except KeyError as e:
                    # Let argparse handle the invalid choice error
                    raise ValueError(
                        f"invalid choice: '{x}' "
                        f"(choose from {', '.join(e.name for e in annotation)})"
                    ) from e

            return {
                "type": enum_converter,
                "choices": list(annotation),
                "metavar": f"{{{','.join(e.name for e in annotation)}}}",
            }
        return {}

    @staticmethod
    def add_global_class_args(parser: argparse.ArgumentParser, target_class: type) -> None:
        """Enable class-based FreyjaCLI with global configuration options.

        Class constructors define application-wide settings that apply to all cmd_tree.
        """
        init_method = target_class.__init__
        sig = inspect.signature(init_method)
        _, param_help = DocStringParser.extract_function_help(init_method)

        for param_name, param in sig.parameters.items():
            # Skip self parameter and varargs
            if param_name == "self" or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            arg_config = {
                "dest": f"_global_{param_name}",  # Prefix to avoid conflicts
                "help": DocStringParser.create_parameter_help(
                    param_name, param_help, param.annotation, param.default
                ),
            }

            # Handle type annotations
            if param.annotation != param.empty:
                type_config = ArgumentParser.get_arg_type_config(param.annotation)
                arg_config.update(type_config)

            # Handle defaults
            if param.default != param.empty:
                arg_config["default"] = param.default
            else:
                # Don't set required=True for boolean flags (they have action="store_true")
                if "action" not in arg_config:
                    arg_config["required"] = True

            # Add argument without prefix (user requested no global- prefix)
            from freyja.utils.text_util import TextUtil

            flag_name = TextUtil.kebab_case(param_name)
            flag = f"--{flag_name}"

            # Check for conflicts with built-in FreyjaCLI options
            built_in_options = {"no-color", "help"}
            if flag_name not in built_in_options:
                parser.add_argument(flag, **arg_config)

    @staticmethod
    def add_subglobal_class_args(
        parser: argparse.ArgumentParser, inner_class: type, command_name: str
    ) -> None:
        """Enable command group configuration for hierarchical FreyjaCLI organization.

        Inner class constructors provide group-specific settings shared across related cmd_tree.
        """
        init_method = inner_class.__init__
        sig = inspect.signature(init_method)
        _, param_help = DocStringParser.extract_function_help(init_method)

        # Get parameters as a list to skip main parameter
        params = list(sig.parameters.items())

        # Skip self (index 0) and main (index 1), start from index 2
        for param_name, param in params[2:]:
            # Skip varargs
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            arg_config = {
                "dest": f"_subglobal_{command_name}_{param_name}",  # Prefix to avoid conflicts
                "help": DocStringParser.create_parameter_help(
                    param_name, param_help, param.annotation, param.default
                ),
            }

            # Handle type annotations
            if param.annotation != param.empty:
                type_config = ArgumentParser.get_arg_type_config(param.annotation)
                arg_config.update(type_config)

            # Set clean metavar if not already set by type config
            if "metavar" not in arg_config and "action" not in arg_config:
                arg_config["metavar"] = param_name.upper()

            # Handle defaults
            if param.default != param.empty:
                arg_config["default"] = param.default
            else:
                # Don't set required=True for boolean flags (they have action="store_true")
                if "action" not in arg_config:
                    arg_config["required"] = True

            # Add argument with command-specific prefix
            from freyja.utils.text_util import TextUtil

            flag = f"--{TextUtil.kebab_case(param_name)}"
            parser.add_argument(flag, **arg_config)

    @staticmethod
    def add_function_args(parser: argparse.ArgumentParser, fn: Any) -> None:
        """Generate FreyjaCLI arguments directly from function signatures.

        Eliminates manual argument configuration by leveraging Python type hints and docstrings.
        Supports positional parameters (first non-default param) for more natural CLI usage.
        """
        sig = inspect.signature(fn)
        _, param_help = DocStringParser.extract_function_help(fn)

        # Check if first parameter (excluding self) has no default - this becomes positional
        first_positional_param = ArgumentParser._get_first_positional_param(fn)

        for name, param in sig.parameters.items():
            # Skip self parameter and varargs
            if name == "self" or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            # Check if this is the positional parameter
            is_positional = first_positional_param and name == first_positional_param.name

            if is_positional:
                # Add as positional (ArgumentPreprocessor handles conversion)
                arg_config: dict[str, Any] = {
                    "help": DocStringParser.create_parameter_help(
                        name, param_help, param.annotation, param.default
                    )
                }

                # Handle type annotations
                if param.annotation != param.empty:
                    type_config = ArgumentParser.get_arg_type_config(param.annotation)
                    arg_config.update(type_config)

                # Only add metavar for positional args that don't use action (non-boolean)
                if "action" not in arg_config:
                    # Convert parameter name to uppercase for positional display
                    from freyja.utils.text_util import TextUtil

                    positional_name = name.upper()
                    arg_config["metavar"] = positional_name

                # Positional args are required by default unless they have defaults
                if param.default == param.empty:
                    # Positional and required
                    parser.add_argument(name, **arg_config)
                else:
                    # Positional but optional
                    arg_config["nargs"] = "?"
                    arg_config["default"] = param.default
                    parser.add_argument(name, **arg_config)
            else:
                # For optional arguments, specify dest
                arg_config: dict[str, Any] = {
                    "dest": name,
                    "help": DocStringParser.create_parameter_help(
                        name, param_help, param.annotation, param.default
                    ),
                }

                # Handle type annotations
                if param.annotation != param.empty:
                    type_config = ArgumentParser.get_arg_type_config(param.annotation)
                    arg_config.update(type_config)

                # Handle defaults - determine if argument is required
                if param.default != param.empty:
                    arg_config["default"] = param.default
                    # Don't set required for optional args
                else:
                    arg_config["required"] = True

                # Add argument with kebab-case flag name
                from freyja.utils.text_util import TextUtil

                flag = f"--{TextUtil.kebab_case(name)}"
                parser.add_argument(flag, **arg_config)

    @staticmethod
    def _get_first_positional_param(fn: Any) -> inspect.Parameter | None:
        """Get the first parameter without a default value (excluding self)."""
        sig = inspect.signature(fn)

        for name, param in sig.parameters.items():
            if name == "self" or param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            # First parameter without default value becomes positional
            if param.default == param.empty:
                return param

        return None
