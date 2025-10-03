import logging
from typing import Dict, Any, List
from pathlib import Path

# Import the base class
from .db_connector_base import DBConnectorBase

# Import the necessary LangChain and Chroma components
# NOTE: We use the `langchain_community` package for vector stores
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.embeddings import (
    SentenceTransformerEmbeddings,
)  # Placeholder for a custom embedding function if needed
from chromadb.utils import embedding_functions

logger = logging.getLogger("ELESS.ChromaConnector")


class ChromaDBConnector(DBConnectorBase):
    """
    Concrete connector for the Chroma vector database, using the LangChain wrapper.
    Supports both persistent (disk) and in-memory modes.
    """

    def __init__(self, config: Dict[str, Any], connection_name: str, dimension: int):
        super().__init__(config, connection_name, dimension)

        self.vector_store = None  # The Chroma vector store instance (LangChain wrapper)

        # Chroma-specific configuration
        self.path = self.db_config.get("path", "./chroma_db")
        self.collection_name = self.db_config.get("collection_name", "eless_vectors")
        self.persist = self.db_config.get("persist", True)

        # NOTE: LangChain's Chroma wrapper requires an embedding function,
        # even if vectors are pre-computed. We use a pass-through function
        # to tell the store *not* to embed the input texts.
        self.embedding_function = embedding_functions.pass_through_embedding_function

    def connect(self):
        """
        Initializes the Chroma vector store instance (LangChain wrapper).
        """
        try:
            # Determine the client settings based on persistence config
            client_settings = {}
            if self.persist:
                # Configuration for PersistentClient
                client_settings = {"persist_directory": str(Path(self.path))}
                logger.info(f"Chroma client initialized (Persistent) at: {self.path}")
            else:
                # For in-memory, no settings are needed beyond the defaults
                logger.info("Chroma client initialized (In-Memory).")

            # Instantiate the LangChain Chroma vector store
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,  # Pass-through function
                **client_settings,
            )

            logger.info(
                f"LangChain Chroma vector store collection '{self.collection_name}' ready."
            )

        except Exception as e:
            logger.error(f"Failed to connect and initialize LangChain Chroma: {e}")
            raise

    def upsert_batch(self, vectors: List[Dict[str, Any]]):
        """
        Inserts or updates a batch of vector-chunk data into the Chroma collection.

        Args:
            vectors: A list of dicts, each with 'id', 'vector' (list), and 'metadata'.
        """
        if not self.vector_store:
            raise ConnectionError(
                "Chroma vector store is not initialized. Run connect() first."
            )
        if not vectors:
            return

        # LangChain's upsert method for Chroma requires the following arguments:
        ids = [v["id"] for v in vectors]
        embeddings = [v["vector"] for v in vectors]
        metadatas = [v["metadata"] for v in vectors]

        # Chroma's underlying client is available via ._client and the collection via ._collection
        # We need to use the raw chromadb client method for upsert with pre-computed vectors.
        try:
            # Access the underlying chromadb collection to perform the upsert with pre-computed vectors
            # The LangChain wrapper's `add_embeddings` or `add_documents` methods do not
            # easily support upserting IDs and pre-computed vectors together.
            self.vector_store._collection.upsert(
                ids=ids, embeddings=embeddings, metadatas=metadatas
            )
            logger.debug(
                f"Successfully upserted {len(ids)} vectors to LangChain Chroma collection '{self.collection_name}'."
            )

        except Exception as e:
            logger.error(
                f"LangChain Chroma upsert failed for batch of size {len(ids)}: {e}"
            )
            raise

    def close(self):
        """
        Closes the connection. For LangChain's Chroma wrapper using PersistentClient,
        this ensures data is written to disk.
        """
        if self.vector_store and self.persist:
            try:
                # Access the underlying client to call the persist method
                self.vector_store._client.persist()
                logger.info(
                    "Chroma persistent client data flushed to disk via LangChain wrapper."
                )
            except Exception as e:
                logger.warning(f"Error during Chroma client persistence/cleanup: {e}")

        self.vector_store = None

    def check_connection(self) -> bool:
        """Verifies the client and collection are ready."""
        # Check if the vector store instance exists
        if self.vector_store is None:
            return False

        # Check if the underlying Chroma client and collection are accessible
        try:
            # Access the underlying chromadb client and check a property
            client_status = self.vector_store._client is not None
            collection_status = self.vector_store._collection is not None
            return client_status and collection_status
        except Exception:
            return False
