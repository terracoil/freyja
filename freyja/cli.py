# Refactored CLI class - Simplified coordinator role only
from __future__ import annotations

import types
from typing import *

from .command.cli_execution_coordinator import CliExecutionCoordinator
from .command.cli_target_analyzer import CliTargetAnalyzer
from .command.command_builder import CommandBuilder
from .command.command_discovery import CommandDiscovery
from .command.command_executor import CommandExecutor
from .command.command_parser import CommandParser
from .command.multi_class_handler import MultiClassHandler
from .completion.base import get_completion_handler
from .enums.target_info_keys import TargetInfoKeys

Target = Union[types.ModuleType, Type[Any], Sequence[Type[Any]]]

# Re-export for backward compatibility
__all__ = ['CLI']


class CLI:
  """
  Simplified CLI coordinator that orchestrates command discovery, parsing, and execution.
  """

  def __init__(self, target: Target, title: Optional[str] = None, function_filter: Optional[callable] = None,
               method_filter: Optional[callable] = None, theme=None, alphabetize: bool = True, enable_completion: bool = False):
    """
    Initialize CLI with target and configuration.

    :param target: Module, class, or list of classes to generate CLI from
    :param title: CLI application title
    :param function_filter: Optional filter for functions (module mode)
    :param method_filter: Optional filter for methods (class mode)
    :param theme: Optional theme for colored output
    :param alphabetize: Whether to sort commands and options alphabetically
    :param enable_completion: Whether to enable shell completion
    """
    # Determine target mode and validate input
    self.target_mode, self.target_info = CliTargetAnalyzer.analyze_target(target)

    # Validate class mode for command collisions when multiple classes are present
    all_classes = self.target_info.get(TargetInfoKeys.ALL_CLASSES.value)
    if all_classes and len(all_classes) > 1:
      handler = MultiClassHandler()
      handler.validate_classes(all_classes)

    # Set title based on target
    self.title = title or CliTargetAnalyzer.generate_title(target)

    # Store only essential config
    self.enable_completion = enable_completion

    # Initialize discovery service
    discovery = CommandDiscovery(target=target, function_filter=function_filter, method_filter=method_filter)

    # Discover commands
    self.discovered_commands = discovery.discover_commands()

    # Initialize command executors
    executors = self._initialize_executors()

    # Initialize execution coordinator
    self.execution_coordinator = CliExecutionCoordinator(self.target_mode, executors)

    # Initialize parser service
    self.parser_service = CommandParser(title=self.title, theme=theme, alphabetize=alphabetize, enable_completion=enable_completion)

    # Set target_class and target_classes properties early for use in command tree building
    all_classes = self.target_info.get(TargetInfoKeys.ALL_CLASSES.value)
    if all_classes:
      # Class mode: set both for backward compatibility
      self.target_class = self.target_info.get(TargetInfoKeys.PRIMARY_CLASS.value)
      self.target_classes = all_classes
    else:
      # Module mode
      self.target_class = None
      self.target_classes = None

    # Build command structure (after target_classes is set)
    command_tree = self._build_command_tree()

    # Backward compatibility properties
    self.commands = command_tree

    # Essential compatibility properties only
    self.target_module = self.target_info.get(TargetInfoKeys.MODULE.value)

  def run(self, args: List[str] = None) -> Any:
    """
    Parse arguments and execute the appropriate command.

    :param args: Optional command line arguments (uses sys.argv if None)
    :return: Command execution result
    """
    result = None

    # Handle completion requests early
    if self.enable_completion and self._is_completion_request():
      self._handle_completion()
    else:
      # Check for no-color flag
      no_color = CliExecutionCoordinator.check_no_color_flag(args or [])

      # Create parser and parse arguments
      parser = self.create_parser(no_color=no_color)

      # Parse and execute with context  
      result = self._execute_with_context(parser, args)

    return result

  def _execute_with_context(self, parser, args) -> Any:
    """Execute command with CLI context."""
    # Add context information to the execution coordinator
    self.execution_coordinator.use_inner_class_pattern = any(cmd.is_hierarchical for cmd in self.discovered_commands)
    self.execution_coordinator.inner_class_metadata = self._get_inner_class_metadata()
    self.execution_coordinator.discovered_commands = self.discovered_commands

    return self.execution_coordinator.parse_and_execute(parser, args)

  def _initialize_executors(self) -> dict:
    """Initialize command executors based on target mode."""
    executors = {}
    all_classes = self.target_info.get(TargetInfoKeys.ALL_CLASSES.value)

    if all_classes and len(all_classes) > 1:
      # Multiple classes: create executor for each class
      for target_class in all_classes:
        executor = CommandExecutor(target_class=target_class, target_module=None, inner_class_metadata=self._get_inner_class_metadata())
        executors[target_class] = executor
    else:
      # Single class or module: create single primary executor
      primary_executor = CommandExecutor(target_class=self.target_info.get(TargetInfoKeys.PRIMARY_CLASS.value),
                                         target_module=self.target_info.get(TargetInfoKeys.MODULE.value),
                                         inner_class_metadata=self._get_inner_class_metadata())
      executors['primary'] = primary_executor

    return executors

  def _get_inner_class_metadata(self) -> dict:
    """Extract inner class metadata from discovered commands."""
    metadata = {}

    for command in self.discovered_commands:
      if command.is_hierarchical and command.metadata:
        metadata[command.name] = command.metadata

    return metadata

  def _build_command_tree(self) -> dict:
    """Build hierarchical command structure using CommandBuilder."""
    # Convert CommandInfo objects to the format expected by CommandBuilder
    functions = {}
    inner_classes = {}

    for command in self.discovered_commands:
      # Use the hierarchical name if available, otherwise original name
      if command.is_hierarchical and command.parent_class:
        # For multiple classes, key by the full command name that includes class prefix
        # For single class, use parent_class__method format
        if len(self.target_classes or []) > 1:
          # Multiple classes: command name keyed by class prefix: system--completion__handle-completion
          functions[command.name] = command.function
        else:
          # Single class: Keyed by class__method
          hierarchical_key = f"{command.parent_class}__{command.original_name}"
          functions[hierarchical_key] = command.function
      else:
        # Direct methods use original name for backward compatibility
        functions[command.original_name] = command.function

      if command.is_hierarchical and command.inner_class:
        inner_classes[command.parent_class] = command.inner_class

    # Determine if using inner class pattern
    use_inner_class_pattern = any(cmd.is_hierarchical for cmd in self.discovered_commands)

    builder = CommandBuilder(target_mode=self.target_mode, functions=functions, inner_classes=inner_classes,
                             use_inner_class_pattern=use_inner_class_pattern)

    return builder.build_command_tree()

  def _is_completion_request(self) -> bool:
    """Check if this is a shell completion request."""
    import os
    return os.getenv('_FREYA_COMPLETE') is not None

  def _handle_completion(self):
    """Handle shell completion request."""
    try:
      completion_handler = get_completion_handler(self)
      completion_handler.complete()
    except ImportError:
      # Completion module    not available
      pass

  def create_parser(self, no_color: bool = False):
    """Create argument parser (for backward compatibility)."""
    return self.parser_service.create_parser(commands=self.discovered_commands, target_mode=self.target_mode.value,
                                             target_class=self.target_info.get(TargetInfoKeys.PRIMARY_CLASS.value), no_color=no_color)
