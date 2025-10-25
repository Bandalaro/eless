"""Default configuration for ELESS.

This module provides default configuration values for the ELESS pipeline.
"""

from typing import Dict, Any
import copy

# Default configuration dictionary
DEFAULT_CONFIG = {
    "cache": {
        "directory": ".eless_cache",
        "manifest_file": "manifest.json",
        "max_size_mb": 1024,
        "max_files": 10000,
        "auto_cleanup": True,
    },
    "logging": {
        "directory": ".eless_logs",
        "level": "INFO",
        "enable_console": True,
        "max_file_size_mb": 10,
        "backup_count": 5,
    },
    "embedding": {
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimension": 384,
        "device": "cpu",
        "batch_size": 32,
        "normalize": True,
        "cache_embeddings": True,
        "model_path": None,
        "use_gpu": False,
        "quantize": False,
    },
    "resource_limits": {
        "memory_warning_percent": 80,
        "memory_critical_percent": 90,
        "cpu_high_percent": 85,
        "min_memory_mb": 256,
        "max_memory_mb": 512,
        "enable_adaptive_batching": True,
    },
    "streaming": {
        "buffer_size": 8192,
        "max_file_size_mb": 100,
        "enable_memory_mapping": True,
        "auto_streaming_threshold": 0.7,
    },
    "chunking": {
        "chunk_size": 500,
        "chunk_overlap": 50,
        "min_chunk_size": 64,
        "skip_short_chunks": True,
        "overlap_strategy": "simple",
        "text_splitter": "sentence",
        "language": "en",
    },
    "parallel_processing": {
        "max_workers": None,
        "mode": "auto",
        "enable_parallel_files": True,
        "enable_parallel_chunks": True,
        "enable_parallel_embedding": True,
        "enable_parallel_database": True,
        "chunk_batch_size": 100,
        "file_batch_size": 10,
        "resource_monitoring": True,
        "adaptive_workers": True,
        "memory_threshold_percent": 80,
        "cpu_threshold_percent": 85,
        "queue_size": 100,
        "timeout_seconds": 300,
        "enable_progress_tracking": True,
    },
    "databases": {
        "batch_size": 64,
        "default": {"drop_existing": False},
        "targets": [],  # Empty by default; users should add based on installed dependencies
        "connections": {
            "chroma": {"type": "chroma", "path": ".eless_chroma"},
            "faiss": {
                "type": "faiss",
                "index_path": ".eless_faiss/index.faiss",
                "metadata_path": ".eless_faiss/metadata.json",
            },
            "qdrant": {
                "type": "qdrant",
                "host": "localhost",
                "port": 6333,
                "api_key": None,
                "collection_name": "eless_embeddings",
                "timeout": 30,
            },
            "postgresql": {
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "user": "your_user",
                "password": "your_password",
                "database": "your_db",
                "table_name": "eless_embeddings",
                "connection_timeout": 30,
            },
            "cassandra": {
                "type": "cassandra",
                "hosts": ["localhost"],
                "port": 9042,
                "keyspace": "eless_keyspace",
                "table_name": "eless_embeddings",
                "replication_factor": 1,
            },
        },
    },
}


def get_default_config() -> Dict[str, Any]:
    """Get default configuration values for ELESS pipeline.

    Returns:
        Dict[str, Any]: Default configuration dictionary
    """
    return copy.deepcopy(DEFAULT_CONFIG)
