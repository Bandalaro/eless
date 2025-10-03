import unittest
import subprocess
import sys
import os
import venv
import tempfile
import shutil
from pathlib import Path
import pkg_resources


class TestPackageInstallation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create a clean virtual environment for testing package installation."""
        cls.temp_dir = tempfile.mkdtemp(prefix="eless_pkg_test_")
        cls.venv_dir = Path(cls.temp_dir) / "venv"
        venv.create(cls.venv_dir, with_pip=True)

        # Get paths
        if sys.platform == "win32":
            cls.python_path = cls.venv_dir / "Scripts" / "python.exe"
            cls.pip_path = cls.venv_dir / "Scripts" / "pip.exe"
        else:
            cls.python_path = cls.venv_dir / "bin" / "python"
            cls.pip_path = cls.venv_dir / "bin" / "pip"

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.temp_dir)

    def test_package_installation(self):
        """Test basic package installation."""
        # Install package
        result = subprocess.run(
            [str(self.pip_path), "install", "-e", "."], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, f"Installation failed: {result.stderr}")

        # Verify installation
        result = subprocess.run(
            [str(self.pip_path), "list"], capture_output=True, text=True
        )
        self.assertIn("eless", result.stdout)

    def test_core_imports(self):
        """Test that all core modules can be imported."""
        # Create test script
        test_script = Path(self.temp_dir) / "test_imports.py"
        test_script.write_text(
            """
import src.eless_pipeline
import src.core.config_loader
import src.core.state_manager
import src.core.resource_monitor
import src.core.error_handler
import src.core.archiver
import src.processing.parallel_processor
import src.processing.streaming_processor
import src.processing.dispatcher
import src.database.db_loader
import src.embedding.embedder
print("All imports successful!")
"""
        )

        # Run test script in virtual environment
        result = subprocess.run(
            [str(self.python_path), str(test_script)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, f"Import test failed: {result.stderr}")
        self.assertIn("All imports successful!", result.stdout)

    def test_cli_installation(self):
        """Test CLI command installation."""
        # Install package with CLI
        subprocess.run([str(self.pip_path), "install", "-e", "."], capture_output=True)

        # Test CLI command
        result = subprocess.run(
            [str(self.python_path), "-m", "eless", "version"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("ELESS version", result.stdout)

    def test_optional_dependencies(self):
        """Test installation with different dependency groups."""
        dependency_groups = ["embeddings", "databases", "parsers", "full"]

        for group in dependency_groups:
            # Install with specific extras
            result = subprocess.run(
                [str(self.pip_path), "install", f".[{group}]"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"Installation failed for group {group}: {result.stderr}",
            )

            # Verify dependencies
            dist = pkg_resources.working_set.by_key["eless"]
            extras = dist.extras if hasattr(dist, "extras") else []
            self.assertIn(group, extras)

    def test_development_environment(self):
        """Test development environment setup."""
        # Install development dependencies
        result = subprocess.run(
            [str(self.pip_path), "install", ".[dev]"], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)

        # Verify development tools
        dev_tools = ["pytest", "black", "flake8", "mypy"]
        for tool in dev_tools:
            result = subprocess.run(
                [str(self.pip_path), "show", tool], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0)

    def test_package_metadata(self):
        """Test package metadata."""
        # Install package
        subprocess.run([str(self.pip_path), "install", "-e", "."], capture_output=True)

        # Get distribution info
        dist = pkg_resources.working_set.by_key["eless"]

        # Check metadata
        self.assertEqual(dist.project_name, "eless")
        self.assertTrue(dist.version)
        self.assertTrue(dist.has_metadata("METADATA") or dist.has_metadata("PKG-INFO"))

        # Check dependencies
        deps = [str(r) for r in dist.requires()]
        self.assertTrue(any("click" in d for d in deps))
        self.assertTrue(any("PyYAML" in d for d in deps))
        self.assertTrue(any("numpy" in d for d in deps))
        self.assertTrue(any("psutil" in d for d in deps))

    def test_package_resources(self):
        """Test package resource files."""
        # Install package
        subprocess.run([str(self.pip_path), "install", "-e", "."], capture_output=True)

        # Check for essential resource files
        test_script = Path(self.temp_dir) / "test_resources.py"
        test_script.write_text(
            """
import pkg_resources
import json
import yaml

try:
    # Test YAML config loading
    config = pkg_resources.resource_string('src', 'config/default_config.yaml')
    yaml.safe_load(config)
    
    # Test other resource files
    files = pkg_resources.resource_listdir('src', 'config')
    print("Resource files:", files)
    print("All resource checks passed!")
except Exception as e:
    print(f"Resource test failed: {e}")
    exit(1)
"""
        )

        result = subprocess.run(
            [str(self.python_path), str(test_script)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, f"Resource test failed: {result.stderr}")
        self.assertIn("All resource checks passed!", result.stdout)


if __name__ == "__main__":
    unittest.main()
