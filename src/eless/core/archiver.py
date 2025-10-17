import pickle
from pathlib import Path
from typing import List, Dict, Any, Union
import logging
import os

# Ensure numpy is in your requirements.txt for vector handling
import numpy as np

logger = logging.getLogger("ELESS.Archiver")


class Archiver:
    """
    Handles the serialization (saving) and deserialization (loading) of
    processed data (chunks and vectors) to and from the cache directory.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initializes the archiver with the cache directory path."""
        self.cache_dir = Path(config["cache"]["directory"])
        # Ensure the cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Archiver initialized, target cache: {self.cache_dir}")

    def _get_path(self, file_hash: str, data_type: str) -> Path:
        """Helper to construct the file path based on hash and data type."""
        if data_type == "chunks":
            extension = ".chunks.pkl"  # Using pickle for list of chunks/metadata
        elif data_type == "vectors":
            extension = ".vectors.npy"  # Using NumPy for efficiency with arrays
        else:
            raise ValueError(f"Unknown data type for archiving: {data_type}")

        return self.cache_dir / f"{file_hash}{extension}"

    # --- Saving Methods ---

    def save_chunks(self, file_hash: str, chunks_with_metadata: List[Dict]):
        """Saves a list of chunks (with metadata) to a pickled file."""
        path = self._get_path(file_hash, "chunks")
        try:
            with open(path, "wb") as f:
                pickle.dump(chunks_with_metadata, f)
            logger.debug(
                f"Saved {len(chunks_with_metadata)} chunks for {file_hash[:8]} to {path.name}"
            )
        except Exception as e:
            logger.error(f"Failed to save chunks for {file_hash[:8]}: {e}")
            raise

    def save_vectors(self, file_hash: str, vectors: np.ndarray):
        """Saves a NumPy array of vectors to a .npy file."""
        path = self._get_path(file_hash, "vectors")
        try:
            np.save(path, vectors)
            logger.debug(
                f"Saved vectors of shape {vectors.shape} for {file_hash[:8]} to {path.name}"
            )
        except Exception as e:
            logger.error(f"Failed to save vectors for {file_hash[:8]}: {e}")
            raise

    # --- Loading Methods ---

    def load_chunks(self, file_hash: str) -> Union[List[Dict], None]:
        """Loads chunks (list of dicts) from the pickled file."""
        path = self._get_path(file_hash, "chunks")
        if not path.exists():
            logger.warning(f"Chunk file not found for hash {file_hash[:8]}.")
            return None

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            logger.debug(f"Loaded {len(data)} chunks for {file_hash[:8]}")
            return data
        except Exception as e:
            logger.error(f"Failed to load chunks for {file_hash[:8]}: {e}")
            self.delete_archived_data(file_hash, "chunks")  # Clean up corrupted file
            return None

    def load_vectors(self, file_hash: str) -> Union[np.ndarray, None]:
        """Loads a NumPy array of vectors from the .npy file."""
        path = self._get_path(file_hash, "vectors")
        if not path.exists():
            logger.warning(f"Vector file not found for hash {file_hash[:8]}.")
            return None

        try:
            vectors = np.load(path)
            logger.debug(f"Loaded vectors (Shape: {vectors.shape}) for {file_hash[:8]}")
            return vectors
        except Exception as e:
            logger.error(f"Failed to load vectors for {file_hash[:8]}: {e}")
            self.delete_archived_data(file_hash, "vectors")  # Clean up corrupted file
            return None

    def validate_cache(self, file_hash: str) -> bool:
        """Validates that both chunks and vectors exist and are loadable for the file."""
        chunks = self.load_chunks(file_hash)
        vectors = self.load_vectors(file_hash)
        return chunks is not None and vectors is not None

    # --- Cleanup Method ---

    def delete_archived_data(self, file_hash: str, data_type: str):
        """Deletes a specific archived file."""
        path = self._get_path(file_hash, data_type)
        if path.exists():
            try:
                os.remove(path)
                logger.info(f"Deleted corrupted/old file: {path.name}")
            except OSError as e:
                logger.error(f"Error deleting file {path.name}: {e}")
