import unittest
import multiprocessing
import threading
from pathlib import Path
import tempfile
import os
from unittest.mock import MagicMock, patch

from src.processing.parallel_processor import ParallelProcessor, ParallelConfig
from src.core.resource_monitor import ResourceMonitor


class TestParallelProcessor(unittest.TestCase):
    def setUp(self):
        self.test_config = {
            "parallel_processing": {
                "max_workers": 2,
                "mode": "thread",
                "enable_parallel_files": True,
                "enable_parallel_chunks": True,
                "enable_parallel_embedding": True,
                "enable_parallel_database": True,
                "chunk_batch_size": 5,
                "file_batch_size": 2,
            },
            "embedding": {"batch_size": 32, "model": "all-MiniLM-L6-v2"},
            "resource_limits": {
                "memory_warning_percent": 80,
                "memory_critical_percent": 90,
                "cpu_high_percent": 85,
                "min_memory_mb": 256,
            },
            "cache": {"directory": "/tmp/eless_test_cache"},
        }
        self.resource_monitor = ResourceMonitor(self.test_config)
        self.processor = ParallelProcessor(self.test_config, self.resource_monitor)

    def test_process_files_parallel(self):
        # Create test files
        test_files = []
        with tempfile.TemporaryDirectory() as temp_dir:
            for i in range(5):
                file_path = Path(temp_dir) / f"test_{i}.txt"
                with open(file_path, "w") as f:
                    f.write(f"Test content {i}")
                test_files.append(
                    {
                        "path": file_path,
                        "hash": f"hash_{i}",
                        "size": os.path.getsize(file_path),
                    }
                )

            # Mock processor function
            def mock_processor(file_meta):
                return {"processed": True, "file": file_meta["path"].name}

            # Process files in parallel
            results = list(
                self.processor.process_files_parallel(test_files, mock_processor)
            )

            # Verify results
            self.assertEqual(len(results), 5)
            self.assertTrue(all(r["processed"] for r in results))
            file_names = {r["file"] for r in results}
            self.assertEqual(len(file_names), 5)

    def test_process_chunks_parallel(self):
        test_chunks = [{"text": f"chunk_{i}"} for i in range(10)]

        def mock_processor(chunks):
            return [{"processed": True, **chunk} for chunk in chunks]

        # Process chunks in parallel
        results = self.processor.process_chunks_parallel(
            test_chunks, mock_processor, batch_size=3
        )

        # Verify results
        self.assertEqual(len(results), 10)
        self.assertTrue(all(r["processed"] for r in results))

    def test_process_embeddings_parallel(self):
        test_batches = [[f"text_{i}_{j}" for j in range(3)] for i in range(4)]

        def mock_embedder(batch):
            return [f"embedding_{text}" for text in batch]

        # Process embeddings in parallel
        results = self.processor.process_embeddings_parallel(
            test_batches, mock_embedder
        )

        # Verify results
        self.assertEqual(len(results), 12)  # 4 batches * 3 texts
        self.assertTrue(all("embedding_text" in r for r in results))

    def test_adaptive_workers(self):
        # Test worker count adaptation under high memory pressure
        with patch(
            "src.core.resource_monitor.ResourceMonitor.should_throttle_processing"
        ) as mock_throttle:
            # Simulate high memory pressure
            mock_throttle.return_value = (True, "High memory usage")

            initial_workers = self.processor.current_workers
            new_workers = self.processor.adjust_worker_count()

            # Should reduce workers
            self.assertLess(new_workers, initial_workers)
            self.assertGreaterEqual(new_workers, 1)  # Never go below 1

    def test_thread_vs_process_mode(self):
        # Test with thread mode
        thread_config = dict(self.test_config)
        thread_config["parallel_processing"]["mode"] = "thread"
        thread_processor = ParallelProcessor(thread_config, self.resource_monitor)
        self.assertEqual(
            thread_processor._get_executor_class().__name__, "ThreadPoolExecutor"
        )

        # Test with process mode
        process_config = dict(self.test_config)
        process_config["parallel_processing"]["mode"] = "process"
        process_processor = ParallelProcessor(process_config, self.resource_monitor)
        self.assertEqual(
            process_processor._get_executor_class().__name__, "ProcessPoolExecutor"
        )

    def test_database_load_parallel(self):
        test_data = [{"id": i, "text": f"data_{i}"} for i in range(5)]
        db_connectors = {"db1": MagicMock(), "db2": MagicMock()}

        # Configure mock behaviors
        db_connectors["db1"].upsert_batch.return_value = None
        db_connectors["db2"].upsert_batch.return_value = None

        # Test parallel database loading
        results = self.processor.load_to_databases_parallel(db_connectors, test_data)

        # Verify results
        self.assertEqual(len(results), 2)
        self.assertTrue(all(results.values()))

        # Verify each connector was called
        db_connectors["db1"].upsert_batch.assert_called_once_with(test_data)
        db_connectors["db2"].upsert_batch.assert_called_once_with(test_data)


if __name__ == "__main__":
    unittest.main()
