"""Parse function docstrings to extract parameter descriptions."""

import re
from dataclasses import dataclass


@dataclass
class ParamDoc:
    """Holds parameter documentation extracted from docstring."""

    name: str
    description: str
    type_hint: str | None = None


class DocStringParser:
    """Parser for extracting parameter documentation from function docstrings."""

    @classmethod
    def parse_docstring(cls, docstring: str) -> tuple[str, dict[str, ParamDoc]]:
        """Extract main description and parameter docs from docstring.

        :param docstring: The docstring text to parse
        :return: Tuple of (main_description, param_docs_dict)
        """
        if not docstring:
            return "", {}

        # Split into lines and clean up
        lines = [line.strip() for line in docstring.strip().split("\n")]
        main_lines = []
        param_docs = {}

        # Regex for :param name: description
        param_pattern = re.compile(r"^:param\s+(\w+):\s*(.+)$")

        for line in lines:
            if not line:
                continue

            match = param_pattern.match(line)
            if match:
                param_name, param_desc = match.groups()
                param_docs[param_name] = ParamDoc(param_name, param_desc.strip())
            elif not line.startswith(":"):
                # Only add non-param lines to main description
                main_lines.append(line)

        # Join main description lines, removing empty lines at start/end
        main_desc = " ".join(main_lines).strip()

        return main_desc, param_docs

    @classmethod
    def extract_function_help(cls, func) -> tuple[str, dict[str, str]]:
        """Extract help information from a function's docstring.

        :param func: Function to extract help from
        :return: Tuple of (main_description, param_help_dict)
        """
        import inspect

        docstring = inspect.getdoc(func) or ""
        main_desc, param_docs = cls.parse_docstring(docstring)

        # Convert ParamDoc objects to simple string dict
        param_help = {param.name: param.description for param in param_docs.values()}

        return main_desc or f"Execute {func.__name__}", param_help

    @classmethod
    def create_parameter_help(
        cls,
        param_name: str,
        param_help_dict: dict[str, str],
        param_annotation=None,
        param_default=None,
    ) -> str:
        """Create descriptive help text for a parameter.

        :param param_name: Name of the parameter
        :param param_help_dict: Dictionary of parameter help from docstring
        :param param_annotation: Type annotation of the parameter
        :param param_default: Default value of the parameter
        :return: Descriptive help text for the parameter
        """
        # First try to get description from docstring
        if param_name in param_help_dict:
            help_text = param_help_dict[param_name]
            # Add required indicator if no default value
            import inspect
            if param_default is None or param_default == inspect.Parameter.empty:
                # Add required indicator - use caps to make it stand out more
                help_text += " [REQUIRED]"
            return help_text
        

        # Fallback: create description from type and default
        type_info = ""
        default_info = ""
        required_info = ""

        # Add type information if available
        if param_annotation is not None and hasattr(param_annotation, "__name__"):
            type_info = f"({param_annotation.__name__})"
        elif param_annotation is not None:
            type_info = f"({str(param_annotation).replace('typing.', '')})"

        # Add default information if available and not sentinel/empty
        import inspect
        if param_default is not None and param_default != inspect.Parameter.empty:
            # Format default values with proper representations
            if isinstance(param_default, bool):
                default_value = "true" if param_default else "false"
            elif isinstance(param_default, str):
                default_value = f'"{param_default}"'
            elif isinstance(param_default, (list, dict)):
                default_value = str(param_default)  # Shows [] or {} for empty collections
            else:
                default_value = str(param_default)
            
            default_info = f" (default: {default_value})"
        else:
            # No default value means it's required - use caps to make it stand out
            required_info = " [REQUIRED]"

        # Combine type, default, and required info
        combined_info = f"{type_info}{default_info}{required_info}".strip()

        # Debug output to see what's happening
        result = combined_info if combined_info else param_name
        # print(f"DEBUG: create_parameter_help({param_name}) -> '{result}'")
        return result
