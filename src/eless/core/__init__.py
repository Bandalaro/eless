"""Core package containing configuration and utility modules."""

from .config_loader import ConfigLoader
from .default_config import get_default_config

__all__ = ["ConfigLoader", "get_default_config"]
