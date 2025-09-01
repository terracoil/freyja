# Command discovery functionality extracted from FreyjaCLI class.
import inspect
from collections.abc import Callable as CallableABC
from dataclasses import dataclass, field
from types import ModuleType
from typing import *

from freyja.cli.enums import TargetMode
from freyja.utils.text_util import TextUtil
from freyja.parser import DocStringParser
from .validation import ValidationService
from ..cli.system import SystemClassBuilder

TargetType = ModuleType | type | list[type]


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
      target: TargetType,
      function_filter: Optional[Callable[[str, Any], bool]] = None,
      method_filter: Optional[Callable[[type, str, Any], bool]] = None,
      completion: bool = True,
      theme_tuner: bool = False
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

    self.completion: bool = completion
    self.theme_tuner: bool = theme_tuner

    self.target_classes: Optional[list[type]] = None
    self.target_module: Optional[ModuleType] = None
    self.mode: TargetMode = TargetMode.CLASS
    self.primary_class: Optional[type] = None

    # Determine target mode with unified class handling
    if isinstance(target, list):
      self.target_classes = target
      self._validate_classes(self.target_classes)
      self.primary_class = self.target_classes[-1]
    elif inspect.isclass(target):
      self.primary_class = target
      self.target_classes = [target]
    elif inspect.ismodule(target):
      self.mode = TargetMode.MODULE
      self.target_module = target
    else:
      raise ValueError(f"Target must be module, class, or list of classes, got {type(target).__name__}")

    self.commands : List[CommandInfo] = self.discover_commands()

  def discover_commands(self) -> List[CommandInfo]:
    """
    Discover all commands from the target.

    :return: List of discovered commands
    """
    result = []

    if self.mode == TargetMode.MODULE:
      result = self._discover_from_module()
    elif self.mode == TargetMode.CLASS:
      # Unified class handling: always use multi-class logic for consistency
      result = self.discover_classes()

    # TextUtil.pprint("COMMANDS:::{result}", result=result)

    return result

  def _discover_from_module(self) -> List[CommandInfo]:
    """Discover functions from a module."""
    commands = []

    for name, obj in inspect.getmembers(self.target_module):
      if self.function_filter(name, obj):
        command_info = CommandInfo(
          name=TextUtil.kebab_case(name),
          original_name=name,
          function=obj,
          signature=inspect.signature(obj),
          docstring=inspect.getdoc(obj)
        )
        commands.append(command_info)

    return commands

  def _discover_from_class(self, target_cls: type) -> List[CommandInfo]:
    """Discover methods from a single class (used internally by multi-class logic)."""
    commands = []

    # Check for inner classes first (hierarchical pattern)
    inner_classes = self._discover_inner_classes(target_cls)

    if inner_classes:
      # Mixed pattern: direct methods + inner class methods
      ValidationService.validate_constructor_parameters(
        target_cls, "main class"
      )

      # Validate inner class constructors
      for class_name, inner_class in inner_classes.items():
        ValidationService.validate_inner_class_constructor_parameters(
          inner_class, f"inner class '{class_name}'"
        )

      # Discover direct methods
      direct_commands = self._discover_direct_methods(target_cls)
      commands.extend(direct_commands)

      # Discover inner class methods
      hierarchical_commands = self._discover_methods_from_inner_classes(target_cls, inner_classes)
      commands.extend(hierarchical_commands)

    else:
      # Direct methods only (flat pattern)
      ValidationService.validate_constructor_parameters(
        target_cls, "class", allow_parameterless_only=True
      )
      direct_commands = self._discover_direct_methods(target_cls)
      commands.extend(direct_commands)

    return commands

  @staticmethod
  def _validate_classes(targets: list[type]) -> None:
    if not targets:
      raise ValueError("Passed a list, but no target classes were found.")

    for item in targets:
      if not isinstance(item, type):
        raise ValueError(f"All items in list must be classes, got {type(item).__name__}")

  def discover_classes(self) -> List[CommandInfo]:
    """Discover methods from classes (single or multiple) with proper namespacing.
    
    For single class: methods get no namespace prefix (global namespace).
    For multiple classes: last class gets global namespace, others get kebab-cased class name prefixes.
    """
    commands = []

    if self.completion or self.theme_tuner:
      System = SystemClassBuilder.build(self.completion, self.theme_tuner)
      self.target_classes.insert(0, System)  # SystemClassBuilder.build(self.completion, self.theme_tuner))

    # Separate last class (global) from others (namespaced)
    namespaced_classes = self.target_classes[:-1] if len(self.target_classes) > 1 else []

    # Process namespaced classes first (with class name prefixes)
    for target_class in namespaced_classes:
      # Discover commands for this class
      class_commands = self._discover_from_class(target_class)

      # Add class namespace to command metadata (not name - that's handled by CommandBuilder)
      class_namespace = TextUtil.kebab_case(target_class.__name__)

      for command in class_commands:
        command.metadata['source_class'] = target_class
        command.metadata['class_namespace'] = class_namespace
        command.metadata['is_namespaced'] = True

      commands.extend(class_commands)

    # Discover commands for primary class
    primary_commands = self._discover_from_class(self.primary_class)

    for command in primary_commands:
      command.metadata['source_class'] = self.primary_class
      command.metadata['class_namespace'] = None
      command.metadata['is_namespaced'] = False

    commands.extend(primary_commands)

    # Restore original target
    # self.target_class = original_target_class

    return commands

  def _discover_inner_classes(self, target_class: Type) -> Dict[str, Type]:
    """Discover inner classes that should be treated as command groups."""
    inner_classes = {}

    for name, obj in inspect.getmembers(target_class):
      if (inspect.isclass(obj) and not name.startswith('_')):  # and obj.__qualname__.endswith(f'{target_class.__name__}.{name}')):
        inner_classes[name] = obj

    return inner_classes

  def _discover_direct_methods(self, target_class) -> List[CommandInfo]:
    """Discover methods directly from the target class."""
    commands = []

    for name, obj in inspect.getmembers(target_class):
      if self.method_filter(target_class, name, obj):
        command_info = CommandInfo(
          name=TextUtil.kebab_case(name),
          original_name=name,
          function=obj,
          signature=inspect.signature(obj),
          docstring=inspect.getdoc(obj)
        )
        commands.append(command_info)

    return commands

  def _discover_methods_from_inner_classes(self, target_cls: type, inner_classes: Dict[str, Type]) -> List[CommandInfo]:
    """Discover methods from inner classes for hierarchical commands."""
    commands = []

    for class_name, inner_class in inner_classes.items():
      command_name = TextUtil.kebab_case(class_name)

      for method_name, method_obj in inspect.getmembers(inner_class):
        if (not method_name.startswith('_') and
            callable(method_obj) and
            method_name != '__init__' and
            inspect.isfunction(method_obj)):
          # Use kebab-cased method name as command name (no dunder notation)
          method_kebab = TextUtil.kebab_case(method_name)
          group_name = command_name  # Use the kebab-cased inner class name

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
            is_system_command=self.is_system(target_cls),
            group_name=group_name,  # Kebab-cased inner class name
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

  def is_system(self, cls: type) -> bool:
    return cls.__name__ == 'System'

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

  def _default_method_filter(self, target_class:type, name: str, obj: Any) -> bool:
    """Default filter for class methods."""
    if target_class is None:
      return False

    return (
        not name.startswith('_') and
        callable(obj) and
        (inspect.isfunction(obj) or inspect.ismethod(obj)) and
        hasattr(obj, '__qualname__') and
        target_class.__name__ in obj.__qualname__
    )

  def generate_title(self) -> str:
    """
    Generate FreyjaCLI title based on target type.
    
    :return: Generated title string
    """
    result = "FreyjaCLI Application"

    if self.mode == TargetMode.MODULE:
      if hasattr(self.target_module, '__name__'):
        module_name = self.target_module.__name__.split('.')[-1]  # Get last part of module name
        result = f"{module_name.title()} FreyjaCLI"
    elif self.mode == TargetMode.CLASS:
      if self.primary_class and self.primary_class.__doc__:
        main_desc, _ = DocStringParser.parse_docstring(self.primary_class.__doc__)
        result = main_desc or self.primary_class.__name__
      elif self.primary_class:
        result = self.primary_class.__name__

    return result
