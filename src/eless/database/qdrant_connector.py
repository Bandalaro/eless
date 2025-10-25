import logging
from typing import Dict, Any, List
import os
import uuid
from .db_connector_base import DBConnectorBase
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger("ELESS.QdrantConnector")


class QdrantConnector(DBConnectorBase):
    """Concrete connector for the Qdrant vector database."""

    def __init__(self, config: Dict[str, Any], connection_name: str, dimension: int):
        super().__init__(config, connection_name, dimension)
        self.client = None
        self.collection_name = self.db_config.get(
            "collection_name", "eless_qdrant_collection"
        )
        self.path = self.db_config.get("path")
        self.host = self.db_config.get("host", "localhost")
        self.port = self.db_config.get("port", 6333)
        self.api_key = self.db_config.get("api_key") or os.environ.get("QDRANT_API_KEY")

    def connect(self):
        try:
            # Check if Qdrant instance is running
            self._check_qdrant_running()

            # Initialize Qdrant client
            if self.path:
                self.client = QdrantClient(path=self.path)
            else:
                self.client = QdrantClient(
                    host=self.host, port=self.port, api_key=self.api_key
                )

            # Check for collection and create if needed
            if not self.client.collection_exists(self.collection_name):
                logger.info(
                    f"Qdrant collection '{self.collection_name}' not found. Creating..."
                )
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.dimension, distance=models.Distance.COSINE
                    ),
                )
                logger.info(f"Qdrant collection '{self.collection_name}' created.")

        except Exception as e:
            logger.error(f"Failed to connect or set up Qdrant: {e}")
            raise

    def _check_qdrant_running(self):
        """Check if Qdrant instance is running."""
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            if result != 0:
                raise ConnectionError(
                    f"Qdrant instance not running at http://{self.host}:{self.port}. "
                    "Start the Qdrant server (e.g., 'docker run -p 6333:6333 qdrant/qdrant') "
                    "and ensure the URL is accessible."
                )
            logger.info(f"Qdrant instance confirmed running on {self.host}:{self.port}")
        except Exception as e:
            raise ConnectionError(f"Failed to check Qdrant status: {e}")

    def upsert_batch(self, vectors: List[Dict[str, Any]]):
        if not self.client:
            raise ConnectionError("Qdrant client not initialized.")
        if not vectors:
            return

        points = []
        for v in vectors:
            # Qdrant uses 'points' for upserting, use UUID for id
            point_id = str(uuid.uuid4())
            payload = {**v["metadata"], "file_id": v["id"]}
            points.append(
                models.PointStruct(id=point_id, vector=v["vector"], payload=payload)
            )

        try:
            self.client.upsert(
                collection_name=self.collection_name, points=points, wait=True
            )
            logger.debug(f"Successfully upserted {len(points)} vectors to Qdrant.")
        except UnexpectedResponse as e:
            logger.error(f"Qdrant upsert failed: {e.content}")
            raise
        except Exception as e:
            logger.error(f"Qdrant upsert failed: {e}")
            raise

    def close(self):
        self.client = None
        logger.debug("Qdrant connector closed.")

    def search(
        self, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Searches the Qdrant collection for similar vectors.

        Args:
            query_vector: Query vector
            limit: Maximum number of results

        Returns:
            List of search results
        """
        if not self.client:
            raise ConnectionError("Qdrant client not initialized.")

        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
            )
            results = []
            for hit in search_result:
                results.append(
                    {
                        "content": (
                            hit.payload.get("content", "") if hit.payload else ""
                        ),
                        "metadata": hit.payload if hit.payload else {},
                        "score": hit.score,
                    }
                )
            return results
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    def check_connection(self) -> bool:
        return (
            self.client is not None
            and self.client.get_collection(self.collection_name) is not None
        )
