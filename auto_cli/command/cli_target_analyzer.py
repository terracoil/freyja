"""CLI target analysis service.

Provides services for analyzing and validating CLI targets (modules, classes, multi-class lists).
Extracted from CLI class to reduce its size and improve separation of concerns.
"""
import types
from typing import *

from ..enums import TargetInfoKeys, TargetMode
from .docstring_parser import parse_docstring

Target = Union[types.ModuleType, Type[Any], Sequence[Type[Any]]]


class CliTargetAnalyzer:
  """Analyzes CLI targets and provides metadata for CLI construction."""

  @staticmethod
  def analyze_target(target: Target) -> tuple[TargetMode, Dict[str, Any]]:
    """
    Analyze target and return mode with metadata.
    
    :param target: Module, class, or list of classes to analyze
    :return: Tuple of (target_mode, target_info_dict)
    :raises ValueError: If target is invalid
    """
    mode = None
    info = {}

    if isinstance(target, list):
      if not target:
        raise ValueError("Class list cannot be empty")

      # Validate all items are classes
      for item in target:
        if not isinstance(item, type):
          raise ValueError(f"All items in list must be classes, got {type(item).__name__}")

      if len(target) == 1:
        mode = TargetMode.CLASS
        info = {TargetInfoKeys.PRIMARY_CLASS.value: target[0], TargetInfoKeys.ALL_CLASSES.value: target}
      else:
        mode = TargetMode.MULTI_CLASS
        info = {TargetInfoKeys.PRIMARY_CLASS.value: target[-1], TargetInfoKeys.ALL_CLASSES.value: target}

    elif isinstance(target, type):
      mode = TargetMode.CLASS
      info = {TargetInfoKeys.PRIMARY_CLASS.value: target, TargetInfoKeys.ALL_CLASSES.value: [target]}

    elif hasattr(target, '__file__'):  # Module check
      mode = TargetMode.MODULE
      info = {TargetInfoKeys.MODULE.value: target}

    else:
      raise ValueError(f"Target must be module, class, or list of classes, got {type(target).__name__}")

    return mode, info

  @staticmethod
  def generate_title(target: Target) -> str:
    """
    Generate CLI title based on target type.
    
    :param target: CLI target to generate title from
    :return: Generated title string
    """
    result = "CLI Application"

    # Analyze target to determine mode and info
    target_mode, target_info = CliTargetAnalyzer.analyze_target(target)

    if target_mode == TargetMode.MODULE:
      if hasattr(target, '__name__'):
        module_name = target.__name__.split('.')[-1]  # Get last part of module name
        result = f"{module_name.title()} CLI"
    elif target_mode in [TargetMode.CLASS, TargetMode.MULTI_CLASS]:
      primary_class = target_info[TargetInfoKeys.PRIMARY_CLASS.value]
      if primary_class.__doc__:
        main_desc, _ = parse_docstring(primary_class.__doc__)
        result = main_desc or primary_class.__name__
      else:
        result = primary_class.__name__

    return result