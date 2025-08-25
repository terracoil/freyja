"""Auto-CLI: Generate CLIs from functions automatically using docstrings."""
from .cli import CLI
from auto_cli.utils.string_utils import StringUtils

__all__ = ["CLI", "StringUtils"]
__version__ = "1.5.0"
