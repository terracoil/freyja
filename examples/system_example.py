#!/usr/bin/env python3
"""Example of using System class for FreyjaCLI utilities."""

from freyja import FreyjaCLI
from freyja.cli.system import System
from freyja.theme import create_default_theme

if __name__ == '__main__':
  # Create FreyjaCLI with System class to demonstrate built-in system utilities
  theme = create_default_theme()
  cli = FreyjaCLI(
    System,
    title="System Utilities FreyjaCLI - Built-in Commands",
    theme=theme,
    enable_completion=True
  )

  # Run the FreyjaCLI and exit with appropriate code
  result = cli.run()
  exit(result if isinstance(result, int) else 0)
