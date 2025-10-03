import unittest
import tempfile
import shutil
import os
from pathlib import Path
import subprocess
import yaml
import json
from click.testing import CliRunner

from src.cli import cli

class TestCLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup test environment."""
        # Create temporary test directory
        cls.temp_dir = tempfile.mkdtemp(prefix='eless_cli_test_')
        
        # Load test configuration
        config_path = Path(__file__).parent / 'fixtures' / 'test_config.yaml'
        with open(config_path, 'r') as f:
            cls.config = yaml.safe_load(f)
        
        # Create temp directories for cache and database
        cls.cache_dir = tempfile.mkdtemp(prefix='eless_cli_cache_')
        cls.db_dir = tempfile.mkdtemp(prefix='eless_cli_db_')
        
        # Update config paths
        cls.config['cache']['directory'] = cls.cache_dir
        cls.config['database']['path'] = str(Path(cls.db_dir) / 'test.db')
        
        # Save modified config
        cls.config_path = Path(cls.temp_dir) / 'config.yaml'
        with open(cls.config_path, 'w') as f:
            yaml.dump(cls.config, f)
            
        # Setup test files
        cls.fixtures_dir = Path(__file__).parent / 'fixtures'
        cls.test_file = Path(cls.temp_dir) / 'sample.txt'
        shutil.copy(cls.fixtures_dir / 'sample.txt', cls.test_file)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        shutil.rmtree(cls.cache_dir, ignore_errors=True)
        shutil.rmtree(cls.db_dir, ignore_errors=True)

    def setUp(self):
        """Setup for each test."""
        self.runner = CliRunner()

    def test_cli_version(self):
        """Test version command."""
        result = self.runner.invoke(cli, ['version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('ELESS version', result.output)

    def test_cli_process(self):
        """Test process command."""
        # Test with config file
        result = self.runner.invoke(cli, [
            'process',
            '--config', str(self.config_path),
            str(self.test_file)
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Processing completed', result.output)

        # Test with directory input
        test_dir = Path(self.temp_dir) / 'test_dir'
        test_dir.mkdir(exist_ok=True)
        shutil.copy(self.test_file, test_dir / 'file1.txt')
        shutil.copy(self.test_file, test_dir / 'file2.txt')

        result = self.runner.invoke(cli, [
            'process',
            '--config', str(self.config_path),
            str(test_dir)
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Processing completed', result.output)

    def test_cli_resume(self):
        """Test resume command."""
        # First process a file
        self.runner.invoke(cli, [
            'process',
            '--config', str(self.config_path),
            str(self.test_file)
        ])

        # Then test resume
        result = self.runner.invoke(cli, [
            'resume',
            '--config', str(self.config_path)
        ])
        self.assertEqual(result.exit_code, 0)

    def test_cli_status(self):
        """Test status command."""
        # Process a file first
        self.runner.invoke(cli, [
            'process',
            '--config', str(self.config_path),
            str(self.test_file)
        ])

        # Check status
        result = self.runner.invoke(cli, [
            'status',
            '--config', str(self.config_path)
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Status Report', result.output)

    def test_cli_config(self):
        """Test config command."""
        # Test config show
        result = self.runner.invoke(cli, [
            'config',
            'show',
            '--config', str(self.config_path)
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Configuration', result.output)

        # Test config validate
        result = self.runner.invoke(cli, [
            'config',
            'validate',
            '--config', str(self.config_path)
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Configuration is valid', result.output)

    def test_cli_error_handling(self):
        """Test CLI error handling."""
        # Test with non-existent file
        result = self.runner.invoke(cli, [
            'process',
            '--config', str(self.config_path),
            'non_existent_file.txt'
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Error', result.output)

        # Test with invalid config
        invalid_config = Path(self.temp_dir) / 'invalid_config.yaml'
        with open(invalid_config, 'w') as f:
            f.write('invalid: yaml: content')

        result = self.runner.invoke(cli, [
            'process',
            '--config', str(invalid_config),
            str(self.test_file)
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Error', result.output)

    def test_cli_verbose_mode(self):
        """Test verbose mode."""
        result = self.runner.invoke(cli, [
            'process',
            '--config', str(self.config_path),
            '--verbose',
            str(self.test_file)
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('DEBUG', result.output)

    def test_cli_batch_processing(self):
        """Test batch processing mode."""
        # Create multiple test files
        batch_dir = Path(self.temp_dir) / 'batch'
        batch_dir.mkdir(exist_ok=True)
        for i in range(5):
            shutil.copy(self.test_file, batch_dir / f'file_{i}.txt')

        result = self.runner.invoke(cli, [
            'process',
            '--config', str(self.config_path),
            '--batch',
            str(batch_dir)
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Processing completed', result.output)

    def test_cli_dry_run(self):
        """Test dry run mode."""
        result = self.runner.invoke(cli, [
            'process',
            '--config', str(self.config_path),
            '--dry-run',
            str(self.test_file)
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Dry run completed', result.output)
        
        # Verify no actual processing occurred
        db_path = Path(self.config['database']['path'])
        self.assertFalse(db_path.exists())

if __name__ == '__main__':
    unittest.main()