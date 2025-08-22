"""Auto-CLI: Generate CLIs from functions automatically using docstrings."""
from .cli import CLI
from .str_utils import StrUtils
from auto_cli.theme.theme_tuner import ThemeTuner, run_theme_tuner

__all__=["CLI", "StrUtils", "ThemeTuner", "run_theme_tuner"]
__version__="1.5.0"
