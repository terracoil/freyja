"""FreyjaCLI self.target analysis service.

Provides services for analyzing and validating FreyjaCLI targets (modules, classes, multi-class lists).
Extracted from FreyjaCLI class to reduce its size and improve separation of concerns.
"""
import types
from typing import *

from . import SystemClassBuilder
from .enums import TargetInfoKeys, TargetMode
from freyja.parser import DocStringParser

Target = Union[types.ModuleType, Type[Any], Sequence[Type[Any]]]


class TargetAnalyzer:
  """Analyzes FreyjaCLI targets and provides metadata for FreyjaCLI construction."""

  def __init__(self, target: Target, completion:bool, theme_tuner:bool):
    if not target:
        raise ValueError("Target cannot be None or empty list")

    self.target:Target = target
    self.completion:bool = completion
    self.theme_tuner:bool = theme_tuner

  def analyze_target(self) -> tuple[TargetMode, Dict[str, Any]]:
    """
    Analyze target and return mode with metadata.
    
    :return: Tuple of (target_mode, target_info_dict)
    """

    targets:Optional[list[type]] = None

    # Ensure class-based targets are list of targets:
    if isinstance(self.target, type):
      targets = [self.target]
    elif isinstance(self.target, list):
      targets = self.target

    if targets:
      # Validate all items are classes
      for item in targets:
        if not isinstance(item, type):
          raise ValueError(f"All items in list must be classes, got {type(item).__name__}")

      mode = TargetMode.CLASS

      if self.completion or self.theme_tuner:
        System = SystemClassBuilder.build(self.completion, self.theme_tuner)
        targets.insert(0, System)

      # Primary class is the last one (gets global namespace), others get prefixed
      info = {TargetInfoKeys.PRIMARY_CLASS.value: targets[-1], TargetInfoKeys.ALL_CLASSES.value: targets}

    elif hasattr(self.target, '__file__'):  # Module check
      mode = TargetMode.MODULE
      info = {TargetInfoKeys.MODULE.value: self.target}

    else:
      raise ValueError(f"Target must be module, class, or list of classes, got {type(self.target).__name__}")

    return mode, info

  def generate_title(self) -> str:
    """
    Generate FreyjaCLI title based on self.target type.
    
    :param self.target: FreyjaCLI self.target to generate title from
    :return: Generated title string
    """
    result = "FreyjaCLI Application"

    # Analyze self.target to determine mode and info
    target_mode, target_info = self.analyze_target()

    if target_mode == TargetMode.MODULE:
      if hasattr(self.target, '__name__'):
        module_name = self.target.__name__.split('.')[-1]  # Get last part of module name
        result = f"{module_name.title()} FreyjaCLI"
    elif target_mode == TargetMode.CLASS:
      primary_class = target_info[TargetInfoKeys.PRIMARY_CLASS.value]
      if primary_class.__doc__:
        main_desc, _ = DocStringParser.parse_docstring(primary_class.__doc__)
        result = main_desc or primary_class.__name__
      else:
        result = primary_class.__name__

    return result
