# Refactored CLI class - Simplified coordinator role only
from __future__ import annotations

import argparse
import types
from typing import *

from .command.command_builder import CommandBuilder
from .command.command_discovery import CommandDiscovery
from .command.command_executor import CommandExecutor
from .command.command_parser import CommandParser
from .command.cli_execution_coordinator import CliExecutionCoordinator
from .command.cli_target_analyzer import CliTargetAnalyzer
from .command.multi_class_handler import MultiClassHandler
from .completion.base import get_completion_handler
from .enums import TargetInfoKeys, TargetMode

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

    # Validate multi-class mode for command collisions
    if self.target_mode == TargetMode.MULTI_CLASS:
      handler = MultiClassHandler()
      handler.validate_classes(self.target_info[TargetInfoKeys.ALL_CLASSES.value])

    # Set title based on target
    self.title = title or CliTargetAnalyzer.generate_title(target)

    # Store configuration
    self.theme = theme
    self.alphabetize = alphabetize
    self.enable_completion = enable_completion

    # Initialize discovery service
    self.discovery = CommandDiscovery(target=target, function_filter=function_filter, method_filter=method_filter)

    # Initialize parser service
    self.parser_service = CommandParser(title=self.title, theme=theme, alphabetize=alphabetize,
      enable_completion=enable_completion)

    # Discover commands
    self.discovered_commands = self.discovery.discover_commands()

    # Initialize command executors
    self.executors = self._initialize_executors()

    # Initialize execution coordinator
    self.execution_coordinator = CliExecutionCoordinator(self.target_mode, self.executors)

    # Build command structure
    self.command_tree = self._build_command_tree()

    # Backward compatibility properties
    self.functions = self._build_functions_dict()
    self.commands = self.command_tree

    # Essential compatibility properties only
    self.target_module = self.target_info.get(TargetInfoKeys.MODULE.value)

    # Set target_class and target_classes based on mode
    if self.target_mode == TargetMode.MULTI_CLASS:
      self.target_class = None  # Multi-class mode has no single primary class
      self.target_classes = self.target_info.get(TargetInfoKeys.ALL_CLASSES.value)
    else:
      self.target_class = self.target_info.get(TargetInfoKeys.PRIMARY_CLASS.value)
      self.target_classes = None

  @property
  def function_filter(self):
    """Access function filter from discovery service."""
    return self.discovery.function_filter if self.target_mode == TargetMode.MODULE else None

  @property
  def method_filter(self):
    """Access method filter from discovery service."""
    return self.discovery.method_filter if self.target_mode in [TargetMode.CLASS, TargetMode.MULTI_CLASS] else None

  @property
  def use_inner_class_pattern(self):
    """Check if using inner class pattern based on discovered commands."""
    return any(cmd.is_hierarchical for cmd in self.discovered_commands)

  @property
  def command_executor(self):
    """Access primary command executor (for single class/module mode)."""
    result = None
    if self.target_mode != TargetMode.MULTI_CLASS:
      result = self.executors.get('primary')
    return result

  @property
  def command_executors(self):
    """Access command executors list (for multi-class mode)."""
    result = None
    if self.target_mode == TargetMode.MULTI_CLASS:
      result = list(self.executors.values())
    return result

  @property
  def inner_classes(self):
    """Access inner classes from discovered commands."""
    inner_classes = {}
    for command in self.discovered_commands:
      if command.is_hierarchical and command.inner_class:
        inner_classes[command.parent_class] = command.inner_class
    return inner_classes

  def display(self):
    """Legacy method for backward compatibility."""
    return self.run()

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
      parser = self.parser_service.create_parser(commands=self.discovered_commands, target_mode=self.target_mode.value,
        target_class=self.target_info.get(TargetInfoKeys.PRIMARY_CLASS.value), no_color=no_color)

      # Parse and execute with context
      result = self._execute_with_context(parser, args or [])

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

    if self.target_mode == TargetMode.MULTI_CLASS:
      # Create executor for each class
      for target_class in self.target_info[TargetInfoKeys.ALL_CLASSES.value]:
        executor = CommandExecutor(target_class=target_class, target_module=None,
          inner_class_metadata=self._get_inner_class_metadata())
        executors[target_class] = executor

    else:
      # Single executor
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

  def _build_functions_dict(self) -> dict:
    """Build functions dict for backward compatibility."""
    functions = {}

    for command in self.discovered_commands:
      # Use original names for backward compatibility (tests expect this)
      functions[command.original_name] = command.function

    return functions

  def _build_command_tree(self) -> dict:
    """Build hierarchical command structure using CommandBuilder."""
    # Convert CommandInfo objects to the format expected by CommandBuilder
    functions = {}
    inner_classes = {}

    for command in self.discovered_commands:
      # Use the hierarchical name if available, otherwise original name
      if command.is_hierarchical and command.parent_class:
        # For multi-class mode, use the full command name that includes class prefix
        # For single-class mode, use parent_class__method format
        if self.target_mode == TargetMode.MULTI_CLASS:
          # Command name already includes class prefix: system--completion__handle-completion
          functions[command.name] = command.function
        else:
          # Single class mode: Completion__handle_completion
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
    return os.getenv('_AUTO_CLI_COMPLETE') is not None

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
