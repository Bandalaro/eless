"""
Configuration templates for ELESS.
Provides pre-made configurations for common use cases.
"""

from typing import Dict, Any


def get_minimal_template() -> Dict[str, Any]:
    """
    Minimal configuration for low-resource systems.
    Suitable for systems with 1-2GB RAM.

    Returns:
        Configuration dictionary
    """
    return {
        "embedding": {
            "model_name": "all-MiniLM-L6-v2",
            "device": "cpu",
            "batch_size": 8,
            "normalize_embeddings": True,
        },
        "chunking": {
            "chunk_size": 256,
            "chunk_overlap": 32,
            "method": "recursive",
        },
        "resource_limits": {
            "max_memory_mb": 256,
            "enable_adaptive_batching": True,
            "max_cpu_percent": 70,
            "memory_warning_percent": 80,
        },
        "streaming": {
            "enable": True,
            "buffer_size": 4096,
            "max_file_size_mb": 50,
            "auto_streaming_threshold": 0.5,
        },
        "parallel_processing": {
            "enable_parallel_files": False,
            "enable_parallel_chunks": False,
            "enable_parallel_embedding": False,
            "enable_parallel_database": False,
            "max_workers": 1,
            "mode": "thread",
        },
        "cache": {
            "enable": True,
            "directory": ".eless_cache",
            "max_size_mb": 100,
            "max_files": 50,
            "eviction_strategy": "lru",
        },
        "databases": {
            "targets": ["faiss"],  # FAISS is lightest
            "batch_size": 8,
        },
    }


def get_balanced_template() -> Dict[str, Any]:
    """
    Balanced configuration for typical systems.
    Suitable for systems with 4-8GB RAM.

    Returns:
        Configuration dictionary
    """
    return {
        "embedding": {
            "model_name": "all-MiniLM-L6-v2",
            "device": "auto",  # Will use GPU if available
            "batch_size": 32,
            "normalize_embeddings": True,
        },
        "chunking": {
            "chunk_size": 512,
            "chunk_overlap": 64,
            "method": "recursive",
        },
        "resource_limits": {
            "max_memory_mb": 2048,
            "enable_adaptive_batching": True,
            "max_cpu_percent": 80,
            "memory_warning_percent": 85,
        },
        "streaming": {
            "enable": True,
            "buffer_size": 8192,
            "max_file_size_mb": 100,
            "auto_streaming_threshold": 0.7,
        },
        "parallel_processing": {
            "enable_parallel_files": True,
            "enable_parallel_chunks": False,
            "enable_parallel_embedding": True,
            "enable_parallel_database": True,
            "max_workers": 4,
            "mode": "auto",
        },
        "cache": {
            "enable": True,
            "directory": ".eless_cache",
            "max_size_mb": 500,
            "max_files": 200,
            "eviction_strategy": "lru",
        },
        "databases": {
            "targets": ["chroma"],
            "batch_size": 32,
        },
    }


def get_high_performance_template() -> Dict[str, Any]:
    """
    High-performance configuration for powerful systems.
    Suitable for systems with 16GB+ RAM and GPU.

    Returns:
        Configuration dictionary
    """
    return {
        "embedding": {
            "model_name": "all-mpnet-base-v2",  # Better quality model
            "device": "cuda",
            "batch_size": 64,
            "normalize_embeddings": True,
        },
        "chunking": {
            "chunk_size": 1024,
            "chunk_overlap": 128,
            "method": "recursive",
        },
        "resource_limits": {
            "max_memory_mb": 8192,
            "enable_adaptive_batching": True,
            "max_cpu_percent": 90,
            "memory_warning_percent": 90,
        },
        "streaming": {
            "enable": False,  # Can load everything in memory
            "buffer_size": 16384,
            "max_file_size_mb": 500,
            "auto_streaming_threshold": 0.9,
        },
        "parallel_processing": {
            "enable_parallel_files": True,
            "enable_parallel_chunks": True,
            "enable_parallel_embedding": True,
            "enable_parallel_database": True,
            "max_workers": 8,
            "mode": "process",  # Use multiprocessing for max speed
        },
        "cache": {
            "enable": True,
            "directory": ".eless_cache",
            "max_size_mb": 2000,
            "max_files": 1000,
            "eviction_strategy": "lru",
        },
        "databases": {
            "targets": ["chroma", "qdrant"],  # Use multiple for redundancy
            "batch_size": 64,
        },
    }


def get_low_memory_template() -> Dict[str, Any]:
    """
    Low-memory configuration for constrained systems.
    Suitable for systems with <2GB RAM or embedded devices.

    Returns:
        Configuration dictionary
    """
    return {
        "embedding": {
            "model_name": "all-MiniLM-L6-v2",
            "device": "cpu",
            "batch_size": 4,
            "normalize_embeddings": True,
        },
        "chunking": {
            "chunk_size": 200,
            "chunk_overlap": 20,
            "method": "simple",
        },
        "resource_limits": {
            "max_memory_mb": 128,
            "enable_adaptive_batching": True,
            "max_cpu_percent": 60,
            "memory_warning_percent": 75,
        },
        "streaming": {
            "enable": True,
            "buffer_size": 2048,
            "max_file_size_mb": 20,
            "auto_streaming_threshold": 0.3,
        },
        "parallel_processing": {
            "enable_parallel_files": False,
            "enable_parallel_chunks": False,
            "enable_parallel_embedding": False,
            "enable_parallel_database": False,
            "max_workers": 1,
            "mode": "thread",
        },
        "cache": {
            "enable": True,
            "directory": ".eless_cache",
            "max_size_mb": 50,
            "max_files": 25,
            "eviction_strategy": "lru",
        },
        "databases": {
            "targets": ["faiss"],
            "batch_size": 4,
        },
    }


def get_docker_template() -> Dict[str, Any]:
    """
    Docker-optimized configuration.
    Suitable for containerized deployments with predictable resources.

    Returns:
        Configuration dictionary
    """
    return {
        "embedding": {
            "model_name": "all-MiniLM-L6-v2",
            "device": "cpu",  # GPU support in Docker requires special setup
            "batch_size": 16,
            "normalize_embeddings": True,
        },
        "chunking": {
            "chunk_size": 512,
            "chunk_overlap": 64,
            "method": "recursive",
        },
        "resource_limits": {
            "max_memory_mb": 1024,
            "enable_adaptive_batching": True,
            "max_cpu_percent": 80,
            "memory_warning_percent": 85,
        },
        "streaming": {
            "enable": True,
            "buffer_size": 8192,
            "max_file_size_mb": 100,
            "auto_streaming_threshold": 0.7,
        },
        "parallel_processing": {
            "enable_parallel_files": True,
            "enable_parallel_chunks": False,
            "enable_parallel_embedding": False,
            "enable_parallel_database": True,
            "max_workers": 2,
            "mode": "thread",  # Thread mode works better in containers
        },
        "cache": {
            "enable": True,
            "directory": "/data/.eless_cache",  # Standard Docker volume path
            "max_size_mb": 500,
            "max_files": 200,
            "eviction_strategy": "lru",
        },
        "databases": {
            "targets": ["chroma"],
            "batch_size": 16,
        },
        "logging": {
            "directory": "/logs",  # Standard Docker volume path
            "level": "INFO",
            "enable_console": True,
        },
    }


def get_template(template_name: str) -> Dict[str, Any]:
    """
    Get a configuration template by name.

    Args:
        template_name: Name of the template

    Returns:
        Configuration dictionary

    Raises:
        ValueError: If template name is not recognized
    """
    templates = {
        "minimal": get_minimal_template,
        "balanced": get_balanced_template,
        "high-performance": get_high_performance_template,
        "low-memory": get_low_memory_template,
        "docker": get_docker_template,
    }

    if template_name not in templates:
        raise ValueError(
            f"Unknown template: {template_name}. "
            f"Available templates: {', '.join(templates.keys())}"
        )

    return templates[template_name]()


def list_templates() -> Dict[str, str]:
    """
    List all available templates with descriptions.

    Returns:
        Dictionary mapping template names to descriptions
    """
    return {
        "minimal": "Low resource usage (256MB RAM, batch 8)",
        "balanced": "Auto-detected optimal settings (recommended)",
        "high-performance": "Maximum performance (16GB+ RAM, GPU)",
        "low-memory": "Optimized for <2GB RAM systems",
        "docker": "Container-optimized configuration",
    }


def print_template_info(template_name: str):
    """
    Print detailed information about a template.

    Args:
        template_name: Name of the template
    """
    try:
        config = get_template(template_name)
        templates_info = list_templates()

        print(f"\n📝 Template: {template_name}")
        print(f"Description: {templates_info[template_name]}")
        print("\nKey Settings:")
        print(f"  Embedding batch size: {config['embedding']['batch_size']}")
        print(f"  Chunk size: {config['chunking']['chunk_size']}")
        print(f"  Max memory: {config['resource_limits']['max_memory_mb']}MB")
        print(
            f"  Parallel processing: {config['parallel_processing']['enable_parallel_files']}"
        )
        print(f"  Default database: {config['databases']['targets'][0]}")
        print()
    except ValueError as e:
        print(f"Error: {e}")
