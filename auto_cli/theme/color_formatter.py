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
          fg_code=self._hex_to_ansi(style.fg, background=False)
          if fg_code:
            codes.append(fg_code)
        elif style.fg.startswith('\x1b['):
          # Direct ANSI code
          codes.append(style.fg)
        else:
          raise ValueError(f"Not a valid format: {style.fg}")

      # Background color - handle hex colors and ANSI codes
      if style.bg:
        if style.bg.startswith('#'):
          # Hex color - convert to ANSI
          bg_code=self._hex_to_ansi(style.bg, background=True)
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

  def _hex_to_ansi(self, hex_color: str, background: bool = False) -> str:
    """Convert hex colors to ANSI escape codes.

    :param hex_color: Hex value (e.g., '#FF0000')
    :param background: Whether this is a background color
    :return: ANSI color code or empty string
    """
    # Map common hex colors to ANSI codes
        # Clean and validate hex input
    hex_color = hex_color.strip().lstrip('#').upper()

    # Handle 3-digit hex (e.g., "F57" -> "FF5577")
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)

    if len(hex_color) != 6 or not all(c in '0123456789ABCDEF' for c in hex_color):
        raise ValueError(f"Invalid hex color: {hex_color}")

    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Find closest ANSI 256 color
    ansi_code = self.rgb_to_ansi256(r, g, b)

    # Return appropriate ANSI escape sequence
    prefix = '\033[48;5;' if background else '\033[38;5;'
    return f"{prefix}{ansi_code}m"

  def rgb_to_ansi256(self, r: int, g: int, b: int) -> int:
    """
    Convert RGB values to the closest ANSI 256-color code.

    Args:
        r, g, b: RGB values (0-255)

    Returns:
        ANSI color code (0-255)
    """
    # Check if it's close to grayscale (colors 232-255)
    if abs(r - g) < 10 and abs(g - b) < 10 and abs(r - b) < 10:
        # Use grayscale palette (24 shades)
        gray = (r + g + b) // 3
        if gray < 8:
            return 16  # Black
        elif gray > 238:
            return 231  # White
        else:
            return 232 + (gray - 8) * 23 // 230

    # Use 6x6x6 color cube (colors 16-231)
    # Map RGB values to 6-level scale (0-5)
    r6 = min(5, r * 6 // 256)
    g6 = min(5, g * 6 // 256)
    b6 = min(5, b * 6 // 256)

    return 16 + (36 * r6) + (6 * g6) + b6
