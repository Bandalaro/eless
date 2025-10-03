import logging
from typing import Dict, Any, List
from pathlib import Path
import numpy as np
import faiss
import os
from .db_connector_base import DBConnectorBase

logger = logging.getLogger("ELESS.FaissConnector")


class FaissConnector(DBConnectorBase):
    """Concrete connector for the local/in-memory Faiss index."""

    def __init__(self, config: Dict[str, Any], connection_name: str, dimension: int):
        super().__init__(config, connection_name, dimension)
        self.index: faiss.Index = None
        self.index_file = self.db_config.get("index_file", "eless_faiss.index")
        self.data_store: Dict[str, Dict[str, Any]] = (
            {}
        )  # To store metadata since Faiss only stores vectors
        self.save_path = Path(
            self.db_config.get("save_path", "./eless_cache/faiss_data")
        )
        self.save_path.mkdir(parents=True, exist_ok=True)
        self.save_file = self.save_path / self.index_file

    def connect(self):
        try:
            if self.save_file.exists():
                # Load existing index
                self.index = faiss.read_index(str(self.save_file))
                logger.info(f"Faiss index loaded from {self.save_file}")
                # Load metadata store (optional, for full recovery)
                # NOTE: Metadata loading is omitted for brevity but required for full functionality
            else:
                # Create a new index (e.g., Euclidean distance)
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info("Faiss index created (IndexFlatL2).")

        except Exception as e:
            logger.error(f"Failed to connect or set up Faiss: {e}")
            raise

    def upsert_batch(self, vectors: List[Dict[str, Any]]):
        if not self.index:
            raise ConnectionError("Faiss index not initialized.")
        if not vectors:
            return

        # 1. Prepare vectors for Faiss
        vector_array = np.array([v["vector"] for v in vectors], dtype="float32")

        # 2. Store metadata (Crucial, as Faiss doesn't store metadata)
        for v in vectors:
            # We use the id to map vector to metadata
            self.data_store[v["id"]] = v["metadata"]

        # 3. Add to Faiss index
        try:
            # Faiss doesn't have an explicit upsert; we re-add (it handles duplicates/ID tracking based on implementation)
            # For IndexFlat, we just add; ID tracking would require IndexIDMap
            self.index.add(vector_array)
            logger.debug(f"Successfully added {len(vectors)} vectors to Faiss index.")
        except Exception as e:
            logger.error(f"Faiss upsert failed: {e}")
            raise

    def close(self):
        """Save the index to disk upon closing for persistence."""
        if self.index:
            try:
                faiss.write_index(self.index, str(self.save_file))
                logger.info(f"Faiss index saved to {self.save_file}")
                # Also save metadata store here
            except Exception as e:
                logger.warning(f"Error saving Faiss index: {e}")
        self.index = None
        self.data_store = {}

    def check_connection(self) -> bool:
        return self.index is not None
