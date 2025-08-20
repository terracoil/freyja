"""Individual style configuration for text formatting."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ThemeStyle:
  """
  Individual style configuration for text formatting.
  Supports foreground/background colors (named or hex) and text decorations.
  """
  fg: str | None=None  # Foreground color (name or hex)
  bg: str | None=None  # Background color (name or hex)
  bold: bool=False  # Bold text
  italic: bool=False  # Italic text (may not work on all terminals)
  dim: bool=False  # Dimmed/faint text
  underline: bool=False  # Underlined text
