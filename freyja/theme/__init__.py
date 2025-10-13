"""Theme module for freyja color schemes."""

from .color_formatter import ColorFormatter
from .enums import Back, Fore, ForeUniversal, Style
from .rgb import RGB, AdjustStrategy
from .theme import (
    Theme,
    create_default_theme,
    create_default_theme_colorful,
    create_no_color_theme,
)
from .theme_style import CommandStyleSection, ThemeStyle

__all__ = [
    "AdjustStrategy",
    "Back",
    "ColorFormatter",
    "CommandStyleSection",
    "Fore",
    "ForeUniversal",
    "RGB",
    "Style",
    "Theme",
    "ThemeStyle",
    "create_default_theme",
    "create_default_theme_colorful",
    "create_no_color_theme",
]
