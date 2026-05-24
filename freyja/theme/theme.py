"""Theme: hierarchical color configuration for Freyja help output."""

from __future__ import annotations

from dataclasses import dataclass

from .rgb import RGB
from .theme_style import CommandStyleSection, ThemeStyle


@dataclass
class Theme:
  """Hierarchical color theme for Freyja CLI help output.

  Each command level has its own ``CommandStyleSection`` (name + description + option
  styles). Non-sectioned roles cover the page title, section subtitles, the required
  asterisk badge, and command-output styling.
  """

  top_level_command_section: CommandStyleSection
  command_group_section: CommandStyleSection
  grouped_command_section: CommandStyleSection
  title: ThemeStyle
  subtitle: ThemeStyle
  required_asterisk: ThemeStyle
  command_output: ThemeStyle


def _section(
  name: ThemeStyle, desc: ThemeStyle, opt: ThemeStyle, opt_desc: ThemeStyle
) -> CommandStyleSection:
  """Build a ``CommandStyleSection`` from its four constituent styles."""
  return CommandStyleSection(
    command_name=name,
    command_description=desc,
    option_name=opt,
    option_description=opt_desc,
  )


def create_sunset_theme() -> Theme:
  """Create the default 'Sunset' theme.

  Palette: deep orange command groups, magenta group options, amber sub-commands,
  violet sub-command options, bold red required asterisk. Tuned for legibility on
  both light and dark terminal backgrounds.
  """
  # Command groups (e.g. "build:") and command-group options (e.g. "--parallel")
  group_name = ThemeStyle(fg=RGB.from_rgb(0xCB4B16), bold=True)  # deep orange
  group_opt = ThemeStyle(fg=RGB.from_rgb(0xD33682))  # magenta
  desc_neutral = ThemeStyle()  # use terminal default fg for descriptions

  # Sub-commands (e.g. "autotag:") and sub-command options (e.g. "--message MESSAGE")
  sub_name = ThemeStyle(fg=RGB.from_rgb(0xB58900), bold=True)  # amber
  sub_opt = ThemeStyle(fg=RGB.from_rgb(0x6C71C4))  # violet

  return Theme(
    top_level_command_section=_section(group_name, desc_neutral, group_opt, desc_neutral),
    command_group_section=_section(group_name, desc_neutral, group_opt, desc_neutral),
    grouped_command_section=_section(sub_name, desc_neutral, sub_opt, desc_neutral),
    title=ThemeStyle(fg=RGB.from_rgb(0xCB4B16), bold=True),
    subtitle=ThemeStyle(bold=True),
    required_asterisk=ThemeStyle(fg=RGB.from_rgb(0xDC322F), bold=True),
    command_output=ThemeStyle(fg=RGB.from_rgb(0xCB4B16), bold=True),
  )


def create_no_color_theme() -> Theme:
  """Create a theme with no COLORS or attributes (used when COLORS are disabled)."""
  plain = ThemeStyle()
  empty_section = _section(plain, plain, plain, plain)
  return Theme(
    top_level_command_section=empty_section,
    command_group_section=empty_section,
    grouped_command_section=empty_section,
    title=plain,
    subtitle=plain,
    required_asterisk=plain,
    command_output=plain,
  )
