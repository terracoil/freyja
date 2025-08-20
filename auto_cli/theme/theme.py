"""Color theming system for CLI output using custom ANSI escape sequences."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Union

from auto_cli.theme.enums import Back, Fore, ForeUniversal, Style



@dataclass
class ThemeStyle:
    """
    Individual style configuration for text formatting.
    Supports foreground/background colors (named or hex) and text decorations.
    """
    fg: str | None = None          # Foreground color (name or hex)
    bg: str | None = None          # Background color (name or hex)
    bold: bool = False             # Bold text
    italic: bool = False           # Italic text (may not work on all terminals)
    dim: bool = False              # Dimmed/faint text
    underline: bool = False        # Underlined text


@dataclass
class Theme:
    """
    Complete color theme configuration for CLI output.
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

    def __init__(self, enable_colors: Union[bool, None] = None):
        """Initialize color formatter with automatic color detection.

        :param enable_colors: Force enable/disable colors, or None for auto-detection
        """
        if enable_colors is None:
            # Auto-detect: enable colors for TTY terminals only
            self.colors_enabled = self._is_color_terminal()
        else:
            self.colors_enabled = enable_colors

        if self.colors_enabled:
            self.enable_windows_ansi_support()

    @staticmethod
    def enable_windows_ansi_support():
        """Enable ANSI escape sequences on Windows terminals."""
        if sys.platform != 'win32':
            return

        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            # Fail silently on older Windows versions or permission issues
            pass



    def _is_color_terminal(self) -> bool:
        """Check if the current terminal supports colors."""
        import os

        result = True
        
        # Check for explicit disable first
        if os.environ.get('NO_COLOR') or os.environ.get('CLICOLOR') == '0':
            result = False
        elif os.environ.get('FORCE_COLOR') or os.environ.get('CLICOLOR'):
            # Check for explicit enable
            result = True
        elif not sys.stdout.isatty():
            # Check if stdout is a TTY (not redirected to file/pipe)
            result = False
        else:
            # Check environment variables that indicate color support
            term = sys.platform
            if term == 'win32':
                # Windows terminal color support
                result = True
            else:
                # Unix-like systems
                term_env = os.environ.get('TERM', '').lower()
                if 'color' in term_env or term_env in ('xterm', 'xterm-256color', 'screen'):
                    result = True
                elif term_env in ('dumb', ''):
                    # Default for dumb terminals or empty TERM
                    result = False
                else:
                    result = True

        return result

    def apply_style(self, text: str, style: ThemeStyle) -> str:
        """Apply a theme style to text.

        :param text: Text to style
        :param style: ThemeStyle configuration to apply
        :return: Styled text (or original text if colors disabled)
        """
        result = text
        
        if self.colors_enabled and text:
            # Build color codes
            codes = []

            # Foreground color - handle hex colors and ANSI codes
            if style.fg:
                if style.fg.startswith('#'):
                    # Hex color - convert to ANSI
                    fg_code = self._hex_to_ansi(style.fg, is_background=False)
                    if fg_code:
                        codes.append(fg_code)
                elif style.fg.startswith('\x1b['):
                    # Direct ANSI code
                    codes.append(style.fg)
                else:
                    # Fallback to old method for backwards compatibility
                    fg_code = self._get_color_code(style.fg, is_background=False)
                    if fg_code:
                        codes.append(fg_code)

            # Background color - handle hex colors and ANSI codes  
            if style.bg:
                if style.bg.startswith('#'):
                    # Hex color - convert to ANSI
                    bg_code = self._hex_to_ansi(style.bg, is_background=True)
                    if bg_code:
                        codes.append(bg_code)
                elif style.bg.startswith('\x1b['):
                    # Direct ANSI code
                    codes.append(style.bg)
                else:
                    # Fallback to old method for backwards compatibility
                    bg_code = self._get_color_code(style.bg, is_background=True)
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
                result = ''.join(codes) + text + Style.RESET_ALL.value
                
        return result

    def _hex_to_ansi(self, hex_color: str, is_background: bool = False) -> str:
        """Convert hex colors to ANSI escape codes.

        :param hex_color: Hex value (e.g., '#FF0000')
        :param is_background: Whether this is a background color
        :return: ANSI color code or empty string
        """
        # Map common hex colors to ANSI codes
        hex_to_ansi_fg = {
            '#000000': '\x1b[30m', '#FF0000': '\x1b[31m', '#008000': '\x1b[32m',
            '#FFFF00': '\x1b[33m', '#0000FF': '\x1b[34m', '#FF00FF': '\x1b[35m',
            '#00FFFF': '\x1b[36m', '#FFFFFF': '\x1b[37m',
            '#808080': '\x1b[90m', '#FF8080': '\x1b[91m',
            '#80FF80': '\x1b[92m', '#FFFF80': '\x1b[93m',
            '#8080FF': '\x1b[94m', '#FF80FF': '\x1b[95m',
            '#80FFFF': '\x1b[96m', '#F0F0F0': '\x1b[97m',
            '#FFA500': '\x1b[33m',  # Orange maps to yellow (closest available)
        }

        hex_to_ansi_bg = {
            '#000000': '\x1b[40m', '#FF0000': '\x1b[41m', '#008000': '\x1b[42m',
            '#FFFF00': '\x1b[43m', '#0000FF': '\x1b[44m', '#FF00FF': '\x1b[45m',
            '#00FFFF': '\x1b[46m', '#FFFFFF': '\x1b[47m',
            '#808080': '\x1b[100m', '#FF8080': '\x1b[101m',
            '#80FF80': '\x1b[102m', '#FFFF80': '\x1b[103m',
            '#8080FF': '\x1b[104m', '#FF80FF': '\x1b[105m',
            '#80FFFF': '\x1b[106m', '#F0F0F0': '\x1b[107m',
        }

        color_map = hex_to_ansi_bg if is_background else hex_to_ansi_fg
        return color_map.get(hex_color.upper(), "")

    def _get_color_code(self, color: str, is_background: bool = False) -> str:
        """Convert color names to ANSI escape codes (backwards compatibility).

        :param color: Color name or hex value
        :param is_background: Whether this is a background color
        :return: ANSI color code or empty string
        """
        return self._hex_to_ansi(color, is_background) if color.startswith('#') else ""


def create_default_theme() -> Theme:
    """Create a default color theme using universal colors for optimal cross-platform compatibility."""
    return Theme(
        title=ThemeStyle(fg=ForeUniversal.PURPLE.value, bg=Back.LIGHTWHITE_EX.value, bold=True),  # Purple bold with light gray background
        subtitle=ThemeStyle(fg=ForeUniversal.GOLD.value, italic=True),  # Gold for subtitles
        command_name=ThemeStyle(fg=ForeUniversal.BRIGHT_BLUE.value, bold=True),  # Bright blue bold for command names
        command_description=ThemeStyle(fg=Fore.LIGHTRED_EX.value),  # Orange (LIGHTRED_EX) for descriptions
        group_command_name=ThemeStyle(fg=ForeUniversal.BRIGHT_BLUE.value, bold=True),  # Bright blue bold for group command names
        subcommand_name=ThemeStyle(fg=ForeUniversal.BRIGHT_BLUE.value, italic=True, bold=True),  # Bright blue italic bold for subcommand names
        subcommand_description=ThemeStyle(fg=Fore.LIGHTRED_EX.value),  # Orange (LIGHTRED_EX) for subcommand descriptions
        option_name=ThemeStyle(fg=ForeUniversal.FOREST_GREEN.value),  # FOREST_GREEN for all options
        option_description=ThemeStyle(fg=ForeUniversal.GOLD.value),  # Gold for option descriptions
        required_option_name=ThemeStyle(fg=ForeUniversal.FOREST_GREEN.value, bold=True),  # FOREST_GREEN bold for required options
        required_option_description=ThemeStyle(fg=Fore.WHITE.value),  # White for required descriptions
        required_asterisk=ThemeStyle(fg=ForeUniversal.GOLD.value)  # Gold for required asterisk markers
    )


def create_default_theme_colorful() -> Theme:
    """Create a colorful theme with traditional terminal colors."""
    return Theme(
        title=ThemeStyle(fg=Fore.MAGENTA.value, bg=Back.LIGHTWHITE_EX.value, bold=True),  # Dark magenta bold with light gray background
        subtitle=ThemeStyle(fg=Fore.YELLOW.value, italic=True),
        command_name=ThemeStyle(fg=Fore.CYAN.value, bold=True),  # Cyan bold for command names
        command_description=ThemeStyle(fg=Fore.LIGHTRED_EX.value),  # Orange (LIGHTRED_EX) for flat command descriptions
        group_command_name=ThemeStyle(fg=Fore.CYAN.value, bold=True),  # Cyan bold for group command names
        subcommand_name=ThemeStyle(fg=Fore.CYAN.value, italic=True, bold=True),  # Cyan italic bold for subcommand names
        subcommand_description=ThemeStyle(fg=Fore.LIGHTRED_EX.value),  # Orange (LIGHTRED_EX) for subcommand descriptions
        option_name=ThemeStyle(fg=Fore.GREEN.value),  # Green for all options
        option_description=ThemeStyle(fg=Fore.YELLOW.value),  # Yellow for option descriptions
        required_option_name=ThemeStyle(fg=Fore.GREEN.value, bold=True),  # Green bold for required options
        required_option_description=ThemeStyle(fg=Fore.WHITE.value),  # White for required descriptions
        required_asterisk=ThemeStyle(fg=Fore.YELLOW.value)  # Yellow for required asterisk markers
    )


def create_no_color_theme() -> Theme:
    """Create a theme with no colors (fallback for non-color terminals)."""
    return Theme(
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

