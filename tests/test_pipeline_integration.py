import unittest
import tempfile
import shutil
import os
from pathlib import Path
import yaml
from unittest.mock import MagicMock, patch

from src.eless_pipeline import ElessPipeline
from src.core.config_loader import ConfigLoader
from src.core.state_manager import StateManager
from src.core.resource_monitor import ResourceMonitor


class TestPipelineIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup test environment and load configuration."""
        # Load test configuration
        config_path = Path(__file__).parent / "fixtures" / "test_config.yaml"
        with open(config_path, "r") as f:
            cls.config = yaml.safe_load(f)

        # Create temporary directories
        cls.temp_dir = tempfile.mkdtemp(prefix="eless_test_")
        cls.cache_dir = tempfile.mkdtemp(prefix="eless_cache_")
        cls.db_dir = tempfile.mkdtemp(prefix="eless_db_")

        # Update config with temporary paths
        cls.config["cache"]["directory"] = cls.cache_dir
        cls.config["databases"]["connections"]["chroma"]["path"] = str(Path(cls.db_dir) / "chroma")
        cls.config["databases"]["connections"]["faiss"]["path"] = str(Path(cls.db_dir) / "faiss")

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        shutil.rmtree(cls.cache_dir, ignore_errors=True)
        shutil.rmtree(cls.db_dir, ignore_errors=True)

    def setUp(self):
        """Setup test-specific resources."""
        # Copy test files to temporary directory
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.test_file = Path(self.temp_dir) / "sample.txt"
        shutil.copy(self.fixtures_dir / "sample.txt", self.test_file)

        # Initialize pipeline components
        self.pipeline = ElessPipeline(self.config)
        self.state_manager = self.pipeline.state_manager
        self.resource_monitor = ResourceMonitor(self.config)

        # Clear state for clean test
        self.state_manager.clear_state()

    def test_pipeline_basic_flow(self):
        """Test basic pipeline flow with a single text file."""
        # Skip if embedding model not available (required for full processing)
        try:
            import sentence_transformers
        except ImportError:
            self.skipTest("Pipeline basic flow test requires sentence-transformers")

        # Run pipeline
        self.pipeline.run_process(str(self.test_file))

        # Verify state manager status
        file_hash = self.state_manager.get_file_hash(str(self.test_file))
        status = self.state_manager.get_status(file_hash)
        self.assertEqual(status, "LOADED")

        # Check cache directory
        cache_files = list(Path(self.cache_dir).glob("*"))
        self.assertGreater(len(cache_files), 0)

        # Check database
        db_path = Path(self.config["databases"]["connections"]["chroma"]["path"])
        self.assertTrue(db_path.exists())

    def test_pipeline_parallel_processing(self):
        """Test parallel processing features."""
        # Skip if embedding model not available
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            self.skipTest("Parallel processing test requires sentence-transformers")

        # Create multiple test files with different content
        test_files = []
        for i in range(3):
            test_file = Path(self.temp_dir) / f"test_{i}.txt"
            with open(test_file, "w") as f:
                f.write(f"Sample content {i}\n")
            test_files.append(test_file)

        # Run pipeline with parallel processing
        for file_path in test_files:
            self.pipeline.run_process(str(file_path))

        # Verify all files were processed
        processed_files = self.state_manager.get_all_files()
        self.assertEqual(len(processed_files), 3)
        self.assertTrue(all(f["status"] == "LOADED" for f in processed_files))

    def test_pipeline_error_handling(self):
        """Test pipeline error handling and recovery."""
        # Clear any existing state from other tests
        self.state_manager.clear_state()

        # Create an unreadable file
        bad_file = Path(self.temp_dir) / "unreadable.txt"
        bad_file.touch()
        os.chmod(bad_file, 0o000)

        # Run pipeline with bad file - should handle the error gracefully
        self.pipeline.run_process(str(bad_file))

        # Verify the file was not successfully processed
        processed_files = self.state_manager.get_all_files()
        # Should have no successfully processed files
        loaded_files = [f for f in processed_files if f["status"] == "LOADED"]
        self.assertEqual(len(loaded_files), 0)

        # Cleanup
        os.chmod(bad_file, 0o666)
        bad_file.unlink()

    def test_pipeline_resource_monitoring(self):
        """Test resource monitoring and adaptation."""
        # Create a large test file
        large_file = Path(self.temp_dir) / "large.txt"
        with open(large_file, "w") as f:
            f.write("x" * 1024 * 1024)  # 1MB file

        # Monitor resource usage during processing
        initial_metrics = self.resource_monitor.get_current_metrics()
        self.pipeline.run_process(str(large_file))
        final_metrics = self.resource_monitor.get_current_metrics()

        # Verify resource monitoring worked
        self.assertIsNotNone(final_metrics)
        self.assertGreaterEqual(len(self.resource_monitor.metrics_history), 1)

    def test_pipeline_configuration(self):
        """Test pipeline with different configurations."""
        # Skip if embedding model not available
        try:
            import sentence_transformers
        except ImportError:
            self.skipTest("Pipeline configuration test requires sentence-transformers")

        # Test with modified configuration
        test_configs = [
            # Minimal parallel processing
            {
                "parallel_processing": {
                    "enable_parallel_files": False,
                    "enable_parallel_chunks": False,
                }
            },
            # Different chunking settings
            {"chunking": {"chunk_size": 256, "chunk_overlap": 64}},
            # Strict resource limits
            {"resource_limits": {"memory_warning_percent": 60, "max_file_size_mb": 50}},
        ]

        for mod_config in test_configs:
            # Clear state for clean test
            self.state_manager.clear_state()

            # Create modified config
            config = self.config.copy()
            for section, settings in mod_config.items():
                config[section].update(settings)

            # Initialize pipeline with new config
            pipeline = ElessPipeline(config)
            pipeline.run_process(str(self.test_file))

            # Verify processing completed
            file_hash = pipeline.state_manager.get_file_hash(str(self.test_file))
            status = pipeline.state_manager.get_status(file_hash)
            self.assertEqual(status, "LOADED")

    def test_pipeline_resume(self):
        """Test pipeline resume functionality."""
        # Skip if embedding model not available
        try:
            import sentence_transformers
        except ImportError:
            self.skipTest("Pipeline resume test requires sentence-transformers")

        # Start processing
        self.pipeline.run_process(str(self.test_file))

        # Simulate interruption by clearing state
        self.state_manager.clear_state()

        # Resume processing
        self.pipeline.run_resume()

        # Verify processing completed
        file_hash = self.pipeline.state_manager.get_file_hash(str(self.test_file))
        status = self.pipeline.state_manager.get_status(file_hash)
        self.assertEqual(status, "LOADED")


if __name__ == "__main__":
    unittest.main()
