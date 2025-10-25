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

<<<<<<< HEAD
from src.eless.eless_pipeline import ElessPipeline
from src.eless.core.state_manager import StateManager
from src.eless.core.error_handler import ErrorHandler
from src.eless.core.archiver import Archiver
from src.eless.core.config_loader import ConfigLoader
from src.eless.embedding.model_loader import ModelLoader
from src.eless.database.qdrant_connector import QdrantConnector
from src.eless.database.postgresql_connector import PostgreSQLConnector
from src.eless.database.db_loader import DatabaseLoader
from unittest.mock import mock_open
=======
from eless.eless_pipeline import ElessPipeline
from eless.core.state_manager import StateManager
from eless.core.error_handler import ErrorHandler
from eless.core.archiver import Archiver
>>>>>>> 11438b7cdd044f7879749246c2da07d58e109b9c


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
<<<<<<< HEAD
                    "src.eless.processing.streaming_processor.StreamingDocumentProcessor.process_large_text_file"
=======
                    "eless.processing.streaming_processor.StreamingDocumentProcessor.process_large_text_file"
>>>>>>> 11438b7cdd044f7879749246c2da07d58e109b9c
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
<<<<<<< HEAD
            "src.eless.processing.dispatcher.chunk_text"
=======
            "eless.processing.dispatcher.chunk_text"
>>>>>>> 11438b7cdd044f7879749246c2da07d58e109b9c
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
<<<<<<< HEAD
            "src.eless.database.db_loader.DatabaseLoader._initialize_connectors"
=======
            "eless.database.db_loader.DatabaseLoader._initialize_connectors"
>>>>>>> 11438b7cdd044f7879749246c2da07d58e109b9c
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

<<<<<<< HEAD
    def test_qdrant_connection_error(self):
        """Test Qdrant connection error handling."""
        from src.eless.database.qdrant_connector import QdrantConnector

        config = {
            "databases": {
                "connections": {
                    "qdrant": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "test_collection"
                    }
                }
            }
        }
        connector = QdrantConnector(config, "qdrant", dimension=384)

        # Mock connection failure
        with patch.object(connector, '_check_qdrant_running', side_effect=ConnectionError("Connection refused")):
            with self.assertRaises(ConnectionError):
                connector.connect()

    def test_postgresql_connection_error(self):
        """Test PostgreSQL connection error handling."""
        from src.eless.database.postgresql_connector import PostgreSQLConnector

        config = {
            "databases": {
                "connections": {
                    "postgresql": {
                        "host": "localhost",
                        "port": 5432,
                        "user": "test",
                        "password": "test",
                        "database": "test"
                    }
                }
            }
        }
        connector = PostgreSQLConnector(config, "postgresql", dimension=384)

        # Mock connection failure
        with patch('psycopg2.connect', side_effect=Exception("Connection refused")):
            with self.assertRaises(ConnectionError):
                connector.connect()



    def test_config_loader_invalid_yaml(self):
        """Test ConfigLoader error handling for invalid YAML."""
        from src.eless.core.config_loader import ConfigLoader

        config_loader = ConfigLoader()

        with patch('builtins.open', mock_open(read_data="invalid: yaml: content: [")), \
             patch('pathlib.Path.exists', return_value=True):
            with self.assertRaises(yaml.YAMLError):
                config_loader.get_final_config(user_config_path="/tmp/invalid.yaml")

    def test_model_loader_import_error(self):
        """Test ModelLoader error handling for missing sentence-transformers."""
        from src.eless.embedding.model_loader import ModelLoader

        config = {"embedding": {"model": "test-model"}}
        
        with patch('src.eless.embedding.model_loader.SENTENCE_TRANSFORMERS_AVAILABLE', False):
            model_loader = ModelLoader(config)
            self.assertIsNone(model_loader.model)
            self.assertEqual(model_loader.embedding_dimension, 384)

    def test_qdrant_upsert_batch_no_client(self):
        """Test Qdrant upsert error when client not initialized."""
        config = {
            "databases": {
                "connections": {
                    "qdrant": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "test_collection"
                    }
                }
            }
        }
        connector = QdrantConnector(config, "qdrant", dimension=384)

        vectors = [{"id": "test", "vector": [0.1] * 384, "metadata": {}}]

        with self.assertRaises(ConnectionError):
            connector.upsert_batch(vectors)

    def test_postgresql_upsert_batch_no_connection(self):
        """Test PostgreSQL upsert error when connection not initialized."""
        config = {
            "databases": {
                "connections": {
                    "postgresql": {
                        "host": "localhost",
                        "port": 5432,
                        "user": "test",
                        "password": "test",
                        "database": "test"
                    }
                }
            }
        }
        connector = PostgreSQLConnector(config, "postgresql", dimension=384)

        vectors = [{"id": "test", "vector": [0.1] * 384, "metadata": {}}]

        with self.assertRaises(ConnectionError):
            connector.upsert_batch(vectors)

    def test_config_validation_errors(self):
        """Test ConfigLoader validation error handling."""
        config_loader = ConfigLoader()

        # Test invalid chunk_size
        invalid_config = {
            "chunking": {"chunk_size": -1},
            "embedding": {"batch_size": 32}
        }

        with self.assertRaises(ValueError):
            config_loader.validate_config(invalid_config)

        # Test invalid embedding batch_size
        invalid_config = {
            "embedding": {"batch_size": 0}
        }

        with self.assertRaises(ValueError):
            config_loader.validate_config(invalid_config)

    def test_state_manager_invalid_status_update(self):
        """Test StateManager error handling for invalid status."""
        from src.eless.core.state_manager import StateManager

        config = {"cache": {"directory": ".", "manifest_file": "manifest.json"}}
        state_manager = StateManager(config)

        # Test invalid status string
        with self.assertRaises(ValueError):
            state_manager.add_or_update_file("hash", "INVALID_STATUS", "path")
        
        # Test non-string status
        with self.assertRaises(TypeError):
            state_manager.add_or_update_file("hash", 123, "path")

    def test_database_loader_import_error(self):
        """Test DatabaseLoader error handling for missing dependencies."""
        from src.eless.database.db_loader import DatabaseLoader

        config = {
            "databases": {
                "targets": ["qdrant"],
                "connections": {
                    "qdrant": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "test"
                    }
                },
                "batch_size": 100
            },
            "embedding": {
                "dimension": 384
            }
        }

        # Mock qdrant availability to False
        with patch('src.eless.database.db_loader.QDRANT_AVAILABLE', False):
            db_loader = DatabaseLoader(config, MagicMock(), MagicMock())
            # Should initialize but with no active connectors
            self.assertEqual(len(db_loader.active_connectors), 0)

=======
>>>>>>> 11438b7cdd044f7879749246c2da07d58e109b9c

if __name__ == "__main__":
    unittest.main()
