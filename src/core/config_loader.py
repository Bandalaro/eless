import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from functools import reduce

from .default_config import get_default_config

logger = logging.getLogger('ELESS.Config')

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
                logger.warning(f"Configuration file not found at {default_config_path}, using embedded defaults")
            else:
                logger.info("Using embedded default configuration")

    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """Loads a YAML file from a given path."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found at: {path}")
            if path == self.default_config_path:
                raise FileNotFoundError(f"CRITICAL: Default configuration file missing at {path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {path}: {e}")
            raise

    def get_final_config(self, user_config_path: Optional[str] = None, **cli_args) -> Dict[str, Any]:
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
                logger.warning(f"User config file not found at: {user_config_path}. Skipping merge.")

        # 3. Merge CLI Arguments (Highest Priority)        
        cli_overrides = {}
        if cli_args:
            if 'chunk_size' in cli_args:
                cli_overrides['chunking'] = {'chunk_size': cli_args['chunk_size']}
            
            final_config = deep_merge(final_config, cli_overrides)
            if cli_overrides:
                logger.info("Applied overrides from CLI arguments.")
            
        return final_config