"""Complete color theme configuration with adjustment capabilities."""
from __future__ import annotations

from typing import Optional

from auto_cli.theme.enums import Back, Fore, ForeUniversal
from auto_cli.theme.rgb import AdjustStrategy, RGB
from auto_cli.theme.theme_style import ThemeStyle

class Theme:
  """
  Complete color theme configuration for CLI output with dynamic adjustment capabilities.
  Defines styling for all major UI elements in the help output with optional color adjustment.
  """

  def __init__(self, title: ThemeStyle, subtitle: ThemeStyle, command_name: ThemeStyle, command_description: ThemeStyle,
               group_command_name: ThemeStyle, subcommand_name: ThemeStyle, subcommand_description: ThemeStyle,
               option_name: ThemeStyle, option_description: ThemeStyle, required_option_name: ThemeStyle,
               required_option_description: ThemeStyle, required_asterisk: ThemeStyle,  # New adjustment parameters
               adjust_strategy: AdjustStrategy = AdjustStrategy.LINEAR, adjust_percent: float = 0.0):
    """Initialize theme with optional color adjustment settings."""
    if adjust_percent < -5.0 or adjust_percent > 5.0:
      raise ValueError(f"adjust_percent must be between -5.0 and 5.0, got {adjust_percent}")
    self.title = title
    self.subtitle = subtitle
    self.command_name = command_name
    self.command_description = command_description
    self.group_command_name = group_command_name
    self.subcommand_name = subcommand_name
    self.subcommand_description = subcommand_description
    self.option_name = option_name
    self.option_description = option_description
    self.required_option_name = required_option_name
    self.required_option_description = required_option_description
    self.required_asterisk = required_asterisk
    self.adjust_strategy = adjust_strategy
    self.adjust_percent = adjust_percent

  def create_adjusted_copy(self, adjust_percent: float, adjust_strategy: Optional[AdjustStrategy] = None) -> 'Theme':
    """Create a new theme with adjusted colors.

    :param adjust_percent: Adjustment percentage (-5.0 to 5.0)
    :param adjust_strategy: Optional strategy override
    :return: New Theme instance with adjusted colors
    """
    if adjust_percent < -5.0 or adjust_percent > 5.0:
      raise ValueError(f"adjust_percent must be between -5.0 and 5.0, got {adjust_percent}")

    strategy = adjust_strategy or self.adjust_strategy

    # Temporarily set adjustment parameters for the adjustment process
    old_adjust_percent = self.adjust_percent
    old_adjust_strategy = self.adjust_strategy
    self.adjust_percent = adjust_percent
    self.adjust_strategy = strategy

    try:
      new_theme = Theme(
        title=self.get_adjusted_style(self.title), subtitle=self.get_adjusted_style(self.subtitle),
        command_name=self.get_adjusted_style(self.command_name),
        command_description=self.get_adjusted_style(self.command_description),
        group_command_name=self.get_adjusted_style(self.group_command_name),
        subcommand_name=self.get_adjusted_style(self.subcommand_name),
        subcommand_description=self.get_adjusted_style(self.subcommand_description),
        option_name=self.get_adjusted_style(self.option_name),
        option_description=self.get_adjusted_style(self.option_description),
        required_option_name=self.get_adjusted_style(self.required_option_name),
        required_option_description=self.get_adjusted_style(self.required_option_description),
        required_asterisk=self.get_adjusted_style(self.required_asterisk), adjust_strategy=strategy,
        adjust_percent=adjust_percent
      )
    finally:
      # Restore original adjustment parameters
      self.adjust_percent = old_adjust_percent
      self.adjust_strategy = old_adjust_strategy

    return new_theme

  def get_adjusted_style(self, original: ThemeStyle) -> ThemeStyle:
    """Create a ThemeStyle with adjusted colors.

    :param original: Original ThemeStyle
    :return: ThemeStyle with adjusted colors
    """
    adjusted_fg = None
    if original.fg:
      # Use RGB adjustment method directly
      adjusted_fg = original.fg.adjust(brightness=self.adjust_percent, strategy=self.adjust_strategy)

    # Background adjustment disabled for now (as in original)
    adjusted_bg = original.bg

    return ThemeStyle(
      fg=adjusted_fg, bg=adjusted_bg, bold=original.bold, italic=original.italic, dim=original.dim,
      underline=original.underline
    )


def create_default_theme() -> Theme:
  """Create a default color theme using universal colors for optimal cross-platform compatibility."""
  return Theme(
    adjust_percent=0.0,
    title=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.PURPLE.value), bg=RGB.from_rgb(Back.LIGHTWHITE_EX.value), bold=True),
    subtitle=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.BROWN.value), italic=True),
    command_name=ThemeStyle(bold=True),
    command_description=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.OKABE_BLUE.value)),
    group_command_name=ThemeStyle(bold=True),
    subcommand_name=ThemeStyle(italic=True, bold=True),
    subcommand_description=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.OKABE_BLUE.value)),
    option_name=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.DARK_GREEN.value)),
    option_description=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.BROWN.value)),
    required_option_name=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.DARK_GREEN.value), bold=True),
    required_option_description=ThemeStyle(fg=RGB.from_rgb(Fore.WHITE.value)),
    required_asterisk=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.BROWN.value))
  )


def create_default_theme_colorful() -> Theme:
  """Create a colorful theme with traditional terminal colors."""
  return Theme(
    title=ThemeStyle(fg=RGB.from_rgb(Fore.MAGENTA.value), bg=RGB.from_rgb(Back.LIGHTWHITE_EX.value), bold=True),
    # Dark magenta bold with light gray background
    subtitle=ThemeStyle(fg=RGB.from_rgb(Fore.YELLOW.value), italic=True),
    command_name=ThemeStyle(fg=RGB.from_rgb(Fore.CYAN.value), bold=True),
    # Cyan bold for command names
    command_description=ThemeStyle(fg=RGB.from_rgb(Fore.LIGHTRED_EX.value)),
    group_command_name=ThemeStyle(fg=RGB.from_rgb(Fore.CYAN.value), bold=True),  # Cyan bold for group command names
    subcommand_name=ThemeStyle(fg=RGB.from_rgb(Fore.CYAN.value), italic=True, bold=True),  # Cyan italic bold for subcommand names
    subcommand_description=ThemeStyle(fg=RGB.from_rgb(Fore.LIGHTRED_EX.value)),  # Orange (LIGHTRED_EX) for subcommand descriptions
    option_name=ThemeStyle(fg=RGB.from_rgb(Fore.GREEN.value)),  # Green for all options
    option_description=ThemeStyle(fg=RGB.from_rgb(Fore.YELLOW.value)),  # Yellow for option descriptions
    required_option_name=ThemeStyle(fg=RGB.from_rgb(Fore.GREEN.value), bold=True),  # Green bold for required options
    required_option_description=ThemeStyle(fg=RGB.from_rgb(Fore.WHITE.value)),  # White for required descriptions
    required_asterisk=ThemeStyle(fg=RGB.from_rgb(Fore.YELLOW.value))  # Yellow for required asterisk markers
  )


def create_no_color_theme() -> Theme:
  """Create a theme with no colors (fallback for non-color terminals)."""
  return Theme(
    title=ThemeStyle(), subtitle=ThemeStyle(), command_name=ThemeStyle(), command_description=ThemeStyle(),
    group_command_name=ThemeStyle(), subcommand_name=ThemeStyle(), subcommand_description=ThemeStyle(),
    option_name=ThemeStyle(), option_description=ThemeStyle(), required_option_name=ThemeStyle(),
    required_option_description=ThemeStyle(), required_asterisk=ThemeStyle()
  )
