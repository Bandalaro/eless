"""
ELESS (Evolving Low-resource Embedding and Storage System)

A resilient RAG data processing pipeline with comprehensive logging,
multi-database support, and CLI interface.
"""

__version__ = "1.0.0"
__author__ = "ELESS Team"
__description__ = "Evolving Low-resource Embedding and Storage System"

from .cli import cli

__all__ = ["cli"]
