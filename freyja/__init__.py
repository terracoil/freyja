"""
Freyja: Zero-configuration CLI generator from classes/module introspection.
Uses class/method/function introspection, typehints, and docstrings to build
a fully functional CLI.  Command groups can be made with inner-classes,
effectively making subclasses.
"""
from freyja.cli import CLI
from freyja.utils.string_utils import StringUtils
from freyja.command.system import System

__all__ = ["CLI", "StringUtils", "System"]
__version__ = "1.5.0"
