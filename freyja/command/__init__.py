"""Command processing package - handles CLI command parsing, building, and execution."""

from .command_discovery import CommandInfo, CommandDiscovery
from .command_parser import CommandParser
from .command_builder import CommandBuilder
from .command_executor import CommandExecutor
from .argument_parser import ArgumentParserService
from .docstring_parser import extract_function_help
from .system import System
from .multi_class_handler import MultiClassHandler

__all__ = [
    'CommandInfo',
    'CommandDiscovery', 
    'CommandParser',
    'CommandBuilder',
    'CommandExecutor',
    'ArgumentParserService',
    'extract_function_help',
    'System',
    'MultiClassHandler'
]