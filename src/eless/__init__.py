"""
ELESS - Evolving Low-resource Embedding and Storage System

A resilient RAG data processing pipeline with comprehensive logging,
multi-database support, and CLI interface.
"""

__version__ = "1.0.0"
__author__ = "ELESS Team"

from .eless_pipeline import ElessPipeline
from .core.state_manager import StateManager, FileStatus
from .core.config_loader import ConfigLoader

__all__ = [
    "ElessPipeline",
    "StateManager",
    "FileStatus",
    "ConfigLoader",
    "__version__",
]
