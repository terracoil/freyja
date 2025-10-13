"""
Freyja: Zero-configuration CLI generator from class introspection.
Uses class/method introspection, type hints, and docstrings to build
a fully functional CLI.  Command groups can be made with inner-classes,
effectively organizing commands into logical groups.
"""

from .freyja_cli import FreyjaCLI

__version__ = "1.0.15"
__all__ = ["FreyjaCLI"]
