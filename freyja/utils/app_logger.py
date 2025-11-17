import logging
import sys
from typing import Optional

from freyja.utils.version import get_freyja_version


class LoggerConfig:
  """Configuration for Freyja's internal logging."""


  version = get_freyja_version()
  def __init__(
    self,
    level: int = logging.INFO,
    format: str = f'[Freyja version: {version}]%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handler: Optional[logging.Handler] = None,
    propagate: bool = True,
    version: str = "v0.0.0"
  ):
    self.level = level
    self.format = format
    self.handler = handler
    self.propagate = propagate
    self.version = version


class AppLogger:
  """Manages Freyja's internal logging with smart defaults."""

  _initialized = False
  _config: Optional[LoggerConfig] = None

  @classmethod
  def get_logger(cls, name: str = 'freyja') -> logging.Logger:
    """Get a Freyja logger, initializing if needed."""
    if not cls._initialized:
      cls._auto_initialize()

    return logging.getLogger(name)

  @classmethod
  def _auto_initialize(cls) -> None:
    """Auto-initialize with smart defaults."""
    logger = logging.getLogger('freyja')

    # Check if already configured
    if logger.handlers or cls._has_root_handlers():
      cls._initialized = True
      return

    # Apply default configuration
    config = LoggerConfig()
    cls.configure(config)

  @classmethod
  def _has_root_handlers(cls) -> bool:
    """Check if root logger has handlers."""
    root = logging.getLogger()
    return bool(root.handlers)

  @classmethod
  def configure(cls, config: LoggerConfig) -> None:
    """Explicitly configure Freyja logging."""
    logger = logging.getLogger('freyja')
    logger.setLevel(config.level)
    logger.propagate = config.propagate

    # Clear existing handlers
    logger.handlers.clear()

    # Add new handler
    handler = config.handler or logging.StreamHandler(sys.stderr)
    if isinstance(handler, logging.StreamHandler) and not handler.formatter:
      handler.setFormatter(logging.Formatter(config.format))

    logger.addHandler(handler)
    cls._initialized = True
    cls._config = config

  @classmethod
  def disable(cls) -> None:
    """Disable Freyja logging."""
    logger = logging.getLogger('freyja')
    logger.handlers.clear()
    logger.setLevel(logging.CRITICAL + 1)
    cls._initialized = True
