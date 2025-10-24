from .completion import Completion
from .tune_theme import TuneTheme


class SystemClassBuilder:
    """Dynamically builds System class with selected system command components."""

    @staticmethod
    def build(completion: bool = True, theme_tuner: bool = False) -> type:
        """Build System class with specified command components enabled."""
        system_class_dict: dict = {}

        if completion:
            system_class_dict["Completion"] = Completion
        if theme_tuner:
            system_class_dict["TuneTheme"] = TuneTheme
        return type("System", (object,), system_class_dict)


# Create default System class for direct import
System = SystemClassBuilder.build(completion=True, theme_tuner=True)

__all__ = ["SystemClassBuilder", "System", "Completion", "TuneTheme"]
