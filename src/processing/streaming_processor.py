import logging
from typing import Iterator, Dict, Any, List, Optional
from pathlib import Path
import os
import mmap
from contextlib import contextmanager

logger = logging.getLogger("ELESS.StreamingProcessor")


class StreamingDocumentProcessor:
    """
    Memory-efficient document processor for low-end systems.
    Uses streaming and chunked processing to handle large files without
    loading entire content into memory.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_memory_usage_mb = config.get("resource_limits", {}).get(
            "max_memory_mb", 512
        )
        self.chunk_buffer_size = config.get("streaming", {}).get(
            "buffer_size", 8192
        )  # 8KB chunks
        self.max_file_size_mb = config.get("streaming", {}).get(
            "max_file_size_mb", 100
        )  # 100MB limit

        logger.info(
            f"StreamingProcessor initialized - Max memory: {self.max_memory_usage_mb}MB, "
            f"Buffer size: {self.chunk_buffer_size}, Max file size: {self.max_file_size_mb}MB"
        )

    def can_process_file(self, file_path: Path) -> bool:
        """
        Check if a file can be processed based on size limits.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file can be processed, False if too large
        """
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            return file_size_mb <= self.max_file_size_mb
        except OSError as e:
            logger.error(f"Cannot check file size for {file_path}: {e}")
            return False

    @contextmanager
    def memory_mapped_file(self, file_path: Path):
        """
        Context manager for memory-mapped file access.
        More memory efficient for large files.

        Args:
            file_path: Path to the file to map

        Yields:
            Memory-mapped file object
        """
        f = None
        mapped = None
        try:
            f = open(file_path, "rb")
            if f.readable():
                mapped = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                yield mapped
            else:
                raise IOError(f"File {file_path} is not readable")
        except Exception as e:
            logger.error(f"Error creating memory map for {file_path}: {e}")
            raise
        finally:
            if mapped:
                mapped.close()
            if f:
                f.close()

    def stream_text_chunks(self, file_path: Path) -> Iterator[str]:
        """
        Stream text file content in small chunks to minimize memory usage.

        Args:
            file_path: Path to the text file

        Yields:
            String chunks of the file content
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                while True:
                    chunk = f.read(self.chunk_buffer_size)
                    if not chunk:
                        break
                    yield chunk

        except Exception as e:
            logger.error(f"Error streaming file {file_path}: {e}")
            raise

    def process_large_text_file(
        self, file_path: Path, file_hash: str, chunker_func
    ) -> Iterator[Dict[str, Any]]:
        """
        Process large text files using streaming to minimize memory usage.

        Args:
            file_path: Path to the text file
            file_hash: Unique hash identifier for the file
            chunker_func: Function to chunk text into smaller pieces

        Yields:
            Chunk dictionaries with text and metadata
        """
        logger.info(f"Processing large file with streaming: {file_path.name}")

        # Accumulate text in a rolling buffer for proper sentence/paragraph boundary detection
        text_buffer = ""
        buffer_limit = self.chunk_buffer_size * 4  # 32KB buffer
        chunk_index = 0

        try:
            for file_chunk in self.stream_text_chunks(file_path):
                text_buffer += file_chunk

                # When buffer gets large enough, process it and keep remainder
                if len(text_buffer) >= buffer_limit:
                    # Find a good breaking point (end of sentence or paragraph)
                    break_point = self._find_good_break_point(
                        text_buffer, buffer_limit // 2
                    )

                    # Extract text to process and keep remainder
                    text_to_process = text_buffer[:break_point]
                    text_buffer = text_buffer[break_point:]

                    # Chunk the processed text
                    chunks = chunker_func(
                        raw_text=text_to_process,
                        file_hash=file_hash,
                        chunk_size=self.config["chunking"]["chunk_size"],
                        chunk_overlap=self.config["chunking"]["chunk_overlap"],
                    )

                    # Yield chunks with corrected indices
                    for chunk in chunks:
                        chunk["metadata"]["chunk_index"] = chunk_index
                        chunk["metadata"][
                            "chunk_id"
                        ] = f"{file_hash[:8]}-{chunk_index:04d}"
                        chunk_index += 1
                        yield chunk

            # Process remaining text in buffer
            if text_buffer.strip():
                chunks = chunker_func(
                    raw_text=text_buffer,
                    file_hash=file_hash,
                    chunk_size=self.config["chunking"]["chunk_size"],
                    chunk_overlap=self.config["chunking"]["chunk_overlap"],
                )

                for chunk in chunks:
                    chunk["metadata"]["chunk_index"] = chunk_index
                    chunk["metadata"]["chunk_id"] = f"{file_hash[:8]}-{chunk_index:04d}"
                    chunk_index += 1
                    yield chunk

        except Exception as e:
            logger.error(f"Error in streaming processing of {file_path}: {e}")
            raise

    def _find_good_break_point(self, text: str, min_position: int) -> int:
        """
        Find a good position to break text for processing.
        Tries to break at paragraph or sentence boundaries.

        Args:
            text: Text to find break point in
            min_position: Minimum position to consider for breaking

        Returns:
            Position to break at
        """
        # Look for paragraph breaks first
        for i in range(min_position, len(text)):
            if text[i : i + 2] == "\n\n":
                return i + 2

        # Look for sentence endings
        sentence_endings = ".!?"
        for i in range(min_position, len(text)):
            if text[i] in sentence_endings and i + 1 < len(text) and text[i + 1] == " ":
                return i + 1

        # Look for any whitespace
        for i in range(min_position, len(text)):
            if text[i].isspace():
                return i

        # Fallback to min_position
        return min_position

    def estimate_memory_usage(self, file_path: Path) -> float:
        """
        Estimate memory usage for processing a file.

        Args:
            file_path: Path to the file

        Returns:
            Estimated memory usage in MB
        """
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)

            # Estimate based on:
            # - File size (for text loading)
            # - Chunking overhead (~2x file size for processing)
            # - Embedding vectors (assume ~1KB per chunk, ~2 chunks per KB of text)

            estimated_chunks = (file_size_mb * 1024) // self.config["chunking"][
                "chunk_size"
            ]
            embedding_memory_mb = estimated_chunks * 0.001  # ~1KB per embedding
            processing_overhead = file_size_mb * 0.5  # 50% overhead for processing

            total_estimate = file_size_mb + embedding_memory_mb + processing_overhead

            logger.debug(
                f"Memory estimate for {file_path.name}: {total_estimate:.1f}MB "
                f"(file: {file_size_mb:.1f}MB, embeddings: {embedding_memory_mb:.1f}MB, "
                f"overhead: {processing_overhead:.1f}MB)"
            )

            return total_estimate

        except Exception as e:
            logger.warning(f"Could not estimate memory usage for {file_path}: {e}")
            return float("inf")  # Assume large if we can't estimate

    def should_use_streaming(self, file_path: Path) -> bool:
        """
        Determine if streaming processing should be used for a file.

        Args:
            file_path: Path to the file

        Returns:
            True if streaming should be used
        """
        estimated_memory = self.estimate_memory_usage(file_path)
        available_memory = self.max_memory_usage_mb * 0.7  # Use 70% of available memory

        should_stream = estimated_memory > available_memory

        if should_stream:
            logger.info(
                f"Using streaming for {file_path.name} "
                f"(estimated: {estimated_memory:.1f}MB > available: {available_memory:.1f}MB)"
            )
        else:
            logger.debug(
                f"Using regular processing for {file_path.name} "
                f"(estimated: {estimated_memory:.1f}MB <= available: {available_memory:.1f}MB)"
            )

        return should_stream


class BatchProcessor:
    """
    Adaptive batch processor that adjusts batch sizes based on available memory.
    """

    def __init__(self, config: Dict[str, Any], resource_monitor):
        self.config = config
        self.resource_monitor = resource_monitor
        self.base_batch_size = config["embedding"]["batch_size"]
        self.min_batch_size = max(1, self.base_batch_size // 8)
        self.max_batch_size = self.base_batch_size * 2

        logger.info(
            f"BatchProcessor initialized - Base: {self.base_batch_size}, "
            f"Range: {self.min_batch_size}-{self.max_batch_size}"
        )

    def get_optimal_batch_size(self, total_items: int) -> int:
        """
        Get optimal batch size based on current system resources.

        Args:
            total_items: Total number of items to process

        Returns:
            Optimal batch size for current conditions
        """
        # Get current system resource status
        memory_pressure = self.resource_monitor.get_memory_pressure_level()
        recommended_size, _ = self.resource_monitor.get_adaptive_batch_size(
            self.base_batch_size
        )

        # Adjust based on total items
        if total_items < self.min_batch_size:
            optimal_size = total_items
        elif total_items < recommended_size:
            optimal_size = total_items
        else:
            optimal_size = recommended_size

        # Ensure within bounds
        optimal_size = max(self.min_batch_size, min(self.max_batch_size, optimal_size))

        logger.debug(
            f"Optimal batch size: {optimal_size} "
            f"(memory pressure: {memory_pressure}, total items: {total_items})"
        )

        return optimal_size

    def process_in_batches(
        self, items: List[Any], processor_func, batch_size: Optional[int] = None
    ) -> Iterator[Any]:
        """
        Process items in adaptive batches.

        Args:
            items: List of items to process
            processor_func: Function to process each batch
            batch_size: Optional override for batch size

        Yields:
            Results from processing each batch
        """
        if batch_size is None:
            batch_size = self.get_optimal_batch_size(len(items))

        logger.info(f"Processing {len(items)} items in batches of {batch_size}")

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]

            # Check if we should reduce batch size due to memory pressure
            if self.resource_monitor.should_throttle_processing()[0]:
                logger.warning("High memory pressure detected, reducing batch size")
                new_batch_size = max(self.min_batch_size, batch_size // 2)
                if new_batch_size < len(batch):
                    # Split current batch
                    for j in range(0, len(batch), new_batch_size):
                        mini_batch = batch[j : j + new_batch_size]
                        yield processor_func(mini_batch)
                else:
                    yield processor_func(batch)

                # Update batch size for next iteration
                batch_size = new_batch_size
            else:
                yield processor_func(batch)
