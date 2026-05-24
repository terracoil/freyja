"""Handles color application and terminal compatibility."""

from __future__ import annotations

import os
import sys

from .enums import Style
from .rgb import RGB, _detect_truecolor
from .theme_style import ThemeStyle


class ColorFormatter:
  """Apply ThemeStyle to text via ANSI escapes when the terminal supports color."""

  def __init__(self, enable_colors: bool | None = None, truecolor: bool | None = None):
    """Initialize color formatter with automatic color and truecolor detection.

    :param enable_colors: Force enable/disable COLORS, or None for auto-detection
    :param truecolor: Force 24-bit ANSI output, or None to detect via ``COLORTERM``
    """
    self.colors_enabled = self._is_color_terminal() if enable_colors is None else enable_colors
    self.truecolor = _detect_truecolor() if truecolor is None else truecolor

    if self.colors_enabled:
      self.enable_windows_ansi_support()

  @staticmethod
  def enable_windows_ansi_support() -> None:
    """Enable ANSI escape sequences on Windows terminals."""
    if sys.platform != 'win32':
      return

    try:
      import ctypes

      kernel32 = ctypes.windll.kernel32
      kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:  # noqa: S110 # intentional silent fail for Windows compatibility
      pass

  @staticmethod
  def _is_color_terminal() -> bool:
    """Determine whether the current terminal should receive ANSI color codes."""
    result = True

    if os.environ.get('NO_COLOR') or os.environ.get('CLICOLOR') == '0':
      result = False
    elif os.environ.get('FORCE_COLOR') or os.environ.get('CLICOLOR'):
      result = True
    elif not sys.stdout.isatty():
      result = False
    elif sys.platform != 'win32':
      term_env = os.environ.get('TERM', '').lower()
      if term_env in ('dumb', ''):
        result = False
      elif 'color' in term_env or term_env in ('xterm', 'xterm-256color', 'screen'):
        result = True

    return result

  def apply_style(self, text: str, style: ThemeStyle) -> str:
    """Apply a theme style to text.

    :param text: Text to style
    :param style: ThemeStyle configuration to apply
    :return: Styled text (or original text if COLORS disabled)
    """
    result = text

    if self.colors_enabled and text and style is not None:
      codes: list[str] = []

      if isinstance(style.fg, RGB):
        codes.append(style.fg.to_ansi(background=False, truecolor=self.truecolor))
      if isinstance(style.bg, RGB):
        codes.append(style.bg.to_ansi(background=True, truecolor=self.truecolor))
      if style.bold:
        codes.append(Style.ANSI_BOLD.value)
      if style.dim:
        codes.append(Style.DIM.value)
      if style.italic:
        codes.append(Style.ANSI_ITALIC.value)
      if style.underline:
        codes.append(Style.ANSI_UNDERLINE.value)

      if codes:
        result = ''.join(codes) + text + Style.RESET_ALL.value

    return result
