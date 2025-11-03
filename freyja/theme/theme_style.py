"""Individual style configuration for text formatting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freyja.theme import RGB


@dataclass
class ThemeStyle:
    """
    Individual style configuration for text formatting.
    Supports foreground/background colors (RGB instances only) and text decorations.
    """

    fg: RGB | None = None  # Foreground color (RGB instance only)
    bg: RGB | None = None  # Background color (RGB instance only)
    bold: bool = False  # Bold text
    italic: bool = False  # Italic text (may not work on all terminals)
    dim: bool = False  # Dimmed/faint text
    underline: bool = False  # Underlined text


