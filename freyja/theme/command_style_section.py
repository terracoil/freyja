"""Hierarchical command styling configuration for a specific command level."""

from __future__ import annotations

from dataclasses import dataclass

from .theme_style import ThemeStyle


@dataclass
class CommandStyleSection:
  """
  Hierarchical command styling configuration for a specific command level.
  Groups related styling attributes for cmd_tree and their options.
  """

  command_name: ThemeStyle  # Style for command names at this level
  command_description: ThemeStyle  # Style for command descriptions at this level
  option_name: ThemeStyle  # Style for option names at this level
  option_description: ThemeStyle  # Style for option descriptions at this level