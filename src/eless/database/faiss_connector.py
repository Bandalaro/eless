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
        self.id_map: Dict[int, str] = {}  # int_id -> original_id
        self.id_counter = 0
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
                # Create a new index with ID mapping
                self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.dimension))
                logger.info("Faiss index created (IndexIDMap with IndexFlatL2).")

        except Exception as e:
            logger.error(f"Failed to connect or set up Faiss: {e}")
            raise

    def upsert_batch(self, vectors: List[Dict[str, Any]]):
        if not self.index:
            raise ConnectionError("Faiss index not initialized.")
        if not vectors:
            return

        # 1. Prepare vectors and ids for Faiss
        vector_array = np.array([v["vector"] for v in vectors], dtype="float32")
        ids = []

        # 2. Assign int ids and store mappings
        for v in vectors:
            int_id = self.id_counter
            self.id_counter += 1
            ids.append(int_id)
            self.id_map[int_id] = v["id"]
            self.data_store[v["id"]] = v["metadata"]

        ids_array = np.array(ids, dtype="int64")

        # 3. Add to Faiss index with ids
        try:
            self.index.add_with_ids(vector_array, ids_array)
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

    def search(
        self, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Searches the Faiss index for similar vectors.

        Args:
            query_vector: Query vector
            limit: Maximum number of results

        Returns:
            List of search results
        """
        if not self.index:
            raise ConnectionError("Faiss index not initialized.")

        try:
            query_array = np.array([query_vector], dtype="float32")
            distances, indices = self.index.search(query_array, limit)
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1:  # Valid index
                    original_id = self.id_map.get(idx)
                    if original_id:
                        metadata = self.data_store.get(original_id, {})
                        results.append(
                            {
                                "content": metadata.get("content", ""),
                                "metadata": metadata,
                                "score": float(distances[0][i]),
                            }
                        )
            return results
        except Exception as e:
            logger.error(f"Faiss search failed: {e}")
            return []

    def check_connection(self) -> bool:
        return self.index is not None
