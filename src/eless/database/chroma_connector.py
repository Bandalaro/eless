import logging
from typing import Dict, Any, List
from pathlib import Path

# Import the base class
from .db_connector_base import DBConnectorBase

# Import ChromaDB directly for more reliable operation
import chromadb
from chromadb.config import Settings

logger = logging.getLogger("ELESS.ChromaConnector")


class PassThroughEmbeddingFunction:
    """Custom pass-through embedding function for pre-computed embeddings."""

    def __call__(self, input):
        # Return the input as-is since embeddings are pre-computed
        return input

    def embed_documents(self, texts):
        return texts

    def embed_query(self, text):
        return text


class ChromaDBConnector(DBConnectorBase):
    """
    Concrete connector for the Chroma vector database, using the LangChain wrapper.
    Supports both persistent (disk) and in-memory modes.
    """

    def __init__(self, config: Dict[str, Any], connection_name: str, dimension: int):
        super().__init__(config, connection_name, dimension)

        self.client = None  # Raw ChromaDB client
        self.collection = None  # ChromaDB collection

        # Chroma-specific configuration
        self.path = self.db_config.get("path", "./chroma_db")
        self.collection_name = self.db_config.get("collection_name", "eless_vectors")
        self.persist = self.db_config.get("persist", True)

    def connect(self):
        """
        Initializes the ChromaDB client and collection.
        """
        try:
            if self.persist:
                # Persistent client
                self.client = chromadb.PersistentClient(path=str(Path(self.path)))
                logger.info(f"ChromaDB persistent client initialized at: {self.path}")
            else:
                # In-memory client
                self.client = chromadb.EphemeralClient()
                logger.info("ChromaDB in-memory client initialized")

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name, metadata={"dimension": self.dimension}
            )

            logger.info(f"ChromaDB collection '{self.collection_name}' ready.")

        except Exception as e:
            logger.error(f"Failed to connect and initialize ChromaDB: {e}")
            raise

    def upsert_batch(self, vectors: List[Dict[str, Any]]):
        """
        Inserts or updates a batch of vector-chunk data into the Chroma collection.

        Args:
            vectors: A list of dicts, each with 'id', 'vector' (list), and 'metadata'.
        """
        if not self.collection:
            raise ConnectionError(
                "ChromaDB collection is not initialized. Run connect() first."
            )
        if not vectors:
            return

        # Extract data for ChromaDB upsert
        ids = [v["id"] for v in vectors]
        embeddings = [v["vector"] for v in vectors]
        metadatas = [v["metadata"] for v in vectors]

        try:
            self.collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas)
            logger.debug(
                f"Successfully upserted {len(ids)} vectors to ChromaDB collection '{self.collection_name}'."
            )

        except Exception as e:
            logger.error(f"Failed to upsert batch to ChromaDB. Error: {e}")
            raise

    def search(
        self, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Searches the Chroma collection for similar vectors.

        Args:
            query_vector: Query vector
            limit: Maximum number of results

        Returns:
            List of search results
        """
        if not self.collection:
            raise ConnectionError("Chroma collection is not initialized.")

        try:
            # Use raw ChromaDB query
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
            # Format results
            formatted_results = []
            if results and "documents" in results and results["documents"]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append(
                        {
                            "content": results["documents"][0][i],
                            "metadata": (
                                results["metadatas"][0][i]
                                if results["metadatas"] and results["metadatas"][0]
                                else {}
                            ),
                            "score": (
                                results["distances"][0][i]
                                if results["distances"] and results["distances"][0]
                                else 0.0
                            ),
                        }
                    )
            return formatted_results
        except Exception as e:
            logger.error(f"Chroma search failed: {e}")
            return []

    def check_connection(self) -> bool:
        """Verifies the client and collection are ready."""
        return self.client is not None and self.collection is not None

    def close(self):
        """
        Closes the ChromaDB connection (alias for disconnect).
        """
        self.disconnect()

    def disconnect(self):
        """
        Cleans up the ChromaDB connection.
        """
        if self.client:
            # ChromaDB client doesn't have explicit disconnect, just clear references
            self.collection = None
            self.client = None
            logger.info("ChromaDB client disconnected.")
