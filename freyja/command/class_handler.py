import inspect
from typing import Any

"""Multi-class FreyjaCLI command handling and collision detection.

Provides services for managing cmd_tree from multiple classes in a single FreyjaCLI,
including collision detection, command ordering, and source tracking.
"""


class ClassHandler:
  """Handles cmd_tree from multiple classes with collision detection and ordering."""

  def __init__(self):
    """Initialize multi-class handler."""
    self.command_sources: dict[str, type] = {}  # command_name -> source_class
    self.class_commands: dict[type, list[str]] = {}  # source_class -> [command_names]
    self.collision_tracker: dict[str, list[type]] = {}  # command_name -> [source_classes]

  def track_command(self, command_name: str, source_class: type) -> None:
    """Track a command and its source class for collision detection."""
    # Guard: Ensure command_name is not empty
    if not command_name or (isinstance(command_name, str) and not command_name.strip()):
      raise ValueError("command_name cannot be empty")
    
    # Guard: Ensure source_class is not None
    if source_class is None:
      raise ValueError("source_class cannot be None")
    # Track collision if command already exists
    if command_name in self.command_sources:
      if command_name not in self.collision_tracker:
        self.collision_tracker[command_name] = [self.command_sources[command_name]]
      self.collision_tracker[command_name].append(source_class)
    else:
      self.command_sources[command_name] = source_class

    # Track commands per class for ordering
    self.class_commands.setdefault(source_class, []).append(command_name)

  def detect_collisions(self) -> list[tuple[str, list[type]]]:
    """Detect and return command name collisions."""
    return list(self.collision_tracker.items())

  def has_collisions(self) -> bool:
    """Check if any command name collisions exist."""
    return len(self.collision_tracker) > 0

  def get_ordered_commands(self, class_order: list[type]) -> list[str]:
    """Get commands ordered by class sequence, then alphabetically within each class."""
    return [
      cmd
      for cls in class_order
      if cls in self.class_commands
      for cmd in sorted(self.class_commands[cls])
    ]

  def get_command_source(self, command_name: str) -> type | None:
    """Get the source class for a command."""
    return self.command_sources.get(command_name)

  def format_collision_error(self) -> str:
    """Format collision error message for user display."""
    if not self.has_collisions():
      return ""

    error_lines = [
      "Command name collisions detected:",
      *[
        f"  '{cmd}' conflicts between: {', '.join(cls.__name__ for cls in classes)}"
        for cmd, classes in self.collision_tracker.items()
      ],
      "",
      "Solutions:",
      "1. Rename methods in one of the conflicting classes",
      "2. Use different inner class names to create unique command paths",
      "3. Use separate FreyjaCLI instances for conflicting classes"
    ]
    return "\n".join(error_lines)

  def validate_classes(self, classes: list[type]) -> None:
    """Validate that classes can be used together without collisions."""
    temp_handler = ClassHandler()
    for cls in classes:
      self._simulate_class_commands(temp_handler, cls)

    if temp_handler.has_collisions():
      raise ValueError(temp_handler.format_collision_error())

  def _simulate_class_commands(self, handler: "ClassHandler", cls: type) -> None:
    """Simulate command discovery for collision detection."""
    from freyja.utils.text_util import TextUtil

    inner_classes = self._discover_inner_classes(cls)

    if inner_classes:
      # Track direct methods
      for name, obj in inspect.getmembers(cls):
        if self._is_valid_method(name, obj, cls):
          handler.track_command(TextUtil.kebab_case(name), cls)

      # Track inner class methods
      for class_name, inner_class in inner_classes.items():
        command_name = TextUtil.kebab_case(class_name)
        for method_name, method_obj in inspect.getmembers(inner_class):
          if (not method_name.startswith("_") and callable(method_obj) and
              method_name != "__init__" and inspect.isfunction(method_obj)):
            cli_name = f"{command_name}--{TextUtil.kebab_case(method_name)}"
            handler.track_command(cli_name, cls)
    else:
      # Direct methods only
      for name, obj in inspect.getmembers(cls):
        if self._is_valid_method(name, obj, cls):
          handler.track_command(TextUtil.kebab_case(name), cls)

  def _discover_inner_classes(self, cls: type) -> dict[str, type]:
    """Discover inner classes for a given class."""
    return {
      name: obj
      for name, obj in inspect.getmembers(cls)
      if (inspect.isclass(obj) and not name.startswith("_") and
          obj.__qualname__.endswith(f"{cls.__name__}.{name}"))
    }

  def _is_valid_method(self, name: str, obj: Any, cls: type) -> bool:
    """Check if a method should be included as a CLI command."""
    return (not name.startswith("_") and callable(obj) and
            (inspect.isfunction(obj) or inspect.ismethod(obj)) and
            hasattr(obj, "__qualname__") and cls.__name__ in obj.__qualname__)
