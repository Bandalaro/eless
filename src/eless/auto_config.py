"""
Auto-configuration system for ELESS.
Detects system resources and generates optimal configuration.
"""

import psutil
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger("ELESS.AutoConfig")


def detect_system_resources() -> Dict[str, Any]:
    """
    Detect and return system resource information.

    Returns:
        Dict with system resource details
    """
    try:
        ram_total = psutil.virtual_memory().total / (1024**3)
        ram_available = psutil.virtual_memory().available / (1024**3)
        cpu_count = psutil.cpu_count()

        # Check GPU availability
        gpu_available = False
        try:
            import torch

            gpu_available = torch.cuda.is_available()
        except ImportError:
            pass

        # Disk space
        try:
            disk_free = psutil.disk_usage(str(Path.home())).free / (1024**3)
        except:
            disk_free = 0

        return {
            "ram_total_gb": round(ram_total, 2),
            "ram_available_gb": round(ram_available, 2),
            "cpu_count": cpu_count,
            "gpu_available": gpu_available,
            "disk_free_gb": round(disk_free, 2),
        }
    except Exception as e:
        logger.warning(f"Failed to detect system resources: {e}")
        return {
            "ram_total_gb": 4.0,
            "ram_available_gb": 2.0,
            "cpu_count": 2,
            "gpu_available": False,
            "disk_free_gb": 10.0,
        }


def calculate_optimal_batch_size(
    ram_available_gb: float, model_size_mb: int = 80
) -> int:
    """
    Calculate optimal batch size based on available RAM.

    Args:
        ram_available_gb: Available RAM in GB
        model_size_mb: Size of the embedding model in MB

    Returns:
        Optimal batch size
    """
    # Conservative estimate: each batch item uses ~2MB for processing
    available_for_batching = (ram_available_gb * 0.3 * 1024) - model_size_mb
    optimal_batch = int(available_for_batching / 2)

    # Clamp to reasonable values (8 to 128)
    return max(8, min(optimal_batch, 128))


def calculate_worker_count(cpu_count: int) -> int:
    """
    Calculate optimal number of workers based on CPU count.

    Args:
        cpu_count: Number of CPU cores

    Returns:
        Optimal worker count
    """
    if cpu_count <= 2:
        return 1
    elif cpu_count <= 4:
        return 2
    else:
        return min(cpu_count - 1, 8)


def generate_auto_config() -> Dict[str, Any]:
    """
    Generate optimal configuration based on system resources.

    Returns:
        Configuration dictionary
    """
    resources = detect_system_resources()

    logger.info(
        f"Detected system: {resources['ram_available_gb']}GB RAM, "
        f"{resources['cpu_count']} CPUs, GPU: {resources['gpu_available']}"
    )

    # Calculate optimal settings
    batch_size = calculate_optimal_batch_size(resources["ram_available_gb"])
    worker_count = calculate_worker_count(resources["cpu_count"])

    # Determine memory limit (use 50% of available RAM)
    max_memory_mb = int(resources["ram_available_gb"] * 0.5 * 1024)

    # Base configuration
    config = {
        "embedding": {
            "model_name": "all-MiniLM-L6-v2",
            "device": "cuda" if resources["gpu_available"] else "cpu",
            "batch_size": batch_size,
        },
        "resource_limits": {
            "max_memory_mb": max_memory_mb,
            "enable_adaptive_batching": True,
            "max_cpu_percent": 80,
        },
        "parallel": {
            "enable_parallel_files": resources["cpu_count"] > 2,
            "enable_parallel_chunks": False,  # Conservative default
            "max_workers": worker_count,
            "mode": "thread",
        },
        "streaming": {
            "buffer_size": 8192,
            "max_file_size_mb": 100,
            "auto_streaming_threshold": (
                0.7 if resources["ram_available_gb"] < 4 else 0.8
            ),
        },
        "logging": {
            "level": "INFO",
            "enable_console": True,
            "directory": ".eless_logs",
        },
    }

    return config


def get_preset_config(preset_name: str) -> Dict[str, Any]:
    """
    Get a preset configuration.

    Args:
        preset_name: Name of preset (minimal, balanced, performance)

    Returns:
        Configuration dictionary
    """
    presets = {
        "minimal": {
            "embedding": {
                "batch_size": 8,
                "device": "cpu",
            },
            "resource_limits": {
                "max_memory_mb": 256,
                "enable_adaptive_batching": True,
            },
            "streaming": {
                "auto_streaming_threshold": 0.5,
            },
        },
        "balanced": generate_auto_config(),
        "performance": {
            "embedding": {
                "batch_size": 64,
                "device": "cuda",
            },
            "resource_limits": {
                "max_memory_mb": 4096,
                "enable_adaptive_batching": True,
            },
            "parallel": {
                "enable_parallel_files": True,
                "max_workers": 8,
            },
        },
    }

    return presets.get(preset_name, presets["balanced"])


def print_system_info():
    """Print system information in a user-friendly format."""
    resources = detect_system_resources()

    print("\n📊 System Information:")
    print(
        f"  RAM: {resources['ram_available_gb']:.1f}GB available / {resources['ram_total_gb']:.1f}GB total"
    )
    print(f"  CPU: {resources['cpu_count']} cores")
    print(
        f"  GPU: {'✓ Available' if resources['gpu_available'] else '✗ Not available'}"
    )
    print(f"  Disk: {resources['disk_free_gb']:.1f}GB free")

    config = generate_auto_config()
    print(f"\n⚙️  Recommended Settings:")
    print(f"  Batch size: {config['embedding']['batch_size']}")
    print(f"  Device: {config['embedding']['device']}")
    print(f"  Workers: {config['parallel']['max_workers']}")
    print(f"  Memory limit: {config['resource_limits']['max_memory_mb']}MB")
    print()


if __name__ == "__main__":
    # Test auto-configuration
    print_system_info()
