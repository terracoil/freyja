"""Argument and command parsing — argparse integration and docstring discovery."""

from .argument_parser import ArgumentParser
from .command_parser import CommandParser
from .docstring_parser import DocStringParser

__all__ = [
  'ArgumentParser',
  'CommandParser',
  'DocStringParser',
]
