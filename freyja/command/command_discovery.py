# Command discovery functionality extracted from FreyjaCLI class.
import inspect
from collections.abc import Callable
from typing import Any, Sequence

from freyja.cli import SystemClassBuilder, TargetModeEnum
from freyja.parser import DocStringParser
from freyja.utils import TextUtil
from freyja.shared.command_info import CommandInfo
from freyja.shared.command_tree import CommandTree

from .validation_service import ValidationService

TargetType = type | list[type] | type[Any] | Sequence[type[Any]]


class CommandDiscovery:
    """
    Discovers commands from classes using introspection.

    Handles both flat command structures (direct methods) and
    hierarchical structures (inner classes with methods).
    """

    def __init__(
        self,
        target: TargetType,
        method_filter: Callable[[type, str, Any], bool] | None = None,
        completion: bool = True,
        theme_tuner: bool = False,
    ):
        """
        Initialize command discovery.

        :param target: Class or list of classes to discover from
        :param method_filter: Optional filter for class methods
        """
        self.target = target
        self.method_filter = method_filter or self._default_method_filter

        self.completion: bool = completion
        self.theme_tuner: bool = theme_tuner

        self.target_classes: list[type] = []
        self.mode: TargetModeEnum = TargetModeEnum.CLASS
        self.primary_class: type | None = None

        # Determine target mode with unified class handling
        if isinstance(target, list):
            self.target_classes = target
            self._validate_classes(self.target_classes)
            self.primary_class = self.target_classes[-1]
        elif inspect.isclass(target):
            self.primary_class = target
            self.target_classes = [target]
        else:
            raise ValueError(
                f"Target must be class or list of classes, got {type(target).__name__}"
            )

        self.cmd_tree: CommandTree = self.discover_commands()

    def discover_commands(self) -> CommandTree:
        """
        Discover all commands from the target classes.

        :return: CommandTree with hierarchical command structure
        """
        # Import CommandTree here to avoid circular imports
        command_tree: CommandTree = CommandTree()

        # Unified class handling: always use multi-class logic for consistency
        self.discover_classes(command_tree)

        return command_tree

    def _discover_from_class(
        self, target_cls: type, command_tree, is_namespaced: bool = False
    ) -> None:
        """Discover methods from a single class and add to command tree."""
        # Check for inner classes first (hierarchical pattern)
        inner_classes = self._discover_inner_classes(target_cls)

        if inner_classes:
            # Mixed pattern: direct methods + inner class methods
            ValidationService.validate_constructor_parameters(target_cls, "main class")

            # Validate inner class constructors
            for class_name, inner_class in inner_classes.items():
                ValidationService.validate_inner_class_constructor_parameters(
                    inner_class, f"inner class '{class_name}'"
                )
        else:
            # Direct methods only (flat pattern)
            ValidationService.validate_constructor_parameters(
                target_cls, "class", allow_parameterless_only=True
            )

        # Create top-level group for namespaced classes (whether they have inner classes or not)
        if is_namespaced:
            class_namespace = TextUtil.kebab_case(target_cls.__name__)
            class_description = self._get_class_description(target_cls)
            command_tree.add_group(
                class_namespace,
                class_description,
                is_system_command=self.is_system(target_cls),
                is_namespaced=True,
            )

        # Discover direct methods
        self._discover_direct_methods(target_cls, command_tree, is_namespaced)

        # Discover inner class methods (if any)
        if inner_classes:
            self._discover_methods_from_inner_classes(
                target_cls, inner_classes, command_tree, is_namespaced
            )

    @staticmethod
    def _validate_classes(targets: list[type]) -> None:
        if not targets:
            raise ValueError("Passed a list, but no target classes were found.")

        if invalid_items := [item for item in targets if not isinstance(item, type)]:
            invalid_type = type(invalid_items[0]).__name__
            raise ValueError(f"All items in list must be classes, got {invalid_type}")

    def discover_classes(self, command_tree) -> None:
        """Discover methods from classes (single or multiple) and add to command tree.

        For single class: methods get no namespace prefix (global namespace).
        Multi-class: last gets global namespace, others get kebab-case prefixes.
        """
        if self.completion or self.theme_tuner:
            system = SystemClassBuilder.build(self.completion, self.theme_tuner)
            self.target_classes.insert(
                0, system
            )  # SystemClassBuilder.build(self.completion, self.theme_tuner))

        # Separate last class (global) from others (namespaced)
        namespaced_classes = self.target_classes[:-1] if len(self.target_classes) > 1 else []

        # Process namespaced classes first (with class name prefixes)
        for target_class in namespaced_classes:
            # Discover cmd_tree for this class and add to tree
            self._discover_from_class(target_class, command_tree, is_namespaced=True)

        # Discover cmd_tree for primary class (no namespace)
        if self.primary_class is not None:
            self._discover_from_class(self.primary_class, command_tree, is_namespaced=False)

    def _discover_inner_classes(self, target_class: type) -> dict[str, type]:
        """Discover inner classes that should be treated as command groups."""
        inner_classes = {}

        for name, obj in inspect.getmembers(target_class):
            if inspect.isclass(obj) and not name.startswith(
                "_"
            ):  # and obj.__qualname__.endswith(f'{target_class.__name__}.{name}')):
                inner_classes[name] = obj

        return inner_classes

    def _discover_direct_methods(
        self, target_class, command_tree, is_namespaced: bool = False
    ) -> None:
        """Discover methods directly from the target class and add to command tree."""
        for name, obj in inspect.getmembers(target_class):
            if self.method_filter(target_class, name, obj):
                command_info = CommandInfo(
                    name=TextUtil.kebab_case(name),
                    original_name=name,
                    function=obj,
                    signature=inspect.signature(obj),
                    docstring=inspect.getdoc(obj),
                )

                # Add metadata for execution
                command_info.metadata["source_class"] = target_class
                command_info.metadata["is_namespaced"] = is_namespaced
                if is_namespaced:
                    command_info.metadata["class_namespace"] = TextUtil.kebab_case(
                        target_class.__name__
                    )
                    # Add command to the parent class group
                    class_namespace = TextUtil.kebab_case(target_class.__name__)
                    command_tree.add_command_to_group(
                        class_namespace, command_info.name, command_info
                    )
                else:
                    command_info.metadata["class_namespace"] = None
                    command_tree.add_command(command_info.name, command_info)

    def _discover_methods_from_inner_classes(
        self,
        target_cls: type,
        inner_classes: dict[str, type],
        command_tree,
        is_namespaced: bool = False,
    ) -> None:
        """Discover methods from inner classes for hierarchical cmd_tree and add to tree."""
        for class_name, inner_class in inner_classes.items():
            command_name = TextUtil.kebab_case(class_name)

            # Get group description from inner class docstring
            description = self._get_group_description(inner_class, command_name)

            if is_namespaced:
                # Create subgroup under the parent class group
                class_namespace = TextUtil.kebab_case(target_cls.__name__)
                command_tree.add_subgroup_to_group(
                    class_namespace,
                    command_name,
                    description,
                    inner_class=inner_class,
                    is_system_command=self.is_system(target_cls),
                )
                full_group_path = f"{class_namespace}.{command_name}"
            else:
                # Create top-level group
                command_tree.add_group(
                    command_name,
                    description,
                    inner_class=inner_class,
                    is_system_command=self.is_system(target_cls),
                )
                full_group_path = command_name

            for method_name, method_obj in inspect.getmembers(inner_class):
                if (
                    not method_name.startswith("_")
                    and callable(method_obj)
                    and method_name != "__init__"
                    and inspect.isfunction(method_obj)
                ):
                    # Use kebab-cased method name as command name (no dunder notation)
                    method_kebab = TextUtil.kebab_case(method_name)

                    command_info = CommandInfo(
                        name=method_kebab,  # Just the method name, not group__method
                        original_name=method_name,
                        function=method_obj,
                        signature=inspect.signature(method_obj),
                        docstring=inspect.getdoc(method_obj),
                        is_hierarchical=True,
                        parent_class=class_name,
                        command_path=full_group_path,
                        inner_class=inner_class,
                        is_system_command=self.is_system(target_cls),
                        group_name=command_name,  # Just the inner class name
                        method_name=method_kebab,  # Kebab-cased method name
                    )

                    # Store metadata for execution
                    command_info.metadata.update(
                        {
                            "inner_class": inner_class,
                            "inner_class_name": class_name,
                            "command_name": command_name,
                            "method_name": method_name,
                            "source_class": target_cls,
                            "is_namespaced": is_namespaced,
                        }
                    )

                    if is_namespaced:
                        command_info.metadata["class_namespace"] = TextUtil.kebab_case(
                            target_cls.__name__
                        )
                        # Add command to subgroup
                        command_tree.add_command_to_subgroup(
                            TextUtil.kebab_case(target_cls.__name__),
                            command_name,
                            method_kebab,
                            command_info,
                            method_name=method_kebab,
                        )
                    else:
                        command_info.metadata["class_namespace"] = None
                        # Add command to top-level group
                        command_tree.add_command_to_group(
                            command_name, method_kebab, command_info, method_name=method_kebab
                        )

    def _get_group_description(self, inner_class: type, group_name: str) -> str:
        """Get description for command group from inner class docstring."""
        if inner_class and inner_class.__doc__:
            description, _ = DocStringParser.parse_docstring(inner_class.__doc__)
            return description

        # Fallback to generating description from group name
        return f"{group_name.title().replace('-', ' ')} operations"

    def _get_class_description(self, target_cls: type) -> str:
        """Get description for class group from class docstring."""
        if target_cls and target_cls.__doc__:
            description, _ = DocStringParser.parse_docstring(target_cls.__doc__)
            return description

        # Fallback to generating description from class name
        class_name = TextUtil.kebab_case(target_cls.__name__)
        return f"{class_name.title().replace('-', ' ')} cmd_tree and utilities"

    def is_system(self, cls: type) -> bool:
        """Check if class is a System command class."""
        return cls.__name__ == "System"

    def _default_method_filter(self, target_class: type, name: str, obj: Any) -> bool:
        """Default filter for class methods."""
        if target_class is None:
            return False

        if name.startswith("_"):
            return False

        if not callable(obj):
            return False

        if not (inspect.isfunction(obj) or inspect.ismethod(obj)):
            return False

        if not hasattr(obj, "__qualname__"):
            return False

        # Check if method belongs to this class or its inheritance chain
        # This handles both direct methods and inherited methods properly
        method_belongs_to_class = False
        
        # First check if it's a direct method of the target class
        if target_class.__name__ in obj.__qualname__:
            method_belongs_to_class = True
        else:
            # Check if it's an inherited method by looking at MRO
            # The method should belong to one of the classes in the inheritance chain
            for base_class in target_class.__mro__:
                if base_class.__name__ in obj.__qualname__:
                    # Verify this is actually the same method object
                    try:
                        if hasattr(base_class, name) and getattr(base_class, name) is obj:
                            method_belongs_to_class = True
                            break
                    except AttributeError:
                        continue
        
        if not method_belongs_to_class:
            return False
        
        # Exclude @staticmethod and @classmethod decorated methods
        # Only instance methods should become CLI commands
        try:
            raw_attr = inspect.getattr_static(target_class, name)
            if isinstance(raw_attr, staticmethod):
                return False
            if isinstance(raw_attr, classmethod):
                return False
        except (AttributeError, TypeError):
            # If we can't determine the method type, allow it through
            pass

        return True

    def generate_title(self) -> str:
        """Generate FreyjaCLI title based on target type."""
        if self.primary_class:
            if self.primary_class.__doc__:
                main_desc, _ = DocStringParser.parse_docstring(self.primary_class.__doc__)
                return main_desc or self.primary_class.__name__
            return self.primary_class.__name__

        return "FreyjaCLI Application"
