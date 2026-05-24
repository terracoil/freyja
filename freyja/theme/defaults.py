"""Default theme accessors for Freyja CLI."""

from .theme import Theme, create_no_color_theme, create_sunset_theme


def get_default_theme() -> Theme:
  """Return the default Sunset theme."""
  return create_sunset_theme()


def get_no_color_theme() -> Theme:
  """Return the no-color theme (used when COLORS are disabled)."""
  return create_no_color_theme()
