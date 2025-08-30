"""
Freyja: Zero-configuration CLI generator from classes/module introspection.
Uses class/method/function introspection, typehints, and docstrings to build
a fully functional CLI.  Command groups can be made with inner-classes,
effectively making subclasses.
"""
from .cli import CLI
from .utils.string_utils import StringUtils

__all__ = ["CLI", "StringUtils"]
__version__ = "1.5.0"
