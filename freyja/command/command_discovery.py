# Command discovery functionality extracted from FreyjaCLI class.
import inspect
import types
from collections.abc import Callable as CallableABC
from dataclasses import dataclass, field
from typing import *

from freyja.cli.enums import TargetMode
from freyja.utils.string_utils import StringUtils
from .validation import ValidationService


@dataclass
class CommandInfo:
  """Information about a discovered command."""
  name: str
  original_name: str
  function: CallableABC
  signature: inspect.Signature
  docstring: Optional[str] = None
  is_hierarchical: bool = False
  parent_class: Optional[str] = None
  command_path: Optional[str] = None
  is_system_command: bool = False
  inner_class: Optional[Type] = None
  metadata: Dict[str, Any] = field(default_factory=dict)
  # New fields for nested command structure
  group_name: Optional[str] = None  # For hierarchical commands (kebab-cased inner class name)
  method_name: Optional[str] = None  # For hierarchical commands (kebab-cased method name)


class CommandDiscovery:
  """
  Discovers commands from modules or classes using introspection.

  Handles both flat command structures (direct functions/methods) and
  hierarchical structures (inner classes with methods).
  """

  def __init__(
      self,
      target: Union[types.ModuleType, Type[Any], List[Type[Any]]],
      function_filter: Optional[Callable[[str, Any], bool]] = None,
      method_filter: Optional[Callable[[str, Any], bool]] = None
  ):
    """
    Initialize command discovery.

    :param target: Module, class, or list of classes to discover from
    :param function_filter: Optional filter for module functions
    :param method_filter: Optional filter for class methods
    """
    self.target = target
    self.function_filter = function_filter or self._default_function_filter
    self.method_filter = method_filter or self._default_method_filter

    # Determine target mode with unified class handling
    if isinstance(target, list):
      self.target_mode = TargetMode.CLASS
      self.target_classes = target
      self.target_class = None
      self.target_module = None
    elif inspect.isclass(target):
      # Treat single class as list with one item for unified handling
      self.target_mode = TargetMode.CLASS
      self.target_class = None
      self.target_classes = [target]
      self.target_module = None
    elif inspect.ismodule(target):
      self.target_mode = TargetMode.MODULE
      self.target_module = target
      self.target_class = None
      self.target_classes = None
    else:
      raise ValueError(f"Target must be module, class, or list of classes, got {type(target).__name__}")

  def discover_commands(self) -> List[CommandInfo]:
    """
    Discover all commands from the target.

    :return: List of discovered commands
    """
    result = []

    if self.target_mode == TargetMode.MODULE:
      result = self._discover_from_module()
    elif self.target_mode == TargetMode.CLASS:
      # Unified class handling: always use multi-class logic for consistency
      result = self._discover_from_multi_class()

    return result

  def _discover_from_module(self) -> List[CommandInfo]:
    """Discover functions from a module."""
    commands = []

    for name, obj in inspect.getmembers(self.target_module):
      if self.function_filter(name, obj):
        command_info = CommandInfo(
          name=StringUtils.kebab_case(name),
          original_name=name,
          function=obj,
          signature=inspect.signature(obj),
          docstring=inspect.getdoc(obj)
        )
        commands.append(command_info)

    return commands

  def _discover_from_class(self) -> List[CommandInfo]:
    """Discover methods from a single class (used internally by multi-class logic)."""
    commands = []

    # Check for inner classes first (hierarchical pattern)
    inner_classes = self._discover_inner_classes(self.target_class)

    if inner_classes:
      # Mixed pattern: direct methods + inner class methods
      ValidationService.validate_constructor_parameters(
        self.target_class, "main class"
      )

      # Validate inner class constructors
      for class_name, inner_class in inner_classes.items():
        ValidationService.validate_inner_class_constructor_parameters(
          inner_class, f"inner class '{class_name}'"
        )

      # Discover direct methods
      direct_commands = self._discover_direct_methods()
      commands.extend(direct_commands)

      # Discover inner class methods
      hierarchical_commands = self._discover_methods_from_inner_classes(inner_classes)
      commands.extend(hierarchical_commands)

    else:
      # Direct methods only (flat pattern)
      ValidationService.validate_constructor_parameters(
        self.target_class, "class", allow_parameterless_only=True
      )
      direct_commands = self._discover_direct_methods()
      commands.extend(direct_commands)

    return commands

  def _discover_from_multi_class(self) -> List[CommandInfo]:
    """Discover methods from classes (single or multiple) with proper namespacing.
    
    For single class: methods get no namespace prefix (global namespace).
    For multiple classes: last class gets global namespace, others get kebab-cased class name prefixes.
    """
    commands = []
    
    if not self.target_classes:
      return commands

    # Separate last class (global) from others (namespaced)
    namespaced_classes = self.target_classes[:-1] if len(self.target_classes) > 1 else []
    global_class = self.target_classes[-1]

    # Process namespaced classes first (with class name prefixes)
    for target_class in namespaced_classes:
      # Temporarily switch to single class mode
      original_target_class = self.target_class
      self.target_class = target_class

      # Discover commands for this class
      class_commands = self._discover_from_class()

      # Add class namespace to command metadata (not name - that's handled by CommandBuilder)
      class_namespace = StringUtils.kebab_case(target_class.__name__)

      for command in class_commands:
        command.metadata['source_class'] = target_class
        command.metadata['class_namespace'] = class_namespace
        command.metadata['is_namespaced'] = True

      commands.extend(class_commands)

      # Restore original target
      self.target_class = original_target_class

    # Process global class last (no namespace prefix)
    original_target_class = self.target_class
    self.target_class = global_class

    # Discover commands for global class
    global_commands = self._discover_from_class()

    for command in global_commands:
      command.metadata['source_class'] = global_class
      command.metadata['class_namespace'] = None
      command.metadata['is_namespaced'] = False

    commands.extend(global_commands)

    # Restore original target
    self.target_class = original_target_class

    return commands

  def _discover_inner_classes(self, target_class: Type) -> Dict[str, Type]:
    """Discover inner classes that should be treated as command groups."""
    inner_classes = {}

    for name, obj in inspect.getmembers(target_class):
      if (inspect.isclass(obj) and
          not name.startswith('_') and
          obj.__qualname__.endswith(f'{target_class.__name__}.{name}')):
        inner_classes[name] = obj

    return inner_classes

  def _discover_direct_methods(self) -> List[CommandInfo]:
    """Discover methods directly from the target class."""
    commands = []

    for name, obj in inspect.getmembers(self.target_class):
      if self.method_filter(name, obj):
        command_info = CommandInfo(
          name=StringUtils.kebab_case(name),
          original_name=name,
          function=obj,
          signature=inspect.signature(obj),
          docstring=inspect.getdoc(obj)
        )
        commands.append(command_info)

    return commands

  def _discover_methods_from_inner_classes(self, inner_classes: Dict[str, Type]) -> List[CommandInfo]:
    """Discover methods from inner classes for hierarchical commands."""
    commands = []

    for class_name, inner_class in inner_classes.items():
      command_name = StringUtils.kebab_case(class_name)

      for method_name, method_obj in inspect.getmembers(inner_class):
        if (not method_name.startswith('_') and
            callable(method_obj) and
            method_name != '__init__' and
            inspect.isfunction(method_obj)):
          # Use kebab-cased method name as command name (no dunder notation)
          method_kebab = StringUtils.kebab_case(method_name)

          command_info = CommandInfo(
            name=method_kebab,  # Just the method name, not group__method
            original_name=method_name,
            function=method_obj,
            signature=inspect.signature(method_obj),
            docstring=inspect.getdoc(method_obj),
            is_hierarchical=True,
            parent_class=class_name,
            command_path=command_name,
            inner_class=inner_class,
            group_name=command_name,  # Kebab-cased inner class name
            method_name=method_kebab  # Kebab-cased method name
          )

          # Store metadata for execution
          command_info.metadata.update({
            'inner_class': inner_class,
            'inner_class_name': class_name,
            'command_name': command_name,
            'method_name': method_name
          })

          commands.append(command_info)

    return commands

  def _default_function_filter(self, name: str, obj: Any) -> bool:
    """Default filter for module functions."""
    if self.target_module is None:
      return False

    return (
        not name.startswith('_') and
        callable(obj) and
        not inspect.isclass(obj) and
        inspect.isfunction(obj) and
        obj.__module__ == self.target_module.__name__  # Exclude imported functions
    )

  def _default_method_filter(self, name: str, obj: Any) -> bool:
    """Default filter for class methods."""
    if self.target_class is None:
      return False

    return (
        not name.startswith('_') and
        callable(obj) and
        (inspect.isfunction(obj) or inspect.ismethod(obj)) and
        hasattr(obj, '__qualname__') and
        self.target_class.__name__ in obj.__qualname__
    )
