"""Complete color theme configuration with adjustment capabilities."""
from __future__ import annotations

from typing import Optional

from auto_cli.math_utils import MathUtils
from auto_cli.theme.color_utils import hex_to_rgb, is_valid_hex_color, rgb_to_hex
from auto_cli.theme.enums import AdjustStrategy, Back, Fore, ForeUniversal
from auto_cli.theme.theme_style import ThemeStyle


class Themes:
  """
  Complete color theme configuration for CLI output with dynamic adjustment capabilities.
  Defines styling for all major UI elements in the help output with optional color adjustment.
  """

  def __init__(self, title: ThemeStyle, subtitle: ThemeStyle, command_name: ThemeStyle, command_description: ThemeStyle,
               group_command_name: ThemeStyle, subcommand_name: ThemeStyle, subcommand_description: ThemeStyle,
               option_name: ThemeStyle, option_description: ThemeStyle, required_option_name: ThemeStyle,
               required_option_description: ThemeStyle, required_asterisk: ThemeStyle,  # New adjustment parameters
               adjust_strategy: AdjustStrategy = AdjustStrategy.PROPORTIONAL, adjust_percent: float = 0.0):
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

  def get_adjusted_style(self, style_name: str) -> Optional[ThemeStyle]:
    """Get a style with adjusted colors by name.

    :param style_name: Name of the style attribute
    :return: ThemeStyle with adjusted colors, or None if style doesn't exist
    """
    result = None

    if hasattr(self, style_name):
      original_style = getattr(self, style_name)
      if isinstance(original_style, ThemeStyle):
        # Create a new style with adjusted colors
        adjusted_fg = self.adjust_color(original_style.fg) if original_style.fg else None
        print(f"Adjusted {style_name}: {original_style.fg} to {adjusted_fg}")
        adjusted_bg = original_style.bg#self.adjust_color(original_style.bg) if original_style.bg else None

        result = ThemeStyle(
          fg=adjusted_fg, bg=adjusted_bg, bold=original_style.bold, italic=original_style.italic,
          dim=original_style.dim, underline=original_style.underline
        )

    return result

  def adjust_color(self, color: Optional[str]) -> Optional[str]:
    """Apply adjustment to a color based on the current strategy.

    :param color: Original color (hex, ANSI, or None)
    :return: Adjusted color or original if adjustment not possible/needed
    """
    result = color
    # print(f"adjust_color: #{color}: #{is_valid_hex_color(color)}")
    # Only adjust if we have a color, adjustment percentage, and it's a hex color
    if color and self.adjust_percent != 0 and is_valid_hex_color(color):
      try:
        r, g, b = hex_to_rgb(color)
        rgb = None
        # print("adjust_color2")
        val_min, val_max = self.max_rgb_adjust(r, g, b)
        if self.adjust_strategy == AdjustStrategy.PROPORTIONAL:
          a = MathUtils.clamp(self.adjust_percent, val_min, val_max)
          rgb = [int(v * a) for v in (r, g, b)]
          # print(f"Multiplied {[r, g, b]} by {a} to get {rgb} = {rgb_to_hex(*rgb)}\n")
        elif self.adjust_strategy == AdjustStrategy.ABSOLUTE:
          # print("adjust_color3 absolute")
          rgb = [MathUtils.clamp(int(x + self.adjust_percent), 0, 255) for x in (r, g, b)]

        result = rgb_to_hex(*rgb)
      except (ValueError, TypeError) as e:
        print(f"Error: {e}")
        # Return original color if adjustment fails
        pass

    # print(f"adjust_color: #{color} => #{result}")
    return result

  def max_rgb_adjust(self, r: int, g: int, b: int) -> [float, float]:
    """Calculate safe adjustment that won't exceed RGB bounds.

    :param r: Red component (0-255)
    :param g: Green component (0-255)
    :param b: Blue component (0-255)
    :return: Safe adjustment amount
    """
    # Upper bound: ensure all values stay <= 255 when multiplied
    v_min, v_max = MathUtils.minmax_range(r, g, b, True)
    return [self.color_pct(v) for v in [v_min, v_max]]

  def color_pct(self, v: float) -> float:
    return MathUtils.percent(v, 255.0)

  def create_adjusted_copy(self, adjust_percent: float, adjust_strategy: Optional[AdjustStrategy] = None) -> 'Themes':
    """Create a new theme with adjusted colors.

    :param adjust_percent: Adjustment percentage (-5.0 to 5.0)
    :param adjust_strategy: Optional strategy override
    :return: New Themes instance with adjusted colors
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
      new_theme = Themes(
        title=self.get_adjusted_style('title'),
        subtitle=self.get_adjusted_style('subtitle'),
        command_name=self.get_adjusted_style('command_name'),
        command_description=self.get_adjusted_style('command_description'),
        group_command_name=self.get_adjusted_style('group_command_name'),
        subcommand_name=self.get_adjusted_style('subcommand_name'),
        subcommand_description=self.get_adjusted_style('subcommand_description'),
        option_name=self.get_adjusted_style('option_name'),
        option_description=self.get_adjusted_style('option_description'),
        required_option_name=self.get_adjusted_style('required_option_name'),
        required_option_description=self.get_adjusted_style('required_option_description'),
        required_asterisk=self.get_adjusted_style('required_asterisk'),
        adjust_strategy=strategy,
        adjust_percent=adjust_percent
      )
    finally:
      # Restore original adjustment parameters
      self.adjust_percent = old_adjust_percent
      self.adjust_strategy = old_adjust_strategy

    return new_theme

  # def _create_adjusted_theme_style(self, original: ThemeStyle) -> ThemeStyle:
  #   """Create a ThemeStyle with adjusted colors.
  #
  #   :param original: Original ThemeStyle
  #   :return: ThemeStyle with adjusted colors
  #   """
  #   adjusted_fg = self.adjust_color(original.fg) if original.fg else None
  #   adjusted_bg = original.bg # self.adjust_color(original.bg) if original.bg else None
  #
  #   return ThemeStyle(
  #     fg=adjusted_fg, bg=adjusted_bg, bold=original.bold, italic=original.italic, dim=original.dim,
  #     underline=original.underline
  #   )


def create_default_theme() -> Themes:
  """Create a default color theme using universal colors for optimal cross-platform compatibility."""
  return Themes(
    adjust_percent=0.0, title=ThemeStyle(fg=ForeUniversal.PURPLE.value, bg=Back.LIGHTWHITE_EX.value, bold=True),
    # Purple bold with light gray background
    subtitle=ThemeStyle(fg=ForeUniversal.GOLD.value, italic=True),  # Gold for subtitles
    command_name=ThemeStyle(fg=ForeUniversal.BRIGHT_BLUE.value, bold=True),  # Bright blue bold for command names
    command_description=ThemeStyle(fg=Fore.LIGHTRED_EX.value),  # Orange (LIGHTRED_EX) for descriptions
    group_command_name=ThemeStyle(fg=ForeUniversal.BRIGHT_BLUE.value, bold=True),
    # Bright blue bold for group command names
    subcommand_name=ThemeStyle(fg=ForeUniversal.BRIGHT_BLUE.value, italic=True, bold=True),
    # Bright blue italic bold for subcommand names
    subcommand_description=ThemeStyle(fg=Fore.LIGHTRED_EX.value),  # Orange (LIGHTRED_EX) for subcommand descriptions
    option_name=ThemeStyle(fg=ForeUniversal.FOREST_GREEN.value),  # FOREST_GREEN for all options
    option_description=ThemeStyle(fg=ForeUniversal.GOLD.value),  # Gold for option descriptions
    required_option_name=ThemeStyle(fg=ForeUniversal.FOREST_GREEN.value, bold=True),
    # FOREST_GREEN bold for required options
    required_option_description=ThemeStyle(fg=Fore.WHITE.value),  # White for required descriptions
    required_asterisk=ThemeStyle(fg=ForeUniversal.GOLD.value)  # Gold for required asterisk markers
  )


def create_default_theme_colorful() -> Themes:
  """Create a colorful theme with traditional terminal colors."""
  return Themes(
    title=ThemeStyle(fg=Fore.MAGENTA.value, bg=Back.LIGHTWHITE_EX.value, bold=True),
    # Dark magenta bold with light gray background
    subtitle=ThemeStyle(fg=Fore.YELLOW.value, italic=True), command_name=ThemeStyle(fg=Fore.CYAN.value, bold=True),
    # Cyan bold for command names
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


def create_no_color_theme() -> Themes:
  """Create a theme with no colors (fallback for non-color terminals)."""
  return Themes(
    title=ThemeStyle(), subtitle=ThemeStyle(), command_name=ThemeStyle(), command_description=ThemeStyle(),
    group_command_name=ThemeStyle(), subcommand_name=ThemeStyle(), subcommand_description=ThemeStyle(),
    option_name=ThemeStyle(), option_description=ThemeStyle(), required_option_name=ThemeStyle(),
    required_option_description=ThemeStyle(), required_asterisk=ThemeStyle()
  )
