import unittest
import tempfile
import shutil
import os
import signal
import time
import logging
from pathlib import Path
import yaml
from unittest.mock import MagicMock, patch
from multiprocessing import Process, Queue

from eless.eless_pipeline import ElessPipeline
from eless.core.state_manager import StateManager
from eless.core.error_handler import ErrorHandler
from eless.core.archiver import Archiver


class TestErrorHandling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup test environment."""
        # Create temporary directory
        cls.temp_dir = tempfile.mkdtemp(prefix="eless_error_test_")

        # Load test configuration
        config_path = Path(__file__).parent / "fixtures" / "test_config.yaml"
        with open(config_path, "r") as f:
            cls.config = yaml.safe_load(f)

        # Update paths for testing
        cls.cache_dir = tempfile.mkdtemp(prefix="eless_error_cache_")
        cls.db_dir = tempfile.mkdtemp(prefix="eless_error_db_")
        cls.config["cache"]["directory"] = cls.cache_dir
        cls.config["databases"]["connections"]["chroma"]["path"] = str(Path(cls.db_dir) / "chroma")

        # Copy test files
        cls.fixtures_dir = Path(__file__).parent / "fixtures"
        cls.test_file = Path(cls.temp_dir) / "sample.txt"
        shutil.copy(cls.fixtures_dir / "sample.txt", cls.test_file)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        shutil.rmtree(cls.cache_dir, ignore_errors=True)
        shutil.rmtree(cls.db_dir, ignore_errors=True)
        logging.shutdown()

    def setUp(self):
        """Setup for each test."""
        self.pipeline = ElessPipeline(self.config)
        self.state_manager = self.pipeline.state_manager
        self.error_handler = ErrorHandler(self.config, self.state_manager)
        self.archiver = self.pipeline.archiver

    def test_file_access_error(self):
        """Test handling of file access errors."""
        # Create an unreadable file
        unreadable_file = Path(self.temp_dir) / "unreadable.txt"
        unreadable_file.touch()
        os.chmod(unreadable_file, 0o000)

        # Attempt to process
        self.pipeline.run_process(str(unreadable_file))

        # Check error status
        # Since file is unreadable, hash is "ERROR"
        file_hash = "ERROR"
        status = self.state_manager.get_status(file_hash)
        self.assertEqual(status, "ERROR")

        # Verify error was logged
        error_log = self.error_handler.get_error_log(file_hash)
        self.assertIsNotNone(error_log)
        if error_log:
            self.assertIn("Failed to scan", error_log)

        # Cleanup
        os.chmod(unreadable_file, 0o666)
        unreadable_file.unlink()

    def test_invalid_file_format(self):
        """Test handling of invalid file formats."""
        # Create a file with invalid content
        invalid_file = Path(self.temp_dir) / "invalid.bin"
        with open(invalid_file, "wb") as f:
            f.write(os.urandom(1024))  # Random binary data

        # Attempt to process
        with self.assertLogs(level="ERROR"):
            self.pipeline.run_process(str(invalid_file))

        # Verify error handling
        file_hash = self.state_manager.get_file_hash(str(invalid_file))
        status = self.state_manager.get_status(file_hash)
        self.assertEqual(status, "ERROR")

    def test_memory_error_recovery(self):
        """Test recovery from memory errors."""
        # Create a large file
        large_file = Path(self.temp_dir) / "large.txt"
        with open(large_file, "w") as f:
            f.write("x" * (1024 * 1024 * 10))  # 10MB file

        # Force streaming by setting low memory limits
        original_memory_limit = self.config["resource_limits"]["max_memory_percent"]
        self.config["resource_limits"]["max_memory_percent"] = 1  # Very low

        try:
            # Force streaming and mock memory error
            with patch.object(
                self.pipeline.dispatcher.streaming_processor, "should_use_streaming", return_value=True
            ):
                with patch(
                    "eless.processing.streaming_processor.StreamingDocumentProcessor.process_large_text_file"
                ) as mock_process:
                    mock_process.side_effect = MemoryError("Out of memory")

                    with self.assertLogs("ELESS.Dispatcher", level="ERROR"):
                        self.pipeline.run_process(str(large_file))
        finally:
            self.config["resource_limits"]["max_memory_percent"] = original_memory_limit

        # Verify error state
        file_hash = self.state_manager.get_file_hash(str(large_file))
        status = self.state_manager.get_status(file_hash)
        self.assertEqual(status, "ERROR")

        # Reset status to allow re-processing
        self.state_manager.reset_file_status(file_hash)

        # Try processing with reduced batch size
        self.config["chunking"]["chunk_size"] = 1024  # Reduce chunk size
        self.pipeline.run_process(str(large_file))

        # Verify recovery
        status = self.state_manager.get_status(file_hash)
        self.assertEqual(status, "LOADED")

    def test_interrupted_processing(self):
        """Test recovery from interrupted processing."""
        # Use a unique file for this test
        interrupt_file = Path(self.temp_dir) / "interrupt_test.txt"
        interrupt_file.write_text("This is a test file for interruption.")

        # Mock exception during chunking
        with patch(
            "eless.processing.dispatcher.chunk_text"
        ) as mock_chunk:
            mock_chunk.side_effect = Exception("Processing interrupted")

            # Run processing (exception caught internally)
            self.pipeline.run_process(str(interrupt_file))

        # Verify error state
        file_hash = self.state_manager.get_file_hash(str(interrupt_file))
        status = self.state_manager.get_status(file_hash)
        self.assertEqual(status, "ERROR")

        # Reset and re-process
        self.state_manager.reset_file_status(file_hash)
        self.pipeline.run_process(str(interrupt_file))

        # Verify completion
        status = self.state_manager.get_status(file_hash)
        self.assertEqual(status, "LOADED")

    def test_database_error_recovery(self):
        """Test recovery from database errors."""
        # Mock database error
        with patch(
            "eless.database.db_loader.DatabaseLoader._initialize_connectors"
        ) as mock_db:
            mock_db.side_effect = Exception("Database connection error")

            with self.assertLogs(level="ERROR"):
                self.pipeline.run_process(str(self.test_file))

        # Verify error state
        file_hash = self.state_manager.get_file_hash(str(self.test_file))
        initial_status = self.state_manager.get_status(file_hash)

        # Retry with working database
        self.pipeline.run_resume()

        # Verify recovery
        final_status = self.state_manager.get_status(file_hash)
        self.assertEqual(final_status, "LOADED")

    def test_corrupted_cache_recovery(self):
        """Test recovery from corrupted cache."""
        # Process file normally first
        self.pipeline.run_process(str(self.test_file))
        file_hash = self.state_manager.get_file_hash(str(self.test_file))

        # Corrupt the cache
        cache_file = Path(self.cache_dir) / f"{file_hash}.cache"
        with open(cache_file, "w") as f:
            f.write("corrupted data")

        # Reset status to allow re-processing
        self.state_manager.reset_file_status(file_hash)

        # Try processing again
        self.pipeline.run_process(str(self.test_file))

        # Verify recovery
        status = self.state_manager.get_status(file_hash)
        self.assertEqual(status, "LOADED")

        # Check if new cache is valid
        self.assertTrue(self.archiver.validate_cache(file_hash))

    def test_parallel_processing_errors(self):
        """Test error handling in parallel processing."""
        # Create multiple files
        files = []
        for i in range(5):
            file_path = Path(self.temp_dir) / f"test_{i}.txt"
            shutil.copy(self.test_file, file_path)
            files.append(file_path)

        # Make one file unreadable
        os.chmod(files[2], 0o000)

        # Process all files
        for file_path in files:
            self.pipeline.run_process(str(file_path))

        # Check statuses
        statuses = []
        for f in files:
            try:
                hash_val = self.state_manager.get_file_hash(str(f))
                status = self.state_manager.get_status(hash_val)
            except PermissionError:
                status = "ERROR"
            statuses.append(status)

        # Verify other files processed successfully
        self.assertEqual(statuses[0], "LOADED")
        self.assertEqual(statuses[1], "LOADED")
        self.assertEqual(statuses[2], "ERROR")  # Unreadable file
        self.assertEqual(statuses[3], "LOADED")
        self.assertEqual(statuses[4], "LOADED")

        # Cleanup
        os.chmod(files[2], 0o666)

    def test_resource_limit_handling(self):
        """Test handling of resource limits."""
        # Set very strict resource limits
        self.config["resource_limits"]["memory_warning_percent"] = 10
        self.config["resource_limits"]["max_file_size_mb"] = 1

        # Create a file slightly over the limit
        large_file = Path(self.temp_dir) / "overlimit.txt"
        with open(large_file, "w") as f:
            f.write("x" * (1024 * 1024 * 2))  # 2MB file

        # Attempt to process
        with self.assertLogs(level="WARNING"):
            self.pipeline.run_process(str(large_file))

        # Verify adaptive processing
        file_hash = self.state_manager.get_file_hash(str(large_file))
        status = self.state_manager.get_status(file_hash)
        self.assertEqual(status, "LOADED")


if __name__ == "__main__":
    unittest.main()
