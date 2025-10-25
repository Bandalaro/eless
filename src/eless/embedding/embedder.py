import logging
from typing import Dict, Any, List, Generator, Union

import numpy as np

# Import components from the core and embedding layers
from ..core.state_manager import StateManager, FileStatus
from ..core.archiver import Archiver
from .model_loader import ModelLoader
from ..processing.streaming_processor import BatchProcessor


logger = logging.getLogger("ELESS.Embedder")


class Embedder:
    """
    Manages the process of taking text chunks, converting them to vectors
    using a shared model instance, and archiving the results.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        state_manager: StateManager,
        archiver: Archiver,
        model_loader: ModelLoader = None,
        resource_monitor=None,
        batch_processor: BatchProcessor = None,
    ):
        self.config = config
        self.state_manager = state_manager
        self.archiver = archiver
        self.resource_monitor = resource_monitor
        # Use shared model instance if provided, otherwise create new one
        self.model_loader = model_loader if model_loader else ModelLoader(config)
        self.batch_size = config["embedding"]["batch_size"]

        # Use provided batch processor or create one if resource monitor is available
        if batch_processor:
            self.batch_processor = batch_processor
        elif resource_monitor:
            self.batch_processor = BatchProcessor(config, resource_monitor)
        else:
            self.batch_processor = None

        logger.info(
            f"Embedder initialized with batch size: {self.batch_size}, "
            f"adaptive batching: {self.batch_processor is not None}"
        )

    def _get_vectors_for_file(self, file_hash: str) -> Union[np.ndarray, None]:
        """
        Attempts to load vectors from the cache for a given file hash.
        Used for the 'skip/resume' logic.
        """
        vectors = self.archiver.load_vectors(file_hash)
        if vectors is not None:
            logger.info(f"Resuming {file_hash[:8]}. Loaded vectors from cache.")
            # Update status to EMBEDDED if it was previously CHUNKED or SCANNED
            self.state_manager.add_or_update_file(file_hash, FileStatus.EMBEDDED)
            return vectors
        return None

    def embed_file_chunks(
        self, file_hash: str, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Embed all chunks for a single file.

        Args:
            file_hash: Unique identifier for the file
            chunks: List of chunk dictionaries with text and metadata

        Returns:
            List of chunks with vectors attached, or empty list on error
        """
        if not chunks:
            return []

        current_status = self.state_manager.get_status(file_hash)

        # Check if already embedded and cached
        if current_status == FileStatus.EMBEDDED:
            cached_vectors = self._get_vectors_for_file(file_hash)
            if cached_vectors is not None and len(cached_vectors) == len(chunks):
                logger.info(f"File {file_hash[:8]} using cached embeddings")
                for i, chunk in enumerate(chunks):
                    chunk["vector"] = cached_vectors[i]
                return chunks

        # Extract texts for embedding
        texts = [chunk["text"] for chunk in chunks]

        try:
            # Use adaptive batching if available
            if self.batch_processor and len(texts) > self.batch_size:
                logger.info(f"Using adaptive batching for {len(texts)} chunks")
                vectors = self._embed_with_adaptive_batching(texts)
            else:
                # Traditional single batch embedding
                vectors = self.model_loader.embed_chunks(texts)

            if vectors.shape[0] != len(texts):
                logger.error(
                    f"Vector count mismatch for {file_hash[:8]}. Expected {len(texts)}, got {vectors.shape[0]}"
                )
                return []

            # Attach vectors to chunks
            for i, chunk in enumerate(chunks):
                chunk["vector"] = vectors[i]

            # Archive vectors and update state
            self.archiver.save_vectors(file_hash, vectors)
            # Update status (path is preserved automatically)
            self.state_manager.add_or_update_file(file_hash, FileStatus.EMBEDDED)
            logger.info(
                f"File {file_hash[:8]}: Generated and cached {vectors.shape[0]} embeddings"
            )

            return chunks

        except Exception as e:
            logger.error(
                f"Failed to embed chunks for file {file_hash[:8]}: {e}", exc_info=True
            )
            self.state_manager.add_or_update_file(
                file_hash, FileStatus.ERROR, metadata={"error": str(e)}
            )
            return []

    def _embed_with_adaptive_batching(self, texts: List[str]) -> np.ndarray:
        """
        Embed texts using adaptive batching based on available memory.

        Args:
            texts: List of text strings to embed

        Returns:
            Array of embedding vectors
        """
        if not self.batch_processor:
            # Fallback to standard batching
            return self.model_loader.embed_chunks(texts)

        # Process texts in adaptive batches
        all_vectors = []

        for batch_vectors in self.batch_processor.process_in_batches(
            texts, self.model_loader.embed_chunks
        ):
            all_vectors.extend(batch_vectors)

        # Convert to numpy array
        return np.vstack(all_vectors)

    def embed_chunks_streaming(
        self, chunks_generator: Generator[Dict[str, Any], None, None], file_hash: str
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Embed chunks from a streaming generator for memory-efficient processing.

        Args:
            chunks_generator: Generator yielding chunk dictionaries
            file_hash: Unique identifier for the file

        Yields:
            Chunks with vectors attached
        """
        chunk_batch = []
        batch_size = (
            self.batch_processor.get_optimal_batch_size(self.batch_size)
            if self.batch_processor
            else self.batch_size
        )

        logger.info(
            f"Starting streaming embedding for file {file_hash[:8]} with batch size {batch_size}"
        )

        try:
            for chunk in chunks_generator:
                chunk_batch.append(chunk)

                # Process when batch is full
                if len(chunk_batch) >= batch_size:
                    embedded_chunks = self._process_chunk_batch(chunk_batch, file_hash)
                    for embedded_chunk in embedded_chunks:
                        yield embedded_chunk
                    chunk_batch = []

                    # Update batch size if using adaptive processing
                    if self.batch_processor:
                        batch_size = self.batch_processor.get_optimal_batch_size(
                            batch_size
                        )

            # Process any remaining chunks
            if chunk_batch:
                embedded_chunks = self._process_chunk_batch(chunk_batch, file_hash)
                for embedded_chunk in embedded_chunks:
                    yield embedded_chunk

            logger.info(f"Completed streaming embedding for file {file_hash[:8]}")

        except Exception as e:
            logger.error(
                f"Error in streaming embedding for file {file_hash[:8]}: {e}",
                exc_info=True,
            )
            self.state_manager.add_or_update_file(
                file_hash, FileStatus.ERROR, metadata={"error": str(e)}
            )

    def _process_chunk_batch(
        self, chunk_batch: List[Dict[str, Any]], file_hash: str
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of chunks for embedding.

        Args:
            chunk_batch: List of chunk dictionaries to embed
            file_hash: Unique identifier for the file

        Returns:
            List of chunks with vectors attached
        """
        if not chunk_batch:
            return []

        texts = [chunk["text"] for chunk in chunk_batch]

        try:
            vectors = self.model_loader.embed_chunks(texts)

            if vectors.shape[0] != len(texts):
                logger.error(
                    f"Vector count mismatch for batch from {file_hash[:8]}. Expected {len(texts)}, got {vectors.shape[0]}"
                )
                return []

            # Attach vectors to chunks
            for i, chunk in enumerate(chunk_batch):
                chunk["vector"] = vectors[i]

            return chunk_batch

        except Exception as e:
            logger.error(
                f"Failed to embed chunk batch from file {file_hash[:8]}: {e}",
                exc_info=True,
            )
            return []

    def embed_and_archive_chunks(
        self, chunks_generator: Generator[Dict[str, Any], None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Embed chunks from a generator and archive them.

        Args:
            chunks_generator: Generator yielding chunk dictionaries

        Yields:
            Chunks with vectors attached
        """
        from collections import defaultdict

        file_chunks = defaultdict(list)

        try:
            for chunk in chunks_generator:
                file_hash = chunk["metadata"]["file_hash"]
                file_chunks[file_hash].append(chunk)

            # Process each file's chunks
            for file_hash, chunks in file_chunks.items():
                embedded_chunks = self.embed_file_chunks(file_hash, chunks)
                for chunk in embedded_chunks:
                    yield chunk

            logger.info("Completed embedding and archiving")

        except Exception as e:
            logger.error(f"Error in embedding and archiving: {e}", exc_info=True)

    def _process_chunk_batch_for_archive(
        self, chunk_batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of chunks for embedding and archiving.

        Args:
            chunk_batch: List of chunk dictionaries to embed

        Returns:
            List of chunks with vectors attached
        """
        if not chunk_batch:
            return []

        texts = [chunk["text"] for chunk in chunk_batch]

        try:
            vectors = self.model_loader.embed_chunks(texts)

            if vectors.shape[0] != len(texts):
                logger.error(
                    f"Vector count mismatch for batch. Expected {len(texts)}, got {vectors.shape[0]}"
                )
                return []

            # Attach vectors to chunks
            for i, chunk in enumerate(chunk_batch):
                chunk["vector"] = vectors[i]

            return chunk_batch

        except Exception as e:
            logger.error(f"Failed to embed chunk batch: {e}", exc_info=True)
            return []
