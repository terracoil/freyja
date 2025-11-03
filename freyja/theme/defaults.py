"""Default theme configurations for Freyja CLI."""

from .fore import Fore
from .rgb import RGB
from .theme import Theme
from .theme_style import ThemeStyle


def create_default_theme() -> Theme:
    """Create the default colorful theme with command output styling."""
    # Create magenta color for command output (Fore.MAGENTA + bold)
    magenta_rgb = RGB.from_rgb(Fore.MAGENTA.value)

    command_output_style = ThemeStyle(fg=magenta_rgb, bold=True)

    return Theme(command_output=command_output_style)


def create_universal_theme() -> Theme:
    """Create a universal theme compatible with all terminals."""
    # For universal theme, use a dimmed style instead of color
    command_output_style = ThemeStyle(
        bold=True, dim=False  # Just bold, no color for universal compatibility
    )

    return Theme(command_output=command_output_style)


def get_theme_by_name(theme_name: str) -> Theme:
    """Get a theme by name.

    :param theme_name: Name of the theme ('default', 'colorful', 'universal')
    :return: Theme instance
    :raises ValueError: If theme name is not recognized
    """
    theme_map = {
        "default": create_default_theme,
        "colorful": create_default_theme,  # colorful is the same as default
        "universal": create_universal_theme,
    }

    if theme_name not in theme_map:
        raise ValueError(
            f"Unknown theme name: {theme_name}. Available themes: {list(theme_map.keys())}"
        )

    return theme_map[theme_name]()
