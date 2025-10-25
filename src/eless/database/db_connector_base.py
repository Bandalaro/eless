import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

logger = logging.getLogger("ELESS.DBConnector")


class DBConnectorBase(ABC):
    """
    Abstract Base Class for all vector database connectors.
    All concrete database implementations (e.g., PineconeConnector)
    must inherit from this class and implement its abstract methods.
    """

    def __init__(self, config: Dict[str, Any], connection_name: str, dimension: int):
        """
        Initializes the connector with configuration, the connection name
        (from default_config.yaml), and the required embedding dimension.
        """
        self.config = config
        self.connection_name = connection_name
        self.db_config = config["databases"]["connections"][connection_name]
        self.dimension = dimension
        logger.info(
            f"Base connector initialized for {connection_name} (Dim: {dimension})."
        )

    @abstractmethod
    def connect(self):
        """
        Establishes the connection to the specific vector database and
        performs any necessary setup (e.g., ensuring index/collection exists).
        """
        pass

    @abstractmethod
    def upsert_batch(self, vectors: List[Dict[str, Any]]):
        """
        Inserts or updates a batch of vector-chunk data into the database.

        Args:
            vectors: A list of dictionaries, where each dict must contain
                     'id', 'vector', and 'metadata'.
        """
        pass

    @abstractmethod
    def search(
        self, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Searches the database for similar vectors based on the query vector.

        Args:
            query_vector: Query vector
            limit: Maximum number of results to return

        Returns:
            List of search results with scores and metadata
        """
        pass

    @abstractmethod
    def close(self):
        """
        Closes the connection or releases resources used by the connector.
        """
        pass

    @abstractmethod
    def check_connection(self) -> bool:
        """
        Verifies that the connection is active and the target resource
        (index/collection) is ready for upsertion.
        """
        pass

    def get_connection_name(self) -> str:
        """Helper to retrieve the connection name."""
        return self.connection_name


# Example usage of the abstract method contract:
#
# class ChromaConnector(DBConnectorBase):
#     def connect(self):
#         # ChromaDB specific connection logic
#         ...
#     def upsert_batch(self, vectors):
#         # ChromaDB specific upsert logic
#         ...
#     # ... implement other abstract methods
