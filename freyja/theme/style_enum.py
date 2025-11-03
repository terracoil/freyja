"""Text style constants."""

from enum import Enum


class Style(Enum):
  """Text style constants."""

  DIM = "\x1b[2m"
  RESET_ALL = "\x1b[0m"
  # All ANSI style codes in one place
  ANSI_BOLD = "\x1b[1m"  # Bold text
  ANSI_ITALIC = "\x1b[3m"  # Italic text (support varies by terminal)
  ANSI_UNDERLINE = "\x1b[4m"  # Underlined text