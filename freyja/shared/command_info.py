import inspect
from collections.abc import Callable as CallableABC
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CommandInfo:
    """Information about a discovered command."""

    name: str
    original_name: str
    function: CallableABC
    signature: inspect.Signature
    docstring: str | None = None
    is_hierarchical: bool = False
    parent_class: str | None = None
    command_path: str | None = None
    is_system_command: bool = False
    inner_class: type | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    # New fields for nested command structure
    group_name: str | None = None  # For hierarchical cmd_tree (kebab-cased inner class name)
    method_name: str | None = None  # For hierarchical cmd_tree (kebab-cased method name)
