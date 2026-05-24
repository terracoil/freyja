"""Theme module: Sunset palette + supporting types."""

from .color_formatter import ColorFormatter
from .defaults import get_default_theme, get_no_color_theme
from .enums import Back, Fore, Style
from .rgb import RGB, AdjustStrategy
from .theme import Theme, create_no_color_theme, create_sunset_theme
from .theme_style import CommandStyleSection, ThemeStyle

__all__ = [
  'AdjustStrategy',
  'Back',
  'ColorFormatter',
  'CommandStyleSection',
  'Fore',
  'RGB',
  'Style',
  'Theme',
  'ThemeStyle',
  'create_no_color_theme',
  'create_sunset_theme',
  'get_default_theme',
  'get_no_color_theme',
]
