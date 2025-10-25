import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from functools import reduce

from .default_config import get_default_config

logger = logging.getLogger("ELESS.Config")

# --- Helper Functions for Deep Merging ---


def deep_merge(target: Dict, source: Dict) -> Dict:
    """Recursively merges source dictionary into target dictionary."""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target


# --- Core Configuration Loader ---


class ConfigLoader:
    """Handles loading the default configuration and merging it with user overrides."""

    def __init__(self, default_config_path: Optional[Path] = None):
        self.default_config_path = default_config_path
        if default_config_path and default_config_path.exists():
            self._default_config = self._load_yaml_file(default_config_path)
            logger.info(f"Loaded configuration from: {default_config_path}")
        else:
            # Use embedded default configuration
            self._default_config = get_default_config()
            if default_config_path:
                logger.warning(
                    f"Configuration file not found at {default_config_path}, using embedded defaults"
                )
            else:
                logger.info("Using embedded default configuration")

    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """Loads a YAML file from a given path."""
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found at: {path}")
            if path == self.default_config_path:
                raise FileNotFoundError(
                    f"CRITICAL: Default configuration file missing at {path}"
                )
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {path}: {e}")
            raise

    def get_final_config(
        self, user_config_path: Optional[str] = None, **cli_args
    ) -> Dict[str, Any]:
        """
        Loads and merges default config, user config, and CLI arguments.

        The hierarchy of overrides is:
        1. Default Config (Lowest Priority)
        2. User Custom Config File
        3. CLI Arguments (Highest Priority)
        """

        # 1. Start with a deep copy of the default config
        final_config = self._default_config.copy()

        # 2. Load and merge user config if provided
        if user_config_path:
            user_path = Path(user_config_path)
            if user_path.exists():
                user_config = self._load_yaml_file(user_path)
                final_config = deep_merge(final_config, user_config)
                logger.info(f"Merged settings from user config: {user_config_path}")
            else:
                logger.warning(
                    f"User config file not found at: {user_config_path}. Skipping merge."
                )

        # 3. Merge CLI Arguments (Highest Priority)
        cli_overrides = {}
        if cli_args:
            if "chunk_size" in cli_args:
                cli_overrides["chunking"] = {"chunk_size": cli_args["chunk_size"]}

            final_config = deep_merge(final_config, cli_overrides)
            if cli_overrides:
                logger.info("Applied overrides from CLI arguments.")

        return final_config

    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from a file."""
        return self._load_yaml_file(config_path)

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration values and relationships."""
        # Validate parallel processing config
        parallel = config.get("parallel_processing", {})
        if "max_workers" in parallel:
            if not isinstance(parallel["max_workers"], int):
                raise TypeError("max_workers must be an integer")
            if parallel["max_workers"] < 1:
                raise ValueError("max_workers must be greater than 0")
            if parallel["max_workers"] > 64:
                raise ValueError("max_workers must be less than or equal to 64")
        if "mode" in parallel and parallel["mode"] not in ["thread", "process", "auto"]:
            raise ValueError(
                "parallel processing mode must be 'thread', 'process', or 'auto'"
            )

        # Validate embedding config
        embedding = config.get("embedding", {})
        if "batch_size" not in embedding:
            raise KeyError("embedding.batch_size is required")
        if not isinstance(embedding["batch_size"], int):
            raise TypeError("embedding.batch_size must be an integer")
        if embedding["batch_size"] < 1:
            raise ValueError("embedding batch_size must be greater than 0")
        if "normalize" in embedding and not isinstance(embedding["normalize"], bool):
            raise TypeError("embedding.normalize must be a boolean")

        # Validate resource limits
        limits = config.get("resource_limits", {})
        if "memory_warning_percent" in limits:
            if not isinstance(limits["memory_warning_percent"], (int, float)):
                raise TypeError("memory_warning_percent must be a number")
            if not 0 <= limits["memory_warning_percent"] <= 100:
                raise ValueError("memory_warning_percent must be between 0 and 100")
        if "min_memory_mb" in limits:
            if not isinstance(limits["min_memory_mb"], (int, float)):
                raise TypeError("min_memory_mb must be a number")
            if limits["min_memory_mb"] < 0:
                raise ValueError("min_memory_mb cannot be negative")

        # Validate chunking config
        chunking = config.get("chunking", {})
        if "chunk_size" in chunking:
            if not isinstance(chunking["chunk_size"], int):
                raise TypeError("chunk_size must be an integer")
            if chunking["chunk_size"] > 10000:
                raise ValueError("chunk_size must be less than or equal to 10000")
        if "chunk_overlap" in chunking:
            if not isinstance(chunking["chunk_overlap"], int):
                raise TypeError("chunk_overlap must be an integer")
            if chunking["chunk_overlap"] < 0:
                raise ValueError("chunk_overlap must be greater than or equal to 0")

        # Validate chunking vs batch size relationship
        if (
            "chunk_size" in chunking
            and "batch_size" in embedding
            and chunking["chunk_size"] < embedding["batch_size"]
        ):
            raise ValueError("chunk_size must be greater than or equal to batch_size")

        # Validate cache config
        cache = config.get("cache", {})
        if "directory" in cache and not Path(cache["directory"]).parent.exists():
            raise ValueError(
                f"Parent directory for cache does not exist: {cache['directory']}"
            )
        if "retention_days" in cache and cache["retention_days"] < 1:
            raise ValueError("retention_days must be greater than 0")

        # Validate databases config
        databases = config.get("databases", {})
        if "batch_size" in databases:
            if not isinstance(databases["batch_size"], int):
                raise TypeError("databases.batch_size must be an integer")
            if databases["batch_size"] < 1:
                raise ValueError("databases batch_size must be greater than 0")
        if "targets" in databases:
            for target in databases["targets"]:
                if target not in [
                    "sqlite",
                    "postgresql",
                    "chroma",
                    "faiss",
                    "qdrant",
                    "cassandra",
                ]:
                    raise ValueError(f"Unsupported database type: {target}")

    def merge_configs(
        self, base_config: Dict[str, Any], override_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge two configurations with override taking precedence."""
        merged = base_config.copy()
        return deep_merge(merged, override_config)

    def load_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load configuration with default values for missing fields."""
        # Start with default configuration
        final_config = get_default_config()

        # Merge provided config
        return self.merge_configs(final_config, config)

    def load_config_with_env(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration with environment variable support."""
        # Load base configuration
        config = self.load_config(config_path)

        # Environment variable mapping
        env_mapping = {
            "ELESS_CACHE_DIR": ("cache", "directory"),
            "ELESS_DB_PATH": ("database", "path"),
            "ELESS_MAX_WORKERS": ("parallel_processing", "max_workers"),
        }

        # Apply environment variables
        for env_var, (section, key) in env_mapping.items():
            if env_var in os.environ:
                if section not in config:
                    config[section] = {}
                if key == "max_workers":
                    config[section][key] = int(os.environ[env_var])
                else:
                    config[section][key] = os.environ[env_var]

        return config
