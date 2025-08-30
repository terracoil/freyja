#!/usr/bin/env python3
"""Example of using System class for CLI utilities."""

from src import CLI
from src.command.system import System
from src.theme import create_default_theme

if __name__ == '__main__':
  # Create CLI with System class to demonstrate built-in system utilities
  theme = create_default_theme()
  cli = CLI(
    System,
    title="System Utilities CLI - Built-in Commands",
    theme=theme,
    enable_completion=True
  )

  # Run the CLI and exit with appropriate code
  result = cli.run()
  exit(result if isinstance(result, int) else 0)
