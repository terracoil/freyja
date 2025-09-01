# Command discovery functionality extracted from FreyjaCLI class.
import inspect
import types
from typing import *

from freyja.cli.system import System
from freyja.utils import TextUtil
from . import CommandInfo
from .cli_types import Target
from .enums import TargetMode
from .validation import ValidationService

# @dataclass
# class CommandMetadata:
#   src_class: type
#   class_namespace: str
#   is_namespaced: bool

class CommandDiscovery:
  """
  Discovers commands from modules or classes using introspection.

  Handles both flat command structures (direct functions/methods) and
  hierarchical structures (inner classes with methods).
  """

  def __init__(
      self,
      target: Target,
      function_filter: Optional[Callable[[types.ModuleType, str, Any], bool]] = None,
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


    self.command_tree = self.discover_commands()

  def discover_commands(self) -> List[CommandInfo]:
    """
    Discover all commands from the target.

    :return: List of discovered commands
    """
    commands:List[CommandInfo] = []

    if self.target_mode == TargetMode.MODULE:
      commands = self._discover_from_module()
    elif self.target_mode == TargetMode.CLASS:
      commands = self._discover_from_classes()


    print(TextUtil.format_pretty("Commands: {commands}", commands=commands))
    return commands

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

  def _discover_from_class(self, target_cls: type, namespaced: bool) -> List[CommandInfo]:
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

    return commands # [self._set_cmd_metadata(src_cls, cmd, namespaced) for cmd in commands]

  def _discover_from_classes(self) -> List[CommandInfo]:
    """Discover methods from classes (single or multiple) with proper namespacing.

    For single class: methods get no namespace prefix (global namespace).
    For multiple classes: last class gets global namespace, others get kebab-cased class name prefixes.
    """
    commands = []

    if self.target_classes:

      if self.completion or self.theme_tuner:
        self.target_classes.insert(0, System) # SystemClassBuilder.build(self.completion, self.theme_tuner))

      # Separate last class (global) from others (namespaced)
      # namespaced_classes = self.target_classes[:-1] if len(self.target_classes) > 1 else []
      global_class = self.target_classes[-1]


      # Process namespaced classes first (with class name prefixes)
      for target_cls in self.target_classes:
        # Discover commands for this class

        class_commands = self._discover_from_class(
          target_cls,
          namespaced=(target_cls.__name__ != global_class.__name__)
        )

        commands.extend(class_commands)

    return commands

  @classmethod
  def _discover_inner_classes(cls, target_cls: type) -> Dict[str, Type]:
    """Discover inner classes that should be treated as command groups."""
    inner_classes = {}

    print(f"\nLooking for inner classes on {target_cls.__name__}")
    for name, obj in inspect.getmembers(target_cls):
      if inspect.isclass(obj) and not name.startswith('_'):
          #an # obj.__qualname__.endswith(f'{src_cls.__name__}.{name}')):
        print(f"Found inner class: {name}, {obj}")
        inner_classes[name] = obj

    return inner_classes

  def _discover_direct_methods(self, src_cls: type) -> List[CommandInfo]:
    """Discover methods directly from the target class."""
    commands = []

    for name, obj in inspect.getmembers(src_cls):
      if self.method_filter(src_cls, name, obj):
        command_info = CommandInfo(
          name=TextUtil.kebab_case(name),
          original_name=name,
          function=obj,
          signature=inspect.signature(obj),
          docstring=inspect.getdoc(obj),
          src_class= src_cls,
        )
        commands.append(command_info)

    return commands

  @classmethod
  def _discover_methods_from_inner_classes(cls, parent_class: type, inner_classes: Dict[str, Type]) -> List[CommandInfo]:
    """Discover methods from inner classes for hierarchical commands."""
    commands = []

    for class_name, inner_class in inner_classes.items():
      command_name = TextUtil.kebab_case(class_name)
      print(f"_discover_methods_from_inner_classes: {command_name}")

      for method_name, method_obj in inspect.getmembers(inner_class):
        if (not method_name.startswith('_') and
            callable(method_obj) and
            method_name != '__init__' and
            inspect.isfunction(method_obj)):
          # Use kebab-cased method name as command name:
          method_kebab = TextUtil.kebab_case(method_name)

          commands.append(CommandInfo(
            name=method_kebab,  # Just the method name, not group__method
            original_name=method_name,
            function=method_obj,
            signature=inspect.signature(method_obj),
            docstring=inspect.getdoc(method_obj),
            is_hierarchical=True,
            parent_class=parent_class.__name__,
            command_path=command_name,
            inner_class=inner_class,
            group_name=parent_class.__name__,
            method_name=method_name
          ))

          # # Store metadata for execution
          # command_info.metadata.update({
          #   'inner_class': inner_class,
          #   'inner_class_name': class_name,
          #   'command_name': command_name,
          #   'method_name': method_name
          # })

    return commands

  @staticmethod
  def _default_function_filter(target_mod: types.ModuleType, name: str, obj: Any) -> bool:
    """Default filter for module functions."""
    return (
        target_mod and
        not name.startswith('_') and
        callable(obj) and
        not inspect.isclass(obj) and
        inspect.isfunction(obj) and
        obj.__module__ == target_mod.__name__  # Exclude imported functions
    )

  @staticmethod
  def _default_method_filter(target_cls: type, name: str, obj: Any) -> bool:
    """Default filter for class methods."""
    return (
        target_cls and
        (not name.startswith('_')) and
        (callable(obj)) and
        (inspect.isfunction(obj) or inspect.ismethod(obj)) and
        (hasattr(obj, '__qualname__')) and
        (target_cls.__name__ in obj.__qualname__)
    )

  @classmethod
  def set_namespace_info(cls, target_cls: type, cmd: CommandInfo, namespace: bool) -> CommandInfo:
    if not (target_cls and isinstance(target_cls, type)):
      raise ValueError("Target class must exist and be a class.")

    cls_namespace: str | None = TextUtil.kebab_case(target_cls.__name__) if namespace else None

    print(f"Namespace for {target_cls.__name__}: {cls_namespace}" )
    cmd.source = target_cls
    cmd.namespace = cls_name
    # cmd.metadata = CommandMetadata(
    #   src_class=src_cls,
    #   class_namespace=cls_namespace,
    #   is_namespaced=namespace,
    # )

    return cmd
