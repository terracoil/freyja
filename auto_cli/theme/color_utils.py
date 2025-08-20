"""Utility functions for color manipulation and conversion."""
from typing import Tuple

from auto_cli.math_utils import MathUtils

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
  """Convert hex color to RGB tuple.

  :param hex_color: Hex color string (e.g., '#FF0000' or 'FF0000')
  :return: RGB tuple (r, g, b)
  :raises ValueError: If hex_color is invalid
  """
  # Remove # if present and validate
  hex_clean=hex_color.lstrip('#')

  if len(hex_clean) != 6:
    raise ValueError(f"Invalid hex color: {hex_color}")

  try:
    r=int(hex_clean[0:2], 16)
    g=int(hex_clean[2:4], 16)
    b=int(hex_clean[4:6], 16)
    return r, g, b
  except ValueError as e:
    raise ValueError(f"Invalid hex color: {hex_color}") from e


def rgb_to_hex(r: int, g: int, b: int) -> str:
  """Convert RGB values to hex color string.

  :param r: Red component (0-255)
  :param g: Green component (0-255)
  :param b: Blue component (0-255)
  :return: Hex color string (e.g., '#FF0000')
  """
  r=MathUtils.clamp(r, 0, 255)
  g=MathUtils.clamp(g, 0, 255)
  b=MathUtils.clamp(b, 0, 255)
  return f"#{r:02x}{g:02x}{b:02x}".upper()


def is_valid_hex_color(hex_color: str) -> bool:
  """Check if a string is a valid hex color.

  :param hex_color: Color string to validate
  :return: True if valid hex color, False otherwise
  """
  result=False

  try:
    hex_to_rgb(hex_color)
    result=True
  except ValueError:
    result=False

  return result
