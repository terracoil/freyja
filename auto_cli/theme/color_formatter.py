"""Handles color application and terminal compatibility."""
from __future__ import annotations

import sys
from typing import Union

from auto_cli.theme.enums import Style
from auto_cli.theme.theme_style import ThemeStyle


class ColorFormatter:
  """Handles color application and terminal compatibility."""

  def __init__(self, enable_colors: Union[bool, None] = None):
    """Initialize color formatter with automatic color detection.

    :param enable_colors: Force enable/disable colors, or None for auto-detection
    """
    self.colors_enabled=self._is_color_terminal() if enable_colors is None else enable_colors

    if self.colors_enabled:
      self.enable_windows_ansi_support()

  @staticmethod
  def enable_windows_ansi_support():
    """Enable ANSI escape sequences on Windows terminals."""
    if sys.platform != 'win32':
      return

    try:
      import ctypes
      kernel32=ctypes.windll.kernel32
      kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
      # Fail silently on older Windows versions or permission issues
      pass

  def _is_color_terminal(self) -> bool:
    """Check if the current terminal supports colors."""
    import os

    result=True

    # Check for explicit disable first
    if os.environ.get('NO_COLOR') or os.environ.get('CLICOLOR') == '0':
      result=False
    elif os.environ.get('FORCE_COLOR') or os.environ.get('CLICOLOR'):
      # Check for explicit enable
      result=True
    elif not sys.stdout.isatty():
      # Check if stdout is a TTY (not redirected to file/pipe)
      result=False
    else:
      # Check environment variables that indicate color support
      term=sys.platform
      if term == 'win32':
        # Windows terminal color support
        result=True
      else:
        # Unix-like systems
        term_env=os.environ.get('TERM', '').lower()
        if 'color' in term_env or term_env in ('xterm', 'xterm-256color', 'screen'):
          result=True
        elif term_env in ('dumb', ''):
          # Default for dumb terminals or empty TERM
          result=False
        else:
          result=True

    return result

  def apply_style(self, text: str, style: ThemeStyle) -> str:
    """Apply a theme style to text.

    :param text: Text to style
    :param style: ThemeStyle configuration to apply
    :return: Styled text (or original text if colors disabled)
    """
    result=text

    if self.colors_enabled and text:
      # Build color codes
      codes=[]

      # Foreground color - handle hex colors and ANSI codes
      if style.fg:
        if style.fg.startswith('#'):
          # Hex color - convert to ANSI
          fg_code=self._hex_to_ansi(style.fg, is_background=False)
          if fg_code:
            codes.append(fg_code)
        elif style.fg.startswith('\x1b['):
          # Direct ANSI code
          codes.append(style.fg)
        else:
          # Fallback to old method for backwards compatibility
          fg_code=self._get_color_code(style.fg, is_background=False)
          if fg_code:
            codes.append(fg_code)

      # Background color - handle hex colors and ANSI codes
      if style.bg:
        if style.bg.startswith('#'):
          # Hex color - convert to ANSI
          bg_code=self._hex_to_ansi(style.bg, is_background=True)
          if bg_code:
            codes.append(bg_code)
        elif style.bg.startswith('\x1b['):
          # Direct ANSI code
          codes.append(style.bg)
        else:
          # Fallback to old method for backwards compatibility
          bg_code=self._get_color_code(style.bg, is_background=True)
          if bg_code:
            codes.append(bg_code)

      # Text styling (using defined ANSI constants)
      if style.bold:
        codes.append(Style.ANSI_BOLD.value)  # Use ANSI bold to avoid Style.BRIGHT color shifts
      if style.dim:
        codes.append(Style.DIM.value)  # ANSI DIM style
      if style.italic:
        codes.append(Style.ANSI_ITALIC.value)  # ANSI italic code (support varies by terminal)
      if style.underline:
        codes.append(Style.ANSI_UNDERLINE.value)  # ANSI underline code

      if codes:
        result=''.join(codes) + text + Style.RESET_ALL.value

    return result

  def _hex_to_ansi(self, hex_color: str, is_background: bool = False) -> str:
    """Convert hex colors to ANSI escape codes.

    :param hex_color: Hex value (e.g., '#FF0000')
    :param is_background: Whether this is a background color
    :return: ANSI color code or empty string
    """
    # Map common hex colors to ANSI codes
    hex_to_ansi_fg={
      '#000000':'\x1b[30m', '#FF0000':'\x1b[31m', '#008000':'\x1b[32m',
      '#FFFF00':'\x1b[33m', '#0000FF':'\x1b[34m', '#FF00FF':'\x1b[35m',
      '#00FFFF':'\x1b[36m', '#FFFFFF':'\x1b[37m',
      '#808080':'\x1b[90m', '#FF8080':'\x1b[91m',
      '#80FF80':'\x1b[92m', '#FFFF80':'\x1b[93m',
      '#8080FF':'\x1b[94m', '#FF80FF':'\x1b[95m',
      '#80FFFF':'\x1b[96m', '#F0F0F0':'\x1b[97m',
      '#FFA500':'\x1b[33m',  # Orange maps to yellow (closest available)
    }

    hex_to_ansi_bg={
      '#000000':'\x1b[40m', '#FF0000':'\x1b[41m', '#008000':'\x1b[42m',
      '#FFFF00':'\x1b[43m', '#0000FF':'\x1b[44m', '#FF00FF':'\x1b[45m',
      '#00FFFF':'\x1b[46m', '#FFFFFF':'\x1b[47m',
      '#808080':'\x1b[100m', '#FF8080':'\x1b[101m',
      '#80FF80':'\x1b[102m', '#FFFF80':'\x1b[103m',
      '#8080FF':'\x1b[104m', '#FF80FF':'\x1b[105m',
      '#80FFFF':'\x1b[106m', '#F0F0F0':'\x1b[107m',
    }

    color_map=hex_to_ansi_bg if is_background else hex_to_ansi_fg
    return color_map.get(hex_color.upper(), "")

  def _get_color_code(self, color: str, is_background: bool = False) -> str:
    """Convert color names to ANSI escape codes (backwards compatibility).

    :param color: Color name or hex value
    :param is_background: Whether this is a background color
    :return: ANSI color code or empty string
    """
    return self._hex_to_ansi(color, is_background) if color.startswith('#') else ""
