from enum import Enum


class Fore(Enum):
    """Foreground color constants."""
    BLACK = '#000000'
    RED = '#FF0000'
    GREEN = '#008000'
    YELLOW = '#FFFF00'
    BLUE = '#0000FF'
    MAGENTA = '#FF00FF'
    CYAN = '#00FFFF'
    WHITE = '#FFFFFF'

    # Bright colors
    LIGHTBLACK_EX = '#808080'
    LIGHTRED_EX = '#FF8080'
    LIGHTGREEN_EX = '#80FF80'
    LIGHTYELLOW_EX = '#FFFF80'
    LIGHTBLUE_EX = '#8080FF'
    LIGHTMAGENTA_EX = '#FF80FF'
    LIGHTCYAN_EX = '#80FFFF'
    LIGHTWHITE_EX = '#F0F0F0'


class Back(Enum):
    """Background color constants."""
    BLACK = '#000000'
    RED = '#FF0000'
    GREEN = '#008000'
    YELLOW = '#FFFF00'
    BLUE = '#0000FF'
    MAGENTA = '#FF00FF'
    CYAN = '#00FFFF'
    WHITE = '#FFFFFF'

    # Bright backgrounds
    LIGHTBLACK_EX = '#808080'
    LIGHTRED_EX = '#FF8080'
    LIGHTGREEN_EX = '#80FF80'
    LIGHTYELLOW_EX = '#FFFF80'
    LIGHTBLUE_EX = '#8080FF'
    LIGHTMAGENTA_EX = '#FF80FF'
    LIGHTCYAN_EX = '#80FFFF'
    LIGHTWHITE_EX = '#F0F0F0'


class Style(Enum):
    """Text style constants."""
    DIM = '\x1b[2m'
    RESET_ALL = '\x1b[0m'
    # All ANSI style codes in one place
    ANSI_BOLD = '\x1b[1m'      # Bold text
    ANSI_ITALIC = '\x1b[3m'    # Italic text (support varies by terminal)
    ANSI_UNDERLINE = '\x1b[4m' # Underlined text



class ForeUniversal(Enum):
    """Universal foreground colors that work well on both light and dark backgrounds."""
    # Blues (excellent on both)
    BRIGHT_BLUE = '#8080FF'       # Bright blue
    ROYAL_BLUE = '#0000FF'        # Blue

    # Greens (great visibility)
    EMERALD = '#80FF80'           # Bright green
    FOREST_GREEN = '#008000'      # Green

    # Reds (high contrast)
    CRIMSON = '#FF8080'           # Bright red
    FIRE_RED = '#FF0000'          # Red

    # Purples/Magentas
    PURPLE = '#FF80FF'            # Bright magenta
    MAGENTA = '#FF00FF'           # Magenta

    # Oranges/Yellows
    ORANGE = '#FFA500'            # Orange
    GOLD = '#FFFF80'              # Bright yellow

    # Cyans (excellent contrast)
    CYAN = '#00FFFF'              # Cyan
    TEAL = '#80FFFF'              # Bright cyan
