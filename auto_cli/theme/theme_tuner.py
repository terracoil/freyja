"""Interactive theme tuning functionality for auto-cli-py.

This module provides interactive theme adjustment capabilities, allowing users
to fine-tune color schemes with real-time preview and RGB export functionality.
"""

import os

from auto_cli.theme import (AdjustStrategy, ColorFormatter, create_default_theme, create_default_theme_colorful, RGB)


class ThemeTuner:
  """Interactive theme color tuner with real-time preview and RGB export."""

  # Adjustment increment constant for easy modification
  ADJUSTMENT_INCREMENT=0.05

  def __init__(self, base_theme_name: str = "universal"):
    """Initialize the theme tuner.

    :param base_theme_name: Base theme to start with ("universal" or "colorful")
    """
    self.adjust_percent=0.0
    self.adjust_strategy=AdjustStrategy.PROPORTIONAL
    self.use_colorful_theme=base_theme_name.lower() == "colorful"
    self.formatter=ColorFormatter(enable_colors=True)

    # Get terminal width
    try:
      self.console_width=os.get_terminal_size().columns
    except (OSError, ValueError):
      self.console_width=int(os.environ.get('COLUMNS', 80))

  def get_current_theme(self):
    """Get the current theme with adjustments applied."""
    base_theme=create_default_theme_colorful() if self.use_colorful_theme else create_default_theme()

    try:
      return base_theme.create_adjusted_copy(
        adjust_percent=self.adjust_percent,
        adjust_strategy=self.adjust_strategy
      )
    except ValueError:
      return base_theme

  def display_theme_info(self):
    """Display current theme information and preview."""
    theme=self.get_current_theme()

    # Create a fresh formatter with the current adjusted theme
    current_formatter=ColorFormatter(enable_colors=True)

    # Simple header
    print("=" * min(self.console_width, 60))
    print("🎛️  THEME TUNER")
    print("=" * min(self.console_width, 60))

    # Current settings
    strategy_name="PROPORTIONAL" if self.adjust_strategy == AdjustStrategy.PROPORTIONAL else "ABSOLUTE"
    theme_name="COLORFUL" if self.use_colorful_theme else "UNIVERSAL"

    print(f"Theme: {theme_name}")
    print(f"Strategy: {strategy_name}")
    print(f"Adjust: {self.adjust_percent:.2f}")
    print()

    # Simple preview with real-time color updates
    print("📋 CLI Preview:")
    print(
      f"  {current_formatter.apply_style('hello', theme.command_name)}: {current_formatter.apply_style('Greet the user', theme.command_description)}"
      )
    print(
      f"  {current_formatter.apply_style('--name NAME', theme.option_name)}: {current_formatter.apply_style('Specify name', theme.option_description)}"
      )
    print(
      f"  {current_formatter.apply_style('--email EMAIL', theme.required_option_name)} {current_formatter.apply_style('*', theme.required_asterisk)}: {current_formatter.apply_style('Required email', theme.required_option_description)}"
      )
    print()

  def display_rgb_values(self):
    """Display RGB values for theme incorporation."""
    theme=self.get_current_theme()  # Get the current adjusted theme

    print("\n" + "=" * min(self.console_width, 60))
    print("🎨 RGB VALUES FOR THEME INCORPORATION")
    print("=" * min(self.console_width, 60))

    # Color mappings for the current adjusted theme
    color_map=[
      ("title", theme.title.fg, "Title color"),
      ("subtitle", theme.subtitle.fg, "Subtitle color"),
      ("command_name", theme.command_name.fg, "Command name"),
      ("command_description", theme.command_description.fg, "Command description"),
      ("option_name", theme.option_name.fg, "Option name"),
      ("required_option_name", theme.required_option_name.fg, "Required option name"),
    ]

    for name, color_code, description in color_map:
      if isinstance(color_code, RGB):
        # RGB instance
        r, g, b = color_code.to_ints()
        hex_code = color_code.to_hex()
        print(f"  {name:20} = rgb({r:3}, {g:3}, {b:3})  # {hex_code}")
      elif color_code and isinstance(color_code, str) and color_code.startswith('#'):
        # Hex string
        try:
          hex_clean = color_code.strip().lstrip('#').upper()
          if len(hex_clean) == 3:
            hex_clean = ''.join(c * 2 for c in hex_clean)
          if len(hex_clean) == 6 and all(c in '0123456789ABCDEF' for c in hex_clean):
            hex_int = int(hex_clean, 16)
            rgb = RGB.from_rgb(hex_int)
            r, g, b = rgb.to_ints()
            print(f"  {name:20} = rgb({r:3}, {g:3}, {b:3})  # {color_code}")
          else:
            print(f"  {name:20} = {color_code}")
        except ValueError:
          print(f"  {name:20} = {color_code}")
      elif color_code:
        print(f"  {name:20} = {color_code}")

    print("=" * min(self.console_width, 60))

  def run_interactive_menu(self):
    """Run a simple menu-based theme tuner."""
    print("🎛️  THEME TUNER")
    print("=" * 40)
    print("Interactive controls are not available in this environment.")
    print("Using simple menu mode instead.")
    print()

    while True:
      self.display_theme_info()

      print("Available commands:")
      print(f"  [+] Increase adjustment by {self.ADJUSTMENT_INCREMENT}")
      print(f"  [-] Decrease adjustment by {self.ADJUSTMENT_INCREMENT}")
      print("  [s] Toggle strategy")
      print("  [t] Toggle theme (universal/colorful)")
      print("  [r] Show RGB values")
      print("  [q] Quit")

      try:
        choice=input("\nEnter command: ").lower().strip()

        if choice == 'q':
          break
        elif choice == '+':
          self.adjust_percent=min(5.0, self.adjust_percent + self.ADJUSTMENT_INCREMENT)
          print(f"Adjustment increased to {self.adjust_percent:.2f}")
        elif choice == '-':
          self.adjust_percent=max(-5.0, self.adjust_percent - self.ADJUSTMENT_INCREMENT)
          print(f"Adjustment decreased to {self.adjust_percent:.2f}")
        elif choice == 's':
          self.adjust_strategy=AdjustStrategy.ABSOLUTE if self.adjust_strategy == AdjustStrategy.PROPORTIONAL else AdjustStrategy.PROPORTIONAL
          strategy_name="ABSOLUTE" if self.adjust_strategy == AdjustStrategy.ABSOLUTE else "PROPORTIONAL"
          print(f"Strategy changed to {strategy_name}")
        elif choice == 't':
          self.use_colorful_theme=not self.use_colorful_theme
          theme_name="COLORFUL" if self.use_colorful_theme else "UNIVERSAL"
          print(f"Theme changed to {theme_name}")
        elif choice == 'r':
          self.display_rgb_values()
          input("\nPress Enter to continue...")
        else:
          print("Invalid command. Try again.")

        print()

      except (KeyboardInterrupt, EOFError):
        break

    print("\n🎨 Theme tuning session ended.")

  def run(self):
    """Run the theme tuner in the most appropriate mode."""
    # Always use menu mode since raw terminal mode is problematic
    self.run_interactive_menu()


def run_theme_tuner(base_theme: str = "universal") -> None:
  """Convenience function to run the theme tuner.

  :param base_theme: Base theme to start with (universal or colorful)
  """
  tuner=ThemeTuner(base_theme)
  tuner.run()
