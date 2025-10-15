import unittest
import tempfile
import shutil
from pathlib import Path
import yaml
import json
import os
from copy import deepcopy
from unittest.mock import patch

from src.core.config_loader import ConfigLoader
from src.core.state_manager import StateManager
from src.core.resource_monitor import ResourceMonitor

class TestConfigValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup test environment."""
        # Load base test configuration
        config_path = Path(__file__).parent / 'fixtures' / 'test_config.yaml'
        with open(config_path, 'r') as f:
            cls.base_config = yaml.safe_load(f)
        
        # Create temp directories
        cls.temp_dir = tempfile.mkdtemp(prefix='eless_config_test_')

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        """Setup for each test."""
        self.config = deepcopy(self.base_config)
        self.config_loader = ConfigLoader()

    def save_config(self, config, name='test_config.yaml'):
        """Helper to save config to file."""
        config_path = Path(self.temp_dir) / name
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        return config_path

    def test_minimal_config(self):
        """Test minimal valid configuration."""
        minimal_config = {
            'embedding': {
                'batch_size': 32,
                'model': 'all-MiniLM-L6-v2'
            },
            'chunking': {
                'chunk_size': 512,
                'chunk_overlap': 128
            },
            'cache': {
                'directory': self.temp_dir,
                'manifest_file': 'manifest.json'
            },
            'database': {
                'type': 'sqlite',
                'path': str(Path(self.temp_dir) / 'test.db')
            },
            'logging': {
                'level': 'INFO',
                'directory': str(Path(self.temp_dir) / 'logs')
            }
        }
        
        # Create required directories
        Path(minimal_config['cache']['directory']).mkdir(exist_ok=True)
        Path(minimal_config['logging']['directory']).mkdir(exist_ok=True)
        
        config_path = self.save_config(minimal_config)
        loaded_config = self.config_loader.load_config(config_path)
        self.assertIsNotNone(loaded_config)
        
        # Validate the loaded config
        self.config_loader.validate_config(loaded_config)

    def test_invalid_parallel_config(self):
        """Test invalid parallel processing configuration."""
        # Test invalid worker count
        self.config['parallel_processing']['max_workers'] = -1
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

        # Test invalid mode
        self.config['parallel_processing']['mode'] = 'invalid_mode'
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

    def test_invalid_embedding_config(self):
        """Test invalid embedding configuration."""
        # Test missing required fields
        del self.config['embedding']['batch_size']
        with self.assertRaises(KeyError):
            self.config_loader.validate_config(self.config)

        # Test invalid batch size
        self.config['embedding']['batch_size'] = 0
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

    def test_invalid_resource_limits(self):
        """Test invalid resource limit configuration."""
        # Test invalid memory thresholds
        self.config['resource_limits']['memory_warning_percent'] = 101
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

        # Test invalid memory configuration
        self.config['resource_limits']['min_memory_mb'] = -1
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

    def test_invalid_cache_config(self):
        """Test invalid cache configuration."""
        # Test invalid directory
        self.config['cache']['directory'] = '/nonexistent/directory'
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

        # Test invalid retention period
        self.config['cache']['retention_days'] = 0
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

    def test_invalid_database_config(self):
        """Test invalid database configuration."""
        # Test unsupported database type
        self.config['databases']['targets'] = ['unsupported_db']
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

        # Test invalid batch size
        self.config['databases']['batch_size'] = -1
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

    def test_config_dependencies(self):
        """Test configuration dependencies and relationships."""
        # Test chunking vs batch size relationship
        self.config['chunking']['chunk_size'] = 1000
        self.config['embedding']['batch_size'] = 2000
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

        # Test memory limits relationship
        self.config['resource_limits']['memory_warning_percent'] = 90
        self.config['resource_limits']['memory_critical_percent'] = 80
        with self.assertRaises(ValueError):
            self.config_loader.validate_config(self.config)

    def test_config_type_validation(self):
        """Test configuration value type validation."""
        test_cases = [
            ('parallel_processing.max_workers', 'string'),  # Should be int
            ('embedding.normalize', 'string'),  # Should be bool
            ('chunking.chunk_size', '512'),  # Should be int
            ('resource_limits.memory_warning_percent', '80'),  # Should be int/float
        ]

        for path, invalid_value in test_cases:
            config = deepcopy(self.config)
            parts = path.split('.')
            target = config
            for part in parts[:-1]:
                target = target[part]
            target[parts[-1]] = invalid_value

            with self.assertRaises(TypeError):
                self.config_loader.validate_config(config)

    def test_config_value_ranges(self):
        """Test configuration value range validation."""
        test_cases = [
            ('parallel_processing.max_workers', 100),  # Too many workers
            ('chunking.chunk_size', 1000000),  # Too large chunk
            ('chunking.chunk_overlap', -10),  # Negative overlap
            ('resource_limits.memory_warning_percent', 150),  # Invalid percentage
        ]

        for path, invalid_value in test_cases:
            config = deepcopy(self.config)
            parts = path.split('.')
            target = config
            for part in parts[:-1]:
                target = target[part]
            target[parts[-1]] = invalid_value

            with self.assertRaises(ValueError):
                self.config_loader.validate_config(config)

    def test_config_file_formats(self):
        """Test different configuration file formats."""
        # Test YAML format
        yaml_config = self.save_config(self.config, 'config.yaml')
        self.assertIsNotNone(self.config_loader.load_config(yaml_config))

        # Test JSON format
        json_path = Path(self.temp_dir) / 'config.json'
        with open(json_path, 'w') as f:
            json.dump(self.config, f)
        self.assertIsNotNone(self.config_loader.load_config(json_path))

    def test_config_environment_variables(self):
        """Test configuration with environment variables."""
        # Set environment variables
        os.environ['ELESS_CACHE_DIR'] = '/custom/cache/dir'
        os.environ['ELESS_DB_PATH'] = '/custom/db/path'
        os.environ['ELESS_MAX_WORKERS'] = '4'

        # Save test config
        config_path = self.save_config(self.config)

        # Load config with environment variable support
        config = self.config_loader.load_config_with_env(config_path)

        # Verify environment variables were applied
        self.assertEqual(config['cache']['directory'], '/custom/cache/dir')
        self.assertEqual(config['database']['path'], '/custom/db/path')
        self.assertEqual(config['parallel_processing']['max_workers'], 4)

        # Clean up
        del os.environ['ELESS_CACHE_DIR']
        del os.environ['ELESS_DB_PATH']
        del os.environ['ELESS_MAX_WORKERS']

    def test_config_merge(self):
        """Test configuration merging."""
        # Create base config
        base_config = {
            'embedding': {'batch_size': 32},
            'chunking': {'chunk_size': 512}
        }

        # Create override config
        override_config = {
            'embedding': {'batch_size': 64},
            'database': {'type': 'sqlite'}
        }

        # Merge configs
        merged_config = self.config_loader.merge_configs(base_config, override_config)

        # Verify merge results
        self.assertEqual(merged_config['embedding']['batch_size'], 64)  # Override
        self.assertEqual(merged_config['chunking']['chunk_size'], 512)  # Base preserved
        self.assertEqual(merged_config['database']['type'], 'sqlite')  # New section

    def test_config_defaults(self):
        """Test default configuration values."""
        # Load minimal config
        minimal_config = {
            'embedding': {
                'model': 'all-MiniLM-L6-v2'
            }
        }

        # Load with defaults
        config = self.config_loader.load_with_defaults(minimal_config)

        # Verify defaults were applied
        self.assertIn('batch_size', config['embedding'])
        self.assertIn('chunking', config)
        self.assertIn('parallel_processing', config)
        self.assertIn('resource_limits', config)

if __name__ == '__main__':
    unittest.main()


