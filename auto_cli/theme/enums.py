from enum import Enum


class Fore(Enum):
  """Foreground color constants."""
  BLACK=0x000000
  RED=0xFF0000
  GREEN=0x008000
  YELLOW=0xFFFF00
  BLUE=0x0000FF
  MAGENTA=0xFF00FF
  CYAN=0x00FFFF
  WHITE=0xFFFFFF

  # Bright colors
  LIGHTBLACK_EX=0x808080
  LIGHTRED_EX=0xFF8080
  LIGHTGREEN_EX=0x80FF80
  LIGHTYELLOW_EX=0xFFFF80
  LIGHTBLUE_EX=0x8080FF
  LIGHTMAGENTA_EX=0xFF80FF
  LIGHTCYAN_EX=0x80FFFF
  LIGHTWHITE_EX=0xF0F0F0


class Back(Enum):
  """Background color constants."""
  BLACK=0x000000
  RED=0xFF0000
  GREEN=0x008000
  YELLOW=0xFFFF00
  BLUE=0x0000FF
  MAGENTA=0xFF00FF
  CYAN=0x00FFFF
  WHITE=0xFFFFFF

  # Bright backgrounds
  LIGHTBLACK_EX=0x808080
  LIGHTRED_EX=0xFF8080
  LIGHTGREEN_EX=0x80FF80
  LIGHTYELLOW_EX=0xFFFF80
  LIGHTBLUE_EX=0x8080FF
  LIGHTMAGENTA_EX=0xFF80FF
  LIGHTCYAN_EX=0x80FFFF
  LIGHTWHITE_EX=0xF0F0F0


class Style(Enum):
  """Text style constants."""
  DIM='\x1b[2m'
  RESET_ALL='\x1b[0m'
  # All ANSI style codes in one place
  ANSI_BOLD='\x1b[1m'  # Bold text
  ANSI_ITALIC='\x1b[3m'  # Italic text (support varies by terminal)
  ANSI_UNDERLINE='\x1b[4m'  # Underlined text


class ForeUniversal(Enum):
  """Universal foreground colors that work well on both light and dark backgrounds."""
  # Blues (excellent on both)
  BRIGHT_BLUE=0x8080FF  # Bright blue
  ROYAL_BLUE=0x0000FF  # Blue

  # Greens (great visibility)
  EMERALD=0x80FF80  # Bright green
  FOREST_GREEN=0x008000  # Green

  # Reds (high contrast)
  CRIMSON=0xFF8080  # Bright red
  FIRE_RED=0xFF0000  # Red

  # Purples/Magentas
  PURPLE=0xFF80FF  # Bright magenta
  MAGENTA=0xFF00FF  # Magenta

  # Oranges/Yellows
  ORANGE=0xFFA500  # Orange
  GOLD=0xFFFF80  # Bright yellow

  # Cyans (excellent contrast)
  CYAN=0x00FFFF  # Cyan
  TEAL=0x80FFFF  # Bright cyan
