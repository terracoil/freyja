"""Interactive theme tuning functionality for auto-cli-py.

This module provides interactive theme adjustment capabilities, allowing users
to fine-tune color schemes with real-time preview and RGB export functionality.
"""

import os

from typing import Dict, Set

from auto_cli.theme import (AdjustStrategy, ColorFormatter, create_default_theme, create_default_theme_colorful, RGB)
from auto_cli.theme.theme_style import ThemeStyle


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

    # Individual color override tracking
    self.individual_color_overrides: Dict[str, RGB] = {}
    self.modified_components: Set[str] = set()

    # Theme component metadata for user interface
    self.theme_components = [
      ("title", "Title text"),
      ("subtitle", "Section headers (COMMANDS:, OPTIONS:)"),
      ("command_name", "Command names"),
      ("command_description", "Command descriptions"),
      ("group_command_name", "Group command names"),
      ("subcommand_name", "Subcommand names"),
      ("subcommand_description", "Subcommand descriptions"),
      ("option_name", "Option flags (--name)"),
      ("option_description", "Option descriptions"),
      ("required_option_name", "Required option flags"),
      ("required_option_description", "Required option descriptions"),
      ("required_asterisk", "Required field markers (*)")
    ]

    # Get terminal width
    try:
      self.console_width=os.get_terminal_size().columns
    except (OSError, ValueError):
      self.console_width=int(os.environ.get('COLUMNS', 80))

  def get_current_theme(self):
    """Get theme with global adjustments and individual overrides applied."""
    # 1. Start with base theme
    base_theme=create_default_theme_colorful() if self.use_colorful_theme else create_default_theme()

    # 2. Apply global adjustments if any
    if self.adjust_percent != 0.0:
      try:
        adjusted_theme = base_theme.create_adjusted_copy(
          adjust_percent=self.adjust_percent,
          adjust_strategy=self.adjust_strategy
        )
      except ValueError:
        adjusted_theme = base_theme
    else:
      adjusted_theme = base_theme

    # 3. Apply individual color overrides if any
    if self.individual_color_overrides:
      return self._apply_individual_overrides(adjusted_theme)

    return adjusted_theme

  def _apply_individual_overrides(self, theme):
    """Create new theme with individual color overrides applied."""
    from auto_cli.theme.theme import Theme

    # Get all current theme styles
    theme_styles = {}
    for component_name, _ in self.theme_components:
      original_style = getattr(theme, component_name)
      
      if component_name in self.individual_color_overrides:
        # Create new ThemeStyle with overridden color but preserve other attributes
        override_color = self.individual_color_overrides[component_name]
        theme_styles[component_name] = ThemeStyle(
          fg=override_color,
          bg=original_style.bg,
          bold=original_style.bold,
          italic=original_style.italic,
          dim=original_style.dim,
          underline=original_style.underline
        )
      else:
        # Use original style
        theme_styles[component_name] = original_style

    # Create new theme with overridden styles
    return Theme(
      adjust_percent=theme.adjust_percent,
      adjust_strategy=theme.adjust_strategy,
      **theme_styles
    )

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
    
    # Show modification status
    if self.individual_color_overrides:
      modified_count = len(self.individual_color_overrides)
      total_count = len(self.theme_components)
      modified_names = ', '.join(sorted(self.individual_color_overrides.keys()))
      print(f"Modified Components: {modified_count}/{total_count} ({modified_names})")
    else:
      print("Modified Components: None")
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
    """Display RGB values for theme incorporation with names colored in their RGB values on different backgrounds."""
    theme=self.get_current_theme()  # Get the current adjusted theme

    print("\n" + "=" * min(self.console_width, 60))
    print("🎨 RGB VALUES FOR THEME INCORPORATION")
    print("=" * min(self.console_width, 60))

    # Color mappings for the current adjusted theme - include ALL theme components
    color_map=[
      ("title", theme.title.fg, "Title color"),
      ("subtitle", theme.subtitle.fg, "Subtitle color"),
      ("command_name", theme.command_name.fg, "Command name"),
      ("command_description", theme.command_description.fg, "Command description"),
      ("group_command_name", theme.group_command_name.fg, "Group command name"),
      ("subcommand_name", theme.subcommand_name.fg, "Subcommand name"),
      ("subcommand_description", theme.subcommand_description.fg, "Subcommand description"),
      ("option_name", theme.option_name.fg, "Option name"),
      ("option_description", theme.option_description.fg, "Option description"),
      ("required_option_name", theme.required_option_name.fg, "Required option name"),
      ("required_option_description", theme.required_option_description.fg, "Required option description"),
      ("required_asterisk", theme.required_asterisk.fg, "Required asterisk"),
    ]

    # Create background colors for testing readability
    white_bg = RGB.from_rgb(0xFFFFFF)  # White background
    black_bg = RGB.from_rgb(0x000000)  # Black background

    # Collect theme code components
    theme_code_lines = []

    for name, color_code, description in color_map:
      if isinstance(color_code, RGB):
        # Check if this component has been modified
        is_modified = name in self.individual_color_overrides
        
        # RGB instance - show name in the actual color
        r, g, b = color_code.to_ints()
        hex_code = color_code.to_hex()
        hex_int = f"0x{hex_code[1:]}"  # Convert #FF80FF to 0xFF80FF

        # Get the complete theme style for this component (includes bold, italic, etc.)
        current_theme_style = getattr(theme, name)
        
        # Create styled versions using the complete theme style with different backgrounds
        # Only the white/black background versions should be styled
        white_bg_style = ThemeStyle(
          fg=color_code,
          bg=white_bg,
          bold=current_theme_style.bold,
          italic=current_theme_style.italic,
          dim=current_theme_style.dim,
          underline=current_theme_style.underline
        )
        black_bg_style = ThemeStyle(
          fg=color_code,
          bg=black_bg,
          bold=current_theme_style.bold,
          italic=current_theme_style.italic,
          dim=current_theme_style.dim,
          underline=current_theme_style.underline
        )

        # Apply styles (first name is unstyled, only white/black background versions are styled)
        colored_name_white = self.formatter.apply_style(name, white_bg_style)
        colored_name_black = self.formatter.apply_style(name, black_bg_style)

        # First name display is just plain text with standard padding
        padding = 20 - len(name)
        padded_name = name + ' ' * padding

        # Show modification indicator
        modifier_indicator = " [CUSTOM]" if is_modified else ""

        print(f"  {padded_name} = rgb({r:3}, {g:3}, {b:3})  # {hex_code}{modifier_indicator}")
        
        # Show original color if modified
        if is_modified:
          # Get the original color (before override)
          base_theme = create_default_theme_colorful() if self.use_colorful_theme else create_default_theme()
          if self.adjust_percent != 0.0:
            try:
              adjusted_base = base_theme.create_adjusted_copy(
                adjust_percent=self.adjust_percent,
                adjust_strategy=self.adjust_strategy
              )
            except ValueError:
              adjusted_base = base_theme
          else:
            adjusted_base = base_theme
          
          original_style = getattr(adjusted_base, name)
          if original_style.fg and isinstance(original_style.fg, RGB):
            orig_r, orig_g, orig_b = original_style.fg.to_ints()
            orig_hex = original_style.fg.to_hex()
            print(f"    Original: rgb({orig_r:3}, {orig_g:3}, {orig_b:3})  # {orig_hex}")
        
        # Calculate proper alignment accounting for ANSI escape codes
        # Find the longest component name for consistent alignment
        max_component_name_length = max(len(comp_name) for comp_name, _ in self.theme_components)
        target_white_section_width = len("    On white: ") + max_component_name_length + 2
        
        # Calculate current visual width (just the component name, not the ANSI codes)
        current_white_section_width = len("    On white: ") + len(name)
        padding_needed = target_white_section_width - current_white_section_width
        
        print(f"    On white: {colored_name_white}{' ' * padding_needed}On black: {colored_name_black}")
        print()

        # Build theme code line for this color
        # Handle background colors and text styles
        additional_styles = []
        if hasattr(theme, name):
          style_obj = getattr(theme, name)
          if style_obj.bg:
            if isinstance(style_obj.bg, RGB):
              bg_r, bg_g, bg_b = style_obj.bg.to_ints()
              bg_hex = style_obj.bg.to_hex()
              bg_hex_int = f"0x{bg_hex[1:]}"
              additional_styles.append(f"bg=RGB.from_rgb({bg_hex_int})")
          if style_obj.bold:
            additional_styles.append("bold=True")
          if style_obj.italic:
            additional_styles.append("italic=True")
          if style_obj.dim:
            additional_styles.append("dim=True")
          if style_obj.underline:
            additional_styles.append("underline=True")

        # Create ThemeStyle constructor call
        style_params = [f"fg=RGB.from_rgb({hex_int})"]
        style_params.extend(additional_styles)
        style_call = f"ThemeStyle({', '.join(style_params)})"

        theme_code_lines.append(f"    {name}={style_call},")

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

            # Create styled versions with different backgrounds (only for white/black versions)
            white_bg_style = ThemeStyle(fg=rgb, bg=white_bg)
            black_bg_style = ThemeStyle(fg=rgb, bg=black_bg)

            # Apply styles (first name is unstyled, only white/black background versions are styled)
            colored_name_white = self.formatter.apply_style(name, white_bg_style)
            colored_name_black = self.formatter.apply_style(name, black_bg_style)

            # First name display is just plain text with standard padding
            padding = 20 - len(name)
            padded_name = name + ' ' * padding

            print(f"  {padded_name} = rgb({r:3}, {g:3}, {b:3})  # {color_code}")
            
            # Calculate proper alignment accounting for ANSI escape codes
            max_component_name_length = max(len(comp_name) for comp_name, _ in self.theme_components)
            target_white_section_width = len("    On white: ") + max_component_name_length + 2
            
            current_white_section_width = len("    On white: ") + len(name)
            padding_needed = target_white_section_width - current_white_section_width
            
            print(f"    On white: {colored_name_white}{' ' * padding_needed}On black: {colored_name_black}")
            print()

            # Build theme code line
            hex_int_str = f"0x{hex_clean}"
            theme_code_lines.append(f"    {name}=ThemeStyle(fg=RGB.from_rgb({hex_int_str})),")
          else:
            print(f"  {name:20} = {color_code}")
        except ValueError:
          print(f"  {name:20} = {color_code}")
      elif color_code:
        print(f"  {name:20} = {color_code}")
      else:
        # No color defined
        print(f"  {name:20} = (no color)")

    # Display the complete theme creation code
    print("\n" + "=" * min(self.console_width, 60))
    print("📋 THEME CREATION CODE")
    print("=" * min(self.console_width, 60))
    print()
    print("from auto_cli.theme import RGB, ThemeStyle, Theme")
    print()
    print("def create_custom_theme() -> Theme:")
    print("  \"\"\"Create a custom theme with the current colors.\"\"\"")
    print("  return Theme(")

    for line in theme_code_lines:
      print(line)

    print("  )")
    print()
    print("# Usage in your CLI:")
    print("from auto_cli.cli import CLI")
    print("cli = CLI(your_module, theme=create_custom_theme())")
    print("cli.display()")

    print("=" * min(self.console_width, 60))

  def edit_individual_color(self):
    """Interactive color editing for individual theme components."""
    while True:
      print("\n" + "=" * min(self.console_width, 60))
      print("🎨 EDIT INDIVIDUAL COLOR")
      print("=" * min(self.console_width, 60))
      
      # Display components with modification indicators
      for i, (component_name, description) in enumerate(self.theme_components, 1):
        is_modified = component_name in self.individual_color_overrides
        status = " [MODIFIED]" if is_modified else ""
        print(f"  {i:2d}. {component_name:<25} {status}")
        print(f"      {description}")
        
        # Show current color
        current_theme = self.get_current_theme()
        current_style = getattr(current_theme, component_name)
        if current_style.fg and isinstance(current_style.fg, RGB):
          hex_color = current_style.fg.to_hex()
          r, g, b = current_style.fg.to_ints()
          colored_preview = self.formatter.apply_style("██", ThemeStyle(fg=current_style.fg))
          print(f"      Current: {colored_preview} rgb({r:3}, {g:3}, {b:3}) {hex_color}")
        print()

      print("Commands:")
      print("  Enter number (1-12) to edit component")
      print("  [x] Reset all individual colors")
      print("  [q] Return to main menu")

      try:
        choice = input("\nChoice: ").lower().strip()
        
        if choice == 'q':
          break
        elif choice == 'x':
          self._reset_all_individual_colors()
          print("All individual color overrides reset!")
          continue
        
        # Try to parse as component number
        try:
          component_index = int(choice) - 1
          if 0 <= component_index < len(self.theme_components):
            component_name, description = self.theme_components[component_index]
            self._edit_component_color(component_name, description)
          else:
            print(f"Invalid choice. Please enter 1-{len(self.theme_components)}")
        except ValueError:
          print("Invalid input. Please enter a number or command.")
          
      except (KeyboardInterrupt, EOFError):
        break

  def _edit_component_color(self, component_name: str, description: str):
    """Edit color for a specific component."""
    # Get current color
    current_theme = self.get_current_theme()
    current_style = getattr(current_theme, component_name)
    current_color = current_style.fg if current_style.fg else RGB.from_rgb(0x808080)
    
    is_modified = component_name in self.individual_color_overrides
    
    print(f"\n🎨 EDITING: {component_name}")
    print(f"Description: {description}")
    
    if isinstance(current_color, RGB):
      hex_color = current_color.to_hex()
      r, g, b = current_color.to_ints()
      colored_preview = self.formatter.apply_style("██████", ThemeStyle(fg=current_color))
      print(f"Current: {colored_preview} rgb({r:3}, {g:3}, {b:3}) {hex_color}")
    
    if is_modified:
      print("(This color has been customized)")

    print("\nInput Methods:")
    print("  [h] Hex color entry (e.g., FF8080)")
    print("  [r] Reset to original color")
    print("  [q] Cancel")

    try:
      method = input("\nChoose input method: ").lower().strip()
      
      if method == 'q':
        return
      elif method == 'r':
        self._reset_component_color(component_name)
        print(f"Reset {component_name} to original color!")
        return
      elif method == 'h':
        self._hex_color_input(component_name, current_color)
      else:
        print("Invalid choice.")
        
    except (KeyboardInterrupt, EOFError):
      return

  def _hex_color_input(self, component_name: str, current_color: RGB):
    """Handle hex color input for a component."""
    print(f"\nCurrent color: {current_color.to_hex()}")
    print("Enter new hex color (without #):")
    print("Examples: FF8080, ff8080, F80 (short form)")
    
    try:
      hex_input = input("Hex color: ").strip()
      
      if not hex_input:
        print("No input provided, canceling.")
        return
        
      # Normalize hex input
      hex_clean = hex_input.upper().lstrip('#')
      
      # Handle 3-character hex (e.g., F80 -> FF8800)
      if len(hex_clean) == 3:
        hex_clean = ''.join(c * 2 for c in hex_clean)
      
      # Validate hex
      if len(hex_clean) != 6 or not all(c in '0123456789ABCDEF' for c in hex_clean):
        print("Invalid hex color format. Please use 6 digits (e.g., FF8080)")
        return
      
      # Convert to RGB
      hex_int = int(hex_clean, 16)
      new_color = RGB.from_rgb(hex_int)
      
      # Preview the new color
      r, g, b = new_color.to_ints()
      colored_preview = self.formatter.apply_style("██████", ThemeStyle(fg=new_color))
      print(f"\nPreview: {colored_preview} rgb({r:3}, {g:3}, {b:3}) #{hex_clean}")
      
      # Confirm
      confirm = input("Apply this color? [y/N]: ").lower().strip()
      if confirm in ('y', 'yes'):
        self.individual_color_overrides[component_name] = new_color
        self.modified_components.add(component_name)
        print(f"✅ Applied new color to {component_name}!")
      else:
        print("Color change canceled.")
        
    except (KeyboardInterrupt, EOFError):
      print("\nColor editing canceled.")
    except ValueError as e:
      print(f"Error: {e}")

  def _reset_component_color(self, component_name: str):
    """Reset a component's color to original."""
    if component_name in self.individual_color_overrides:
      del self.individual_color_overrides[component_name]
      self.modified_components.discard(component_name)

  def _reset_all_individual_colors(self):
    """Reset all individual color overrides."""
    self.individual_color_overrides.clear()
    self.modified_components.clear()

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
      print("  [e] Edit individual colors")
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
        elif choice == 'e':
          self.edit_individual_color()
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
