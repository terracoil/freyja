import enum


class TargetInfoKeys(enum.Enum):
    """Keys for target_info dictionary."""
    MODULE = 'module'
    PRIMARY_CLASS = 'primary_class'
    ALL_CLASSES = 'all_classes'


class TargetMode(enum.Enum):
    """Target mode enum for command discovery."""
    MODULE = 'module'
    CLASS = 'class'
    MULTI_CLASS = 'multi_class'
