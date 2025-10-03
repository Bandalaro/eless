import os
import yaml
import click
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("ELESS.ConfigWizard")


class ConfigWizard:
    """
    Interactive configuration wizard to help users create optimized ELESS configurations
    based on their system specifications and use cases.
    """

    def __init__(self):
        self.config = {}
        self.system_info = self._detect_system_info()

    def _detect_system_info(self) -> Dict[str, Any]:
        """Detect system specifications for optimal configuration suggestions."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            cpu_count = psutil.cpu_count()

            return {
                "total_memory_gb": round(memory.total / (1024**3), 1),
                "available_memory_gb": round(memory.available / (1024**3), 1),
                "total_disk_gb": round(disk.total / (1024**3), 1),
                "free_disk_gb": round(disk.free / (1024**3), 1),
                "cpu_cores": cpu_count,
                "platform": os.name,
            }
        except Exception as e:
            logger.warning(f"Could not detect system info: {e}")
            return {
                "total_memory_gb": 8.0,
                "available_memory_gb": 4.0,
                "total_disk_gb": 256.0,
                "free_disk_gb": 100.0,
                "cpu_cores": 4,
                "platform": "unknown",
            }

    def run_wizard(self) -> Dict[str, Any]:
        """Run the interactive configuration wizard."""
        click.echo("🧙 Welcome to the ELESS Configuration Wizard!")
        click.echo(
            "This wizard will help you create an optimal configuration for your system.\n"
        )

        # Show system info
        self._show_system_info()

        # Gather user preferences
        use_case = self._get_use_case()
        storage_setup = self._get_storage_setup()
        performance_profile = self._get_performance_profile(use_case)
        database_selection = self._get_database_selection()

        # Build configuration
        self.config = self._build_configuration(
            use_case, storage_setup, performance_profile, database_selection
        )

        # Show final configuration
        self._show_final_config()

        return self.config

    def _show_system_info(self):
        """Display detected system information."""
        info = self.system_info
        click.echo("🖥️  System Information Detected:")
        click.echo(
            f"   Memory: {info['total_memory_gb']} GB total, {info['available_memory_gb']} GB available"
        )
        click.echo(
            f"   Storage: {info['free_disk_gb']} GB free of {info['total_disk_gb']} GB total"
        )
        click.echo(f"   CPU Cores: {info['cpu_cores']}")
        click.echo("")

    def _get_use_case(self) -> str:
        """Get user's primary use case."""
        click.echo("📋 What's your primary use case?")
        options = [
            ("personal", "Personal document processing (small to medium collections)"),
            ("business", "Business document processing (medium to large collections)"),
            ("research", "Research/academic work (focus on accuracy and flexibility)"),
            ("production", "Production system (high reliability and performance)"),
            ("development", "Development/testing (frequent changes, debugging)"),
        ]

        for i, (key, desc) in enumerate(options, 1):
            click.echo(f"   {i}. {desc}")

        choice = click.prompt("\nSelect option", type=click.IntRange(1, len(options)))
        return options[choice - 1][0]

    def _get_storage_setup(self) -> Dict[str, str]:
        """Get storage configuration preferences."""
        click.echo("\n💾 Storage Configuration:")

        # Suggest default based on system
        home_dir = Path.home()
        default_base = str(home_dir / "eless_data")

        use_single_dir = click.confirm(
            f"Use a single directory for all ELESS data? (Recommended: {default_base})",
            default=True,
        )

        if use_single_dir:
            data_dir = click.prompt(
                "Data directory path", default=default_base, type=click.Path()
            )
            return {
                "type": "single",
                "data_dir": data_dir,
                "cache_dir": str(Path(data_dir) / ".eless_cache"),
                "log_dir": str(Path(data_dir) / ".eless_logs"),
            }
        else:
            cache_dir = click.prompt(
                "Cache directory (for processed files & vectors)",
                default=str(home_dir / "eless_cache"),
                type=click.Path(),
            )
            log_dir = click.prompt(
                "Log directory", default=str(home_dir / "eless_logs"), type=click.Path()
            )
            return {"type": "separate", "cache_dir": cache_dir, "log_dir": log_dir}

    def _get_performance_profile(self, use_case: str) -> Dict[str, Any]:
        """Determine performance profile based on system and use case."""
        memory_gb = self.system_info["total_memory_gb"]
        cpu_cores = self.system_info["cpu_cores"]

        # Determine profile based on system resources and use case
        if memory_gb < 4 or use_case in ["personal"]:
            profile = "minimal"
        elif memory_gb < 8 or use_case in ["development"]:
            profile = "standard"
        elif use_case in ["production", "business"]:
            profile = "high-performance"
        else:
            profile = "standard"

        # Allow user to override
        click.echo(f"\n⚡ Performance Profile:")
        click.echo(
            f"   Recommended: {profile} (based on {memory_gb}GB RAM, {cpu_cores} cores)"
        )

        profiles = [
            ("minimal", "Minimal resources (2-4GB RAM, slow systems)"),
            ("standard", "Standard setup (4-8GB RAM, typical systems)"),
            ("high-performance", "High performance (8GB+ RAM, powerful systems)"),
            ("custom", "Custom settings (manual configuration)"),
        ]

        click.echo("\nAvailable profiles:")
        for i, (key, desc) in enumerate(profiles, 1):
            marker = " (recommended)" if key == profile else ""
            click.echo(f"   {i}. {desc}{marker}")

        choice = click.prompt("\nSelect profile", type=click.IntRange(1, len(profiles)))
        selected_profile = profiles[choice - 1][0]

        if selected_profile == "custom":
            return self._get_custom_performance()
        else:
            return self._get_predefined_performance(selected_profile)

    def _get_predefined_performance(self, profile: str) -> Dict[str, Any]:
        """Get predefined performance settings."""
        profiles = {
            "minimal": {
                "embedding_batch_size": 8,
                "database_batch_size": 16,
                "chunk_size": 300,
                "chunk_overlap": 30,
                "cache_max_size_mb": 512,
                "cache_max_files": 5000,
                "memory_warning_percent": 70,
                "memory_critical_percent": 85,
            },
            "standard": {
                "embedding_batch_size": 32,
                "database_batch_size": 64,
                "chunk_size": 500,
                "chunk_overlap": 50,
                "cache_max_size_mb": 1024,
                "cache_max_files": 10000,
                "memory_warning_percent": 80,
                "memory_critical_percent": 90,
            },
            "high-performance": {
                "embedding_batch_size": 64,
                "database_batch_size": 128,
                "chunk_size": 750,
                "chunk_overlap": 75,
                "cache_max_size_mb": 4096,
                "cache_max_files": 50000,
                "memory_warning_percent": 85,
                "memory_critical_percent": 95,
            },
        }
        return profiles[profile]

    def _get_custom_performance(self) -> Dict[str, Any]:
        """Get custom performance settings from user."""
        click.echo("\n🔧 Custom Performance Settings:")

        return {
            "embedding_batch_size": click.prompt(
                "Embedding batch size (higher = more memory, faster processing)",
                default=32,
                type=click.IntRange(1, 256),
            ),
            "database_batch_size": click.prompt(
                "Database batch size", default=64, type=click.IntRange(1, 512)
            ),
            "chunk_size": click.prompt(
                "Text chunk size (characters)",
                default=500,
                type=click.IntRange(100, 2000),
            ),
            "chunk_overlap": click.prompt(
                "Chunk overlap (characters)", default=50, type=click.IntRange(0, 500)
            ),
            "cache_max_size_mb": click.prompt(
                "Maximum cache size (MB)", default=1024, type=click.IntRange(100, 10000)
            ),
        }

    def _get_database_selection(self) -> List[str]:
        """Get user's database preferences."""
        click.echo("\n🗄️  Database Selection:")
        click.echo("Select which databases you want to use for storing embeddings:")

        databases = [
            ("chroma", "ChromaDB - Easy to use, good for getting started"),
            ("faiss", "FAISS - High performance, good for large collections"),
            ("qdrant", "Qdrant - Feature-rich, cloud-ready"),
            ("postgresql", "PostgreSQL - If you already have a database"),
            ("cassandra", "Cassandra - For distributed, high-scale deployments"),
        ]

        selected = []
        for i, (key, desc) in enumerate(databases, 1):
            marker = " (recommended)" if key == "chroma" else ""
            default_select = key == "chroma"
            if click.confirm(f"   {i}. {desc}{marker}", default=default_select):
                selected.append(key)

        if not selected:
            click.echo(
                "At least one database is required. Selecting ChromaDB as default."
            )
            selected = ["chroma"]

        return selected

    def _build_configuration(
        self, use_case: str, storage: Dict, performance: Dict, databases: List[str]
    ) -> Dict[str, Any]:
        """Build the final configuration dictionary."""
        config = {
            # Cache configuration
            "cache": {
                "directory": storage.get("cache_dir", ".eless_cache"),
                "manifest_file": "manifest.json",
                "max_size_mb": performance["cache_max_size_mb"],
                "max_files": performance.get("cache_max_files", 10000),
                "auto_cleanup": True,
            },
            # Logging configuration
            "logging": {
                "directory": storage.get("log_dir", ".eless_logs"),
                "level": "DEBUG" if use_case == "development" else "INFO",
                "enable_console": True,
                "max_file_size_mb": 10,
                "backup_count": 5,
            },
            # Embedding configuration
            "embedding": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "dimensions": 384,
                "device": "cpu",  # TODO: Detect GPU availability
                "batch_size": performance["embedding_batch_size"],
                "trust_remote_code": False,
            },
            # Resource limits
            "resource_limits": {
                "memory_warning_percent": performance["memory_warning_percent"],
                "memory_critical_percent": performance["memory_critical_percent"],
                "cpu_high_percent": 85,
                "min_memory_mb": 256,
                "enable_adaptive_batching": True,
            },
            # Chunking configuration
            "chunking": {
                "chunk_size": performance["chunk_size"],
                "chunk_overlap": performance["chunk_overlap"],
            },
            # Database configuration
            "databases": {
                "batch_size": performance["database_batch_size"],
                "targets": databases,
                "default": {"drop_existing": False},
                "connections": self._build_database_connections(storage, databases),
            },
        }

        return config

    def _build_database_connections(
        self, storage: Dict, databases: List[str]
    ) -> Dict[str, Any]:
        """Build database connection configurations."""
        base_dir = storage.get("data_dir", ".")
        connections = {}

        for db in databases:
            if db == "chroma":
                connections[db] = {
                    "type": "chroma",
                    "path": str(Path(base_dir) / ".eless_chroma"),
                }
            elif db == "faiss":
                faiss_dir = Path(base_dir) / ".eless_faiss"
                connections[db] = {
                    "type": "faiss",
                    "index_path": str(faiss_dir / "index.faiss"),
                    "metadata_path": str(faiss_dir / "metadata.json"),
                }
            elif db == "qdrant":
                connections[db] = {
                    "type": "qdrant",
                    "host": "localhost",
                    "port": 6333,
                    "api_key": None,
                    "collection_name": "eless_embeddings",
                    "timeout": 30,
                }
            elif db == "postgresql":
                connections[db] = {
                    "type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "user": "eless_user",
                    "password": "change_me",
                    "database": "eless_db",
                    "table_name": "eless_embeddings",
                    "connection_timeout": 30,
                }
            elif db == "cassandra":
                connections[db] = {
                    "type": "cassandra",
                    "hosts": ["localhost"],
                    "port": 9042,
                    "keyspace": "eless_keyspace",
                    "table_name": "eless_embeddings",
                    "replication_factor": 1,
                }

        return connections

    def _show_final_config(self):
        """Display the final configuration to the user."""
        click.echo("\n✨ Configuration Generated!")
        click.echo("\nKey settings:")
        click.echo(f"   Storage: {self.config['cache']['directory']}")
        click.echo(f"   Cache limit: {self.config['cache']['max_size_mb']} MB")
        click.echo(f"   Embedding batch size: {self.config['embedding']['batch_size']}")
        click.echo(f"   Chunk size: {self.config['chunking']['chunk_size']} characters")
        click.echo(f"   Databases: {', '.join(self.config['databases']['targets'])}")
        click.echo(
            f"   Memory warning: {self.config['resource_limits']['memory_warning_percent']}%"
        )

    def save_config(self, output_path: Path) -> bool:
        """Save the configuration to a YAML file."""
        try:
            # Create directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)

            click.echo(f"\n💾 Configuration saved to: {output_path}")
            click.echo("\nTo use this configuration:")
            click.echo(f"   eless --config {output_path} process your_documents/")
            return True

        except Exception as e:
            click.secho(f"Error saving configuration: {e}", fg="red")
            return False


def generate_preset_config(preset: str) -> Dict[str, Any]:
    """Generate a preset configuration for different use cases."""
    presets = {
        "minimal": {
            "description": "Low-resource systems (2-4GB RAM)",
            "config": {
                "cache": {"max_size_mb": 512, "max_files": 5000},
                "embedding": {"batch_size": 8},
                "databases": {"batch_size": 16, "targets": ["chroma"]},
                "chunking": {"chunk_size": 300, "chunk_overlap": 30},
                "resource_limits": {
                    "memory_warning_percent": 70,
                    "memory_critical_percent": 85,
                },
            },
        },
        "standard": {
            "description": "Standard systems (4-8GB RAM)",
            "config": {
                "cache": {"max_size_mb": 1024, "max_files": 10000},
                "embedding": {"batch_size": 32},
                "databases": {"batch_size": 64, "targets": ["chroma"]},
                "chunking": {"chunk_size": 500, "chunk_overlap": 50},
                "resource_limits": {
                    "memory_warning_percent": 80,
                    "memory_critical_percent": 90,
                },
            },
        },
        "high-end": {
            "description": "High-performance systems (8GB+ RAM)",
            "config": {
                "cache": {"max_size_mb": 4096, "max_files": 50000},
                "embedding": {"batch_size": 64},
                "databases": {"batch_size": 128, "targets": ["chroma", "faiss"]},
                "chunking": {"chunk_size": 750, "chunk_overlap": 75},
                "resource_limits": {
                    "memory_warning_percent": 85,
                    "memory_critical_percent": 95,
                },
            },
        },
        "docker": {
            "description": "Container/Docker deployments",
            "config": {
                "cache": {"directory": "/data/cache", "max_size_mb": 2048},
                "logging": {"directory": "/data/logs"},
                "embedding": {"batch_size": 32},
                "databases": {
                    "batch_size": 64,
                    "targets": ["qdrant"],
                    "connections": {
                        "qdrant": {"type": "qdrant", "host": "qdrant", "port": 6333}
                    },
                },
            },
        },
    }

    if preset not in presets:
        raise ValueError(f"Unknown preset: {preset}. Available: {list(presets.keys())}")

    # Merge with base configuration
    from .default_config import get_default_config

    base_config = get_default_config()

    # Deep merge preset config over base
    preset_config = presets[preset]["config"]
    for key, value in preset_config.items():
        if isinstance(value, dict) and key in base_config:
            base_config[key].update(value)
        else:
            base_config[key] = value

    return base_config
