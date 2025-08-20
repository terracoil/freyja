"""Color theming system for CLI output using colorama."""
import sys
from dataclasses import dataclass
from typing import Any

try:
    from colorama import Back, Fore, Style
    from colorama import init as colorama_init
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback classes for when colorama is not available
    class _MockColorama:
        def __getattr__(self, name: str) -> str:
            return ""

    Fore = Back = Style = _MockColorama()
    def colorama_init(**kwargs: Any) -> None:
        pass


@dataclass
class ThemeStyle:
    """Individual style configuration for text formatting.

    Supports foreground/background colors (named or hex) and text decorations.
    """
    fg: str | None = None          # Foreground color (name or hex)
    bg: str | None = None          # Background color (name or hex)
    bold: bool = False             # Bold text
    italic: bool = False           # Italic text (may not work on all terminals)
    dim: bool = False              # Dimmed/faint text
    underline: bool = False        # Underlined text


@dataclass
class ColorTheme:
    """Complete color theme configuration for CLI output.

    Defines styling for all major UI elements in the help output.
    """
    title: ThemeStyle                      # Main CLI title/description
    subtitle: ThemeStyle                   # Section headers (e.g., "Commands:")
    command_name: ThemeStyle               # Command names
    command_description: ThemeStyle        # Command descriptions
    group_command_name: ThemeStyle         # Group command names (commands with subcommands)
    subcommand_name: ThemeStyle            # Subcommand names
    subcommand_description: ThemeStyle     # Subcommand descriptions
    option_name: ThemeStyle                # Optional argument names (--flag)
    option_description: ThemeStyle         # Optional argument descriptions
    required_option_name: ThemeStyle       # Required argument names
    required_option_description: ThemeStyle # Required argument descriptions
    required_asterisk: ThemeStyle          # Required asterisk marker (*)


class ColorFormatter:
    """Handles color application and terminal compatibility."""

    # Colorama color name mappings
    _FOREGROUND_COLORS = {
        'BLACK': Fore.BLACK,
        'RED': Fore.RED,
        'GREEN': Fore.GREEN,
        'YELLOW': Fore.YELLOW,
        'BLUE': Fore.BLUE,
        'MAGENTA': Fore.MAGENTA,
        'CYAN': Fore.CYAN,
        'WHITE': Fore.WHITE,
        'LIGHTBLACK_EX': Fore.LIGHTBLACK_EX,
        'LIGHTRED_EX': Fore.LIGHTRED_EX,
        'LIGHTGREEN_EX': Fore.LIGHTGREEN_EX,
        'LIGHTYELLOW_EX': Fore.LIGHTYELLOW_EX,
        'LIGHTBLUE_EX': Fore.LIGHTBLUE_EX,
        'LIGHTMAGENTA_EX': Fore.LIGHTMAGENTA_EX,
        'LIGHTCYAN_EX': Fore.LIGHTCYAN_EX,
        'LIGHTWHITE_EX': Fore.LIGHTWHITE_EX,
        # Add orange as a custom mapping to light red (closest to orange in terminal)
        'ORANGE': Fore.LIGHTRED_EX,
    }

    _BACKGROUND_COLORS = {
        'BLACK': Back.BLACK,
        'RED': Back.RED,
        'GREEN': Back.GREEN,
        'YELLOW': Back.YELLOW,
        'BLUE': Back.BLUE,
        'MAGENTA': Back.MAGENTA,
        'CYAN': Back.CYAN,
        'WHITE': Back.WHITE,
        'LIGHTBLACK_EX': Back.LIGHTBLACK_EX,
        'LIGHTRED_EX': Back.LIGHTRED_EX,
        'LIGHTGREEN_EX': Back.LIGHTGREEN_EX,
        'LIGHTYELLOW_EX': Back.LIGHTYELLOW_EX,
        'LIGHTBLUE_EX': Back.LIGHTBLUE_EX,
        'LIGHTMAGENTA_EX': Back.LIGHTMAGENTA_EX,
        'LIGHTCYAN_EX': Back.LIGHTCYAN_EX,
        'LIGHTWHITE_EX': Back.LIGHTWHITE_EX,
    }

    def __init__(self, enable_colors: bool | None = None):
        """Initialize color formatter with automatic color detection.

        :param enable_colors: Force enable/disable colors, or None for auto-detection
        """
        if enable_colors is None:
            # Auto-detect: enable colors for TTY terminals only
            self.colors_enabled = COLORAMA_AVAILABLE and self._is_color_terminal()
        else:
            self.colors_enabled = enable_colors and COLORAMA_AVAILABLE

        if self.colors_enabled:
            colorama_init(autoreset=True)

    def _is_color_terminal(self) -> bool:
        """Check if the current terminal supports colors."""
        import os
        
        # Check for explicit disable first
        if os.environ.get('NO_COLOR') or os.environ.get('CLICOLOR') == '0':
            return False
            
        # Check for explicit enable
        if os.environ.get('FORCE_COLOR') or os.environ.get('CLICOLOR'):
            return True

        # Check if stdout is a TTY (not redirected to file/pipe)
        if not sys.stdout.isatty():
            return False

        # Check environment variables that indicate color support
        term = sys.platform
        if term == 'win32':
            # Windows terminal color support
            return True

        # Unix-like systems
        term_env = os.environ.get('TERM', '').lower()
        if 'color' in term_env or term_env in ('xterm', 'xterm-256color', 'screen'):
            return True

        # Default for dumb terminals or empty TERM
        if term_env in ('dumb', ''):
            return False

        return True

    def apply_style(self, text: str, style: ThemeStyle) -> str:
        """Apply a theme style to text.

        :param text: Text to style
        :param style: ThemeStyle configuration to apply
        :return: Styled text (or original text if colors disabled)
        """
        if not self.colors_enabled or not text:
            return text

        # Build color codes
        codes = []

        # Foreground color
        if style.fg:
            fg_code = self._get_color_code(style.fg, is_background=False)
            if fg_code:
                codes.append(fg_code)

        # Background color
        if style.bg:
            bg_code = self._get_color_code(style.bg, is_background=True)
            if bg_code:
                codes.append(bg_code)

        # Text styling (using ANSI codes instead of Style.BRIGHT)
        if style.bold:
            codes.append('\x1b[1m')  # ANSI bold code (avoid Style.BRIGHT to prevent color shifts)
        if style.dim:
            codes.append(Style.DIM)
        if style.italic:
            codes.append('\x1b[3m')  # ANSI italic code (support varies by terminal)
        if style.underline:
            codes.append('\x1b[4m')  # ANSI underline code

        if not codes:
            return text

        # Apply formatting
        return ''.join(codes) + text + Style.RESET_ALL

    def _get_color_code(self, color: str, is_background: bool = False) -> str:
        """Convert color name or hex to colorama code.

        :param color: Color name (e.g., 'RED') or hex value (e.g., '#FF0000')
        :param is_background: Whether this is a background color
        :return: Colorama color code or empty string
        """
        color_upper = color.upper()
        color_map = self._BACKGROUND_COLORS if is_background else self._FOREGROUND_COLORS

        # Try direct color name lookup
        if color_upper in color_map:
            return color_map[color_upper]

        # Hex color support is limited in colorama, map common hex colors to names
        hex_to_name = {
            '#000000': 'BLACK', '#FF0000': 'RED', '#008000': 'GREEN',
            '#FFFF00': 'YELLOW', '#0000FF': 'BLUE', '#FF00FF': 'MAGENTA',
            '#00FFFF': 'CYAN', '#FFFFFF': 'WHITE',
            '#808080': 'LIGHTBLACK_EX', '#FF8080': 'LIGHTRED_EX',
            '#80FF80': 'LIGHTGREEN_EX', '#FFFF80': 'LIGHTYELLOW_EX',
            '#8080FF': 'LIGHTBLUE_EX', '#FF80FF': 'LIGHTMAGENTA_EX',
            '#80FFFF': 'LIGHTCYAN_EX', '#F0F0F0': 'LIGHTWHITE_EX',
            '#FFA500': 'YELLOW',  # Orange maps to yellow (closest available)
            '#FF8000': 'RED',     # Dark orange maps to red
        }

        if color.startswith('#') and color.upper() in hex_to_name:
            mapped_name = hex_to_name[color.upper()]
            if mapped_name in color_map:
                return color_map[mapped_name]

        return ""


def create_default_theme() -> ColorTheme:
    """Create a default color theme with reasonable, accessible colors."""
    return ColorTheme(
        title=ThemeStyle(fg='MAGENTA'),  # Dark magenta (no bold)
        subtitle=ThemeStyle(fg='YELLOW'),
        command_name=ThemeStyle(fg='CYAN', bold=True),  # Cyan bold for command names
        command_description=ThemeStyle(fg='ORANGE'),  # Orange for flat command descriptions (match subcommand descriptions)
        group_command_name=ThemeStyle(fg='CYAN', bold=True),  # Cyan bold for group command names
        subcommand_name=ThemeStyle(fg='CYAN', italic=True, bold=True),  # Cyan italic bold for subcommand names
        subcommand_description=ThemeStyle(fg='ORANGE'),  # Actual orange color for subcommand descriptions
        option_name=ThemeStyle(fg='GREEN'),  # Green for all options
        option_description=ThemeStyle(fg='YELLOW'),  # Keep yellow for option descriptions as requested
        required_option_name=ThemeStyle(fg='GREEN', bold=True),  # Green bold for required options
        required_option_description=ThemeStyle(fg='WHITE'),  # White for required descriptions
        required_asterisk=ThemeStyle(fg='YELLOW')  # Yellow for required asterisk markers
    )


def create_no_color_theme() -> ColorTheme:
    """Create a theme with no colors (fallback for non-color terminals)."""
    return ColorTheme(
        title=ThemeStyle(),
        subtitle=ThemeStyle(),
        command_name=ThemeStyle(),
        command_description=ThemeStyle(),
        group_command_name=ThemeStyle(),
        subcommand_name=ThemeStyle(),
        subcommand_description=ThemeStyle(),
        option_name=ThemeStyle(),
        option_description=ThemeStyle(),
        required_option_name=ThemeStyle(),
        required_option_description=ThemeStyle(),
        required_asterisk=ThemeStyle()
    )

