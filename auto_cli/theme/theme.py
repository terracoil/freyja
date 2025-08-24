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
               command_group_name: ThemeStyle, command_group_description: ThemeStyle,
               grouped_command_name: ThemeStyle, grouped_command_description: ThemeStyle,
               option_name: ThemeStyle, option_description: ThemeStyle,
               command_group_option_name: ThemeStyle, command_group_option_description: ThemeStyle,
               grouped_command_option_name: ThemeStyle, grouped_command_option_description: ThemeStyle,
               required_asterisk: ThemeStyle,
               adjust_strategy: AdjustStrategy = AdjustStrategy.LINEAR, adjust_percent: float = 0.0):
    """Initialize theme with optional color adjustment settings."""
    if adjust_percent < -5.0 or adjust_percent > 5.0:
      raise ValueError(f"adjust_percent must be between -5.0 and 5.0, got {adjust_percent}")
    self.title = title
    self.subtitle = subtitle
    self.command_name = command_name
    self.command_description = command_description
    # Command Group Level (inner class level)
    self.command_group_name = command_group_name
    self.command_group_description = command_group_description
    # Grouped Command Level (commands within the group)
    self.grouped_command_name = grouped_command_name
    self.grouped_command_description = grouped_command_description
    self.option_name = option_name
    self.option_description = option_description
    # Command Group Options
    self.command_group_option_name = command_group_option_name
    self.command_group_option_description = command_group_option_description
    # Grouped Command Options
    self.grouped_command_option_name = grouped_command_option_name
    self.grouped_command_option_description = grouped_command_option_description
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
        title=self.get_adjusted_style(self.title),
        subtitle=self.get_adjusted_style(self.subtitle),
        command_name=self.get_adjusted_style(self.command_name),
        command_description=self.get_adjusted_style(self.command_description),
        command_group_name=self.get_adjusted_style(self.command_group_name),
        command_group_description=self.get_adjusted_style(self.command_group_description),
        grouped_command_name=self.get_adjusted_style(self.grouped_command_name),
        grouped_command_description=self.get_adjusted_style(self.grouped_command_description),
        option_name=self.get_adjusted_style(self.option_name),
        option_description=self.get_adjusted_style(self.option_description),
        command_group_option_name=self.get_adjusted_style(self.command_group_option_name),
        command_group_option_description=self.get_adjusted_style(self.command_group_option_description),
        grouped_command_option_name=self.get_adjusted_style(self.grouped_command_option_name),
        grouped_command_option_description=self.get_adjusted_style(self.grouped_command_option_description),
        required_asterisk=self.get_adjusted_style(self.required_asterisk),
        adjust_strategy=strategy,
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
    title=ThemeStyle(bg=RGB.from_rgb(ForeUniversal.MEDIUM_GREY.value), bold=True),
    subtitle=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.TEAL.value), bold=True, italic=True),
    command_name=ThemeStyle(bold=True),
    command_description=ThemeStyle(bold=True),
    # Command Group Level (inner class level)
    command_group_name=ThemeStyle(bold=True),
    command_group_description=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.BROWN.value), bold=True),
    # Grouped Command Level (commands within the group)
    grouped_command_name=ThemeStyle(),
    grouped_command_description=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.BROWN.value), bold=True, italic=True),
    option_name=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.TEAL.value)),
    option_description=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.BROWN.value), bold=True),
    # Command Group Options
    command_group_option_name=ThemeStyle(),
    command_group_option_description=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.BROWN.value), bold=True),
    # Grouped Command Options
    grouped_command_option_name=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.TEAL.value)),
    grouped_command_option_description=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.BROWN.value), bold=True),
    required_asterisk=ThemeStyle(fg=RGB.from_rgb(ForeUniversal.GOLD.value))
  )


def create_default_theme_colorful() -> Theme:
  """Create a colorful theme with traditional terminal colors."""
  return Theme(
    title=ThemeStyle(fg=RGB.from_rgb(Fore.MAGENTA.value), bg=RGB.from_rgb(Back.LIGHTWHITE_EX.value), bold=True),
    subtitle=ThemeStyle(fg=RGB.from_rgb(Fore.YELLOW.value), italic=True),

    command_name=ThemeStyle(fg=RGB.from_rgb(Fore.CYAN.value), bold=True),
    command_description=ThemeStyle(fg=RGB.from_rgb(Fore.LIGHTRED_EX.value)),
    option_name=ThemeStyle(fg=RGB.from_rgb(Fore.GREEN.value)),
    option_description=ThemeStyle(fg=RGB.from_rgb(Fore.YELLOW.value)),

    grouped_command_name=ThemeStyle(fg=RGB.from_rgb(Fore.CYAN.value), italic=True, bold=True),
    grouped_command_description=ThemeStyle(fg=RGB.from_rgb(Fore.LIGHTRED_EX.value)),
    grouped_command_option_name=ThemeStyle(fg=RGB.from_rgb(Fore.GREEN.value)),
    grouped_command_option_description=ThemeStyle(fg=RGB.from_rgb(Fore.YELLOW.value)),

    command_group_name=ThemeStyle(fg=RGB.from_rgb(Fore.CYAN.value), bold=True),
    command_group_description=ThemeStyle(fg=RGB.from_rgb(Fore.LIGHTRED_EX.value)),
    command_group_option_name=ThemeStyle(fg=RGB.from_rgb(Fore.GREEN.value)),
    command_group_option_description=ThemeStyle(fg=RGB.from_rgb(Fore.YELLOW.value)),

    required_asterisk=ThemeStyle(fg=RGB.from_rgb(Fore.YELLOW.value))
  )


def create_no_color_theme() -> Theme:
  """Create a theme with no colors (fallback for non-color terminals)."""
  return Theme(
    title=ThemeStyle(), subtitle=ThemeStyle(), command_name=ThemeStyle(), command_description=ThemeStyle(),
    command_group_name=ThemeStyle(), command_group_description=ThemeStyle(),
    grouped_command_name=ThemeStyle(), grouped_command_description=ThemeStyle(),
    option_name=ThemeStyle(), option_description=ThemeStyle(),
    command_group_option_name=ThemeStyle(), command_group_option_description=ThemeStyle(),
    grouped_command_option_name=ThemeStyle(), grouped_command_option_description=ThemeStyle(),
    required_asterisk=ThemeStyle()
  )
