"""
Health check system for ELESS.
Diagnoses installation and configuration issues.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger("ELESS.HealthCheck")


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version >= (3, 8):
        return True, f"Python {version.major}.{version.minor}.{version.micro} ✓"
    return False, f"Python {version.major}.{version.minor} (3.8+ required)"


def check_core_dependencies() -> Tuple[bool, str]:
    """Check if core dependencies are installed."""
    required = ["click", "yaml", "numpy", "psutil"]
    missing = []

    for dep in required:
        try:
            if dep == "yaml":
                __import__("yaml")
            else:
                __import__(dep)
        except ImportError:
            missing.append(dep)

    if not missing:
        return True, "All core dependencies installed ✓"
    return False, f"Missing: {', '.join(missing)}"


def check_embedding_model() -> Tuple[bool, str]:
    """Check if sentence-transformers is available."""
    try:
        from sentence_transformers import SentenceTransformer

        return True, "sentence-transformers available ✓"
    except ImportError:
        return False, "Not installed (pip install sentence-transformers)"


def check_database(db_name: str, import_name: str) -> Tuple[bool, str]:
    """Check if a database connector is available."""
    try:
        if db_name == "chromadb":
            __import__("chromadb")
            __import__("langchain_community")
        else:
            __import__(import_name)
        return True, f"{db_name} installed ✓"
    except ImportError:
        install_cmd = {
            "chromadb": "pip install chromadb langchain-community",
            "qdrant": "pip install qdrant-client",
            "faiss": "pip install faiss-cpu",
            "psycopg2": "pip install psycopg2-binary",
            "cassandra": "pip install cassandra-driver",
        }
        return (
            False,
            f"Not installed ({install_cmd.get(import_name, f'pip install {import_name}')})",
        )


def check_disk_space() -> Tuple[bool, str]:
    """Check available disk space."""
    try:
        import psutil

        home = Path.home()
        usage = psutil.disk_usage(str(home))
        free_gb = usage.free / (1024**3)

        if free_gb > 5:
            return True, f"{free_gb:.1f}GB available ✓"
        elif free_gb > 1:
            return True, f"{free_gb:.1f}GB available (low)"
        else:
            return False, f"{free_gb:.1f}GB available (critically low)"
    except Exception as e:
        return False, f"Could not check ({str(e)})"


def check_memory() -> Tuple[bool, str]:
    """Check available memory."""
    try:
        import psutil

        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024**3)
        total_gb = mem.total / (1024**3)

        if available_gb > 2:
            return True, f"{available_gb:.1f}GB / {total_gb:.1f}GB available ✓"
        elif available_gb > 0.5:
            return True, f"{available_gb:.1f}GB / {total_gb:.1f}GB available (low)"
        else:
            return (
                False,
                f"{available_gb:.1f}GB / {total_gb:.1f}GB available (critically low)",
            )
    except Exception as e:
        return False, f"Could not check ({str(e)})"


def check_configuration() -> Tuple[bool, str]:
    """Check if configuration file exists and is valid."""
    try:
        from .core.config_loader import ConfigLoader
        from .core.default_config import get_default_config

        # Try to get default config
        config = get_default_config()
        required_keys = ["cache", "chunking", "embedding"]

        for key in required_keys:
            if key not in config:
                return False, f"Missing '{key}' section in config"

        return True, "Configuration valid ✓"
    except Exception as e:
        return False, f"Could not load config: {str(e)}"


def run_health_check(verbose: bool = False) -> Dict[str, Tuple[bool, str]]:
    """
    Run comprehensive health check.

    Args:
        verbose: Print detailed output

    Returns:
        Dict of check results
    """
    checks = {
        "Python version": check_python_version(),
        "Core dependencies": check_core_dependencies(),
        "Embedding model": check_embedding_model(),
        "ChromaDB": check_database("chromadb", "chromadb"),
        "Qdrant": check_database("qdrant", "qdrant_client"),
        "FAISS": check_database("faiss", "faiss"),
        "Disk space": check_disk_space(),
        "Memory": check_memory(),
        "Configuration": check_configuration(),
    }

    if verbose:
        print("\n" + "=" * 60)
        print("🏥 ELESS Health Check")
        print("=" * 60 + "\n")

        max_len = max(len(name) for name in checks.keys())

        for name, (ok, message) in checks.items():
            status = "✓" if ok else "✗"
            status_color = "\033[92m" if ok else "\033[91m"  # Green or Red
            reset_color = "\033[0m"

            print(f"{name:<{max_len}} : {status_color}{status}{reset_color} {message}")

        # Overall status
        all_critical_ok = all(
            ok
            for name, (ok, _) in checks.items()
            if name in ["Python version", "Core dependencies", "Configuration"]
        )

        print("\n" + "=" * 60)
        if all_critical_ok:
            print("✓ Overall health: Good")
            print("  ELESS is ready to use!")
        else:
            print("✗ Issues found")
            print("  Please fix critical issues above.")
        print("=" * 60 + "\n")

        # Recommendations
        if not checks["Embedding model"][0]:
            print("💡 To use embeddings: pip install sentence-transformers")

        any_db = any(checks[db][0] for db in ["ChromaDB", "Qdrant", "FAISS"])
        if not any_db:
            print("💡 No databases installed. Install at least one:")
            print("   pip install chromadb  # Recommended for beginners")

        print()

    return checks


def quick_check() -> bool:
    """
    Quick health check returning True if system is ready.

    Returns:
        bool: True if system is ready to use
    """
    checks = run_health_check(verbose=False)

    # Check critical components
    critical = ["Python version", "Core dependencies"]
    return all(checks[name][0] for name in critical)


if __name__ == "__main__":
    # Run health check when module is executed directly
    run_health_check(verbose=True)
