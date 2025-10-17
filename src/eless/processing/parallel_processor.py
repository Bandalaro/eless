import logging
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Callable, Iterator
from pathlib import Path
import queue
import time
from dataclasses import dataclass

from ..core.resource_monitor import ResourceMonitor

logger = logging.getLogger("ELESS.ParallelProcessor")


@dataclass
class ParallelConfig:
    """Configuration for parallel processing."""

    max_workers: Optional[int] = None  # Auto-detect if None
    processing_mode: str = "auto"  # "thread", "process", "auto"
    enable_parallel_files: bool = True
    enable_parallel_chunks: bool = True
    enable_parallel_embedding: bool = True
    enable_parallel_database: bool = True
    chunk_batch_size: int = 100  # Chunks per parallel batch
    file_batch_size: int = 10  # Files per parallel batch
    resource_monitoring: bool = True
    adaptive_workers: bool = True  # Dynamically adjust worker count


class ParallelProcessor:
    """
    Manages parallel processing across the ELESS pipeline with user control.
    Provides thread/process pool management with adaptive resource monitoring.
    """

    def __init__(
        self, config: Dict[str, Any], resource_monitor: ResourceMonitor = None
    ):
        self.config = config
        self.resource_monitor = resource_monitor

        # Load parallel processing configuration
        parallel_config = config.get("parallel_processing", {})
        self.parallel_config = ParallelConfig(
            max_workers=parallel_config.get("max_workers"),
            processing_mode=parallel_config.get("mode", "auto"),
            enable_parallel_files=parallel_config.get("enable_parallel_files", True),
            enable_parallel_chunks=parallel_config.get("enable_parallel_chunks", True),
            enable_parallel_embedding=parallel_config.get(
                "enable_parallel_embedding", True
            ),
            enable_parallel_database=parallel_config.get(
                "enable_parallel_database", True
            ),
            chunk_batch_size=parallel_config.get("chunk_batch_size", 100),
            file_batch_size=parallel_config.get("file_batch_size", 10),
            resource_monitoring=parallel_config.get("resource_monitoring", True),
            adaptive_workers=parallel_config.get("adaptive_workers", True),
        )

        # Determine optimal worker count
        self.max_workers = self._determine_max_workers()
        self.current_workers = self.max_workers

        # Thread safety
        self.worker_lock = threading.Lock()
        self.stats_lock = threading.Lock()

        # Performance tracking
        self.processing_stats = {
            "files_processed": 0,
            "chunks_processed": 0,
            "embeddings_generated": 0,
            "database_writes": 0,
            "total_processing_time": 0.0,
            "average_file_time": 0.0,
        }

        logger.info(
            f"ParallelProcessor initialized - Mode: {self.parallel_config.processing_mode}, "
            f"Max workers: {self.max_workers}, File parallel: {self.parallel_config.enable_parallel_files}, "
            f"Chunk parallel: {self.parallel_config.enable_parallel_chunks}"
        )

    def _determine_max_workers(self) -> int:
        """Determine optimal number of workers based on system resources and user config."""
        if self.parallel_config.max_workers:
            return self.parallel_config.max_workers

        # Auto-detect based on CPU cores and memory
        cpu_cores = multiprocessing.cpu_count()

        if self.resource_monitor:
            # Consider available memory for worker count
            metrics = self.resource_monitor.get_current_metrics()
            memory_gb = metrics.available_memory_mb / 1024

            # Conservative estimate: 1 worker per 500MB + 1 core
            memory_workers = max(1, int(memory_gb / 0.5))
            cpu_workers = max(1, cpu_cores - 1)  # Leave 1 core for system

            # Use the more conservative estimate
            optimal_workers = min(memory_workers, cpu_workers, 8)  # Cap at 8 workers
        else:
            # Fallback: use 75% of CPU cores, max 4 for safety
            optimal_workers = max(1, min(int(cpu_cores * 0.75), 4))

        logger.info(
            f"Auto-detected optimal workers: {optimal_workers} "
            f"(CPU cores: {cpu_cores}, Memory-based: {memory_workers if self.resource_monitor else 'N/A'})"
        )

        return optimal_workers

    def adjust_worker_count(self) -> int:
        """Dynamically adjust worker count based on current resource usage."""
        if not self.parallel_config.adaptive_workers or not self.resource_monitor:
            return self.current_workers

        metrics = self.resource_monitor.get_current_metrics()
        should_throttle, reason = self.resource_monitor.should_throttle_processing()

        with self.worker_lock:
            old_workers = self.current_workers

            if should_throttle:
                # Reduce workers under high resource pressure
                self.current_workers = max(1, self.current_workers - 1)
                logger.info(
                    f"Reducing workers from {old_workers} to {self.current_workers} - {reason}"
                )
            elif (
                metrics.memory_percent < 60
                and metrics.cpu_percent < 70
                and self.current_workers < self.max_workers
            ):
                # Increase workers when resources are available
                self.current_workers = min(self.max_workers, self.current_workers + 1)
                logger.info(
                    f"Increasing workers from {old_workers} to {self.current_workers} - abundant resources"
                )

        return self.current_workers

    def process_files_parallel(
        self,
        file_metadata_list: List[Dict],
        processor_func: Callable,
        progress_callback: Callable = None,
    ) -> Iterator[Dict]:
        """
        Process multiple files in parallel.

        Args:
            file_metadata_list: List of file metadata dictionaries
            processor_func: Function to process each file
            progress_callback: Optional callback for progress updates

        Yields:
            Processing results for each file
        """
        if (
            not self.parallel_config.enable_parallel_files
            or len(file_metadata_list) <= 1
        ):
            logger.info("Processing files sequentially")
            for file_meta in file_metadata_list:
                yield processor_func(file_meta)
            return

        logger.info(
            f"Processing {len(file_metadata_list)} files with {self.current_workers} workers"
        )

        # Choose executor based on processing mode
        executor_class = self._get_executor_class()

        with executor_class(max_workers=self.current_workers) as executor:
            # Submit all file processing tasks
            future_to_file = {}
            for file_meta in file_metadata_list:
                future = executor.submit(
                    self._safe_file_processor, processor_func, file_meta
                )
                future_to_file[future] = file_meta

            # Process completed futures as they finish
            completed_count = 0
            for future in as_completed(future_to_file):
                completed_count += 1
                file_meta = future_to_file[future]

                try:
                    result = future.result()

                    # Update stats
                    with self.stats_lock:
                        self.processing_stats["files_processed"] += 1

                    # Progress callback
                    if progress_callback:
                        progress_callback(completed_count, len(file_metadata_list))

                    # Adjust worker count based on resource usage
                    if self.parallel_config.adaptive_workers:
                        self.adjust_worker_count()

                    yield result

                except Exception as e:
                    logger.error(
                        f"Failed to process file {file_meta.get('path', 'unknown')}: {e}"
                    )
                    yield {"error": str(e), "file_meta": file_meta}

    def _safe_file_processor(self, processor_func: Callable, file_meta: Dict) -> Dict:
        """Wrapper for file processing with error handling and timing."""
        start_time = time.time()
        try:
            result = processor_func(file_meta)
            processing_time = time.time() - start_time

            # Update average processing time
            with self.stats_lock:
                total_files = self.processing_stats["files_processed"]
                current_avg = self.processing_stats["average_file_time"]
                new_avg = (current_avg * total_files + processing_time) / (
                    total_files + 1
                )
                self.processing_stats["average_file_time"] = new_avg
                self.processing_stats["total_processing_time"] += processing_time

            return result
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
            raise

    def process_chunks_parallel(
        self,
        chunks: List[Dict],
        processor_func: Callable,
        batch_size: Optional[int] = None,
    ) -> List[Dict]:
        """
        Process text chunks in parallel batches.

        Args:
            chunks: List of text chunks to process
            processor_func: Function to process each batch of chunks
            batch_size: Optional batch size override

        Returns:
            List of processed chunks
        """
        if (
            not self.parallel_config.enable_parallel_chunks
            or len(chunks) <= self.parallel_config.chunk_batch_size
        ):
            logger.debug("Processing chunks sequentially")
            return processor_func(chunks)

        batch_size = batch_size or self.parallel_config.chunk_batch_size
        logger.info(
            f"Processing {len(chunks)} chunks in parallel batches of {batch_size}"
        )

        # Split chunks into batches
        chunk_batches = [
            chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)
        ]

        # Choose executor
        executor_class = self._get_executor_class()

        processed_chunks = []
        with executor_class(
            max_workers=min(self.current_workers, len(chunk_batches))
        ) as executor:
            # Submit batch processing tasks
            future_to_batch = {
                executor.submit(processor_func, batch): batch for batch in chunk_batches
            }

            # Collect results
            for future in as_completed(future_to_batch):
                try:
                    batch_result = future.result()
                    if isinstance(batch_result, list):
                        processed_chunks.extend(batch_result)
                    else:
                        processed_chunks.append(batch_result)

                    with self.stats_lock:
                        self.processing_stats["chunks_processed"] += len(
                            future_to_batch[future]
                        )

                except Exception as e:
                    logger.error(f"Failed to process chunk batch: {e}")
                    # Continue processing other batches

        return processed_chunks

    def process_embeddings_parallel(
        self, text_batches: List[List[str]], embedder_func: Callable
    ) -> List:
        """
        Generate embeddings for text batches in parallel.

        Args:
            text_batches: List of text batches to embed
            embedder_func: Function to generate embeddings

        Returns:
            List of embedding vectors
        """
        if not self.parallel_config.enable_parallel_embedding or len(text_batches) <= 1:
            logger.debug("Processing embeddings sequentially")
            all_embeddings = []
            for batch in text_batches:
                embeddings = embedder_func(batch)
                all_embeddings.extend(embeddings)
            return all_embeddings

        logger.info(
            f"Generating embeddings for {len(text_batches)} batches in parallel"
        )

        # For embeddings, prefer thread-based parallelism due to model sharing
        all_embeddings = []
        with ThreadPoolExecutor(
            max_workers=min(self.current_workers, len(text_batches))
        ) as executor:
            future_to_batch = {
                executor.submit(embedder_func, batch): batch for batch in text_batches
            }

            for future in as_completed(future_to_batch):
                try:
                    batch_embeddings = future.result()
                    all_embeddings.extend(batch_embeddings)

                    with self.stats_lock:
                        self.processing_stats["embeddings_generated"] += len(
                            batch_embeddings
                        )

                except Exception as e:
                    logger.error(f"Failed to generate embeddings for batch: {e}")

        return all_embeddings

    def load_to_databases_parallel(
        self, db_connectors: Dict, batch_data: List[Dict]
    ) -> Dict[str, bool]:
        """
        Load data to multiple databases in parallel.

        Args:
            db_connectors: Dictionary of database connectors
            batch_data: Data to load

        Returns:
            Dictionary mapping database names to success status
        """
        if not self.parallel_config.enable_parallel_database or len(db_connectors) <= 1:
            logger.debug("Loading to databases sequentially")
            results = {}
            for name, connector in db_connectors.items():
                try:
                    connector.upsert_batch(batch_data)
                    results[name] = True
                except Exception as e:
                    logger.error(f"Failed to load to {name}: {e}")
                    results[name] = False
            return results

        logger.info(f"Loading to {len(db_connectors)} databases in parallel")

        results = {}
        with ThreadPoolExecutor(
            max_workers=min(self.current_workers, len(db_connectors))
        ) as executor:
            future_to_db = {
                executor.submit(self._safe_db_loader, connector, batch_data): name
                for name, connector in db_connectors.items()
            }

            for future in as_completed(future_to_db):
                db_name = future_to_db[future]
                try:
                    success = future.result()
                    results[db_name] = success

                    if success:
                        with self.stats_lock:
                            self.processing_stats["database_writes"] += 1

                except Exception as e:
                    logger.error(f"Database loading future failed for {db_name}: {e}")
                    results[db_name] = False

        return results

    def _safe_db_loader(self, connector, batch_data: List[Dict]) -> bool:
        """Safe wrapper for database loading."""
        try:
            connector.upsert_batch(batch_data)
            return True
        except Exception as e:
            logger.error(f"Database connector failed: {e}")
            return False

    def _get_executor_class(self):
        """Get the appropriate executor class based on configuration."""
        if self.parallel_config.processing_mode == "thread":
            return ThreadPoolExecutor
        elif self.parallel_config.processing_mode == "process":
            return ProcessPoolExecutor
        else:  # auto
            # Use threads for I/O bound tasks, processes for CPU bound
            # For ELESS, most operations are I/O bound (file reading, network)
            return ThreadPoolExecutor

    def get_processing_stats(self) -> Dict:
        """Get current processing statistics."""
        with self.stats_lock:
            stats = self.processing_stats.copy()
            stats["current_workers"] = self.current_workers
            stats["max_workers"] = self.max_workers
            stats["parallel_enabled"] = {
                "files": self.parallel_config.enable_parallel_files,
                "chunks": self.parallel_config.enable_parallel_chunks,
                "embedding": self.parallel_config.enable_parallel_embedding,
                "database": self.parallel_config.enable_parallel_database,
            }
            return stats

    def shutdown(self):
        """Clean shutdown of parallel processor."""
        logger.info("Shutting down parallel processor")
        # Any cleanup needed
        pass
