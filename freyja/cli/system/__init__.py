"""Freyja system command components (shell completion)."""

from .completion import Completion


class SystemClassBuilder:
  """Dynamically build a System class containing the enabled system commands."""

  @staticmethod
  def build(completion: bool = True) -> type:
    """Build the System class with the requested components enabled."""
    members: dict = {}
    if completion:
      members['Completion'] = Completion
    return type('System', (object,), members)


System = SystemClassBuilder.build(completion=True)

__all__ = ['SystemClassBuilder', 'System', 'Completion']
