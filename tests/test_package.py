import unittest
import subprocess
import sys
import os
import venv
import tempfile
import shutil
from pathlib import Path
from importlib import metadata


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
import eless.eless_pipeline
import eless.core.config_loader
import eless.core.state_manager
import eless.core.resource_monitor
import eless.core.error_handler
import eless.core.archiver
import eless.processing.parallel_processor
import eless.processing.streaming_processor
import eless.processing.dispatcher
import eless.database.db_loader
import eless.embedding.embedder
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

        # Test CLI command (entry point creates 'eless' command)
        if sys.platform == "win32":
            eless_cmd = str(self.venv_dir / "Scripts" / "eless.exe")
        else:
            eless_cmd = str(self.venv_dir / "bin" / "eless")

        result = subprocess.run(
            [eless_cmd, "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("ELESS", result.stdout)

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
            try:
                dist_meta = metadata.metadata("eless")
                # Check that package was installed successfully
                self.assertIsNotNone(dist_meta)
            except metadata.PackageNotFoundError:
                self.fail(f"Package 'eless' not found after installing with [{group}] extras")

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
        dist_meta = metadata.metadata("eless")
        dist_version = metadata.version("eless")

        # Check metadata
        self.assertEqual(dist_meta["Name"], "eless")
        self.assertTrue(dist_version)
        
        # Check basic metadata exists
        self.assertIn("Summary", dist_meta)
        self.assertIn("Version", dist_meta)

        # Check dependencies
        requires = metadata.requires("eless")
        if requires:
            deps_str = " ".join(requires).lower()
            self.assertTrue("click" in deps_str)
            self.assertTrue("pyyaml" in deps_str)
            self.assertTrue("numpy" in deps_str)
            self.assertTrue("psutil" in deps_str)

    def test_package_resources(self):
        """Test package resource files."""
        # Install package
        subprocess.run([str(self.pip_path), "install", "-e", "."], capture_output=True)

        # Check if CLI command is available
        result = subprocess.run(
            [str(self.python_path), "-c", "import sys; print('Python import works')"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)

        # Check if eless command exists
        eless_path = self.venv_dir / "bin" / "eless"
        self.assertTrue(eless_path.exists(), "CLI command not found")

        # Try to run eless --help
        result = subprocess.run(
            [str(eless_path), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("ELESS", result.stdout)


if __name__ == "__main__":
    unittest.main()
