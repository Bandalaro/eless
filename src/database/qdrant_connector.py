import logging
from typing import Dict, Any, List
import os
from .db_connector_base import DBConnectorBase
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger('ELESS.QdrantConnector')

class QdrantConnector(DBConnectorBase):
    """Concrete connector for the Qdrant vector database."""
    
    def __init__(self, config: Dict[str, Any], connection_name: str, dimension: int):
        super().__init__(config, connection_name, dimension)
        self.client = None
        self.collection_name = self.db_config.get('collection_name', 'eless_qdrant_collection')
        self.host = self.db_config.get('host', 'localhost')
        self.port = self.db_config.get('port', 6333)
        self.api_key = self.db_config.get('api_key') or os.environ.get('QDRANT_API_KEY')

    def connect(self):
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(host=self.host, port=self.port, api_key=self.api_key)
            
            # Check for collection and create if needed
            collections = self.client.get_collections().collections
            if self.collection_name not in [c.name for c in collections]:
                logger.info(f"Qdrant collection '{self.collection_name}' not found. Creating...")
                self.client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.dimension, 
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Qdrant collection '{self.collection_name}' created.")
            
        except Exception as e:
            logger.error(f"Failed to connect or set up Qdrant: {e}")
            raise

    def upsert_batch(self, vectors: List[Dict[str, Any]]):
        if not self.client: raise ConnectionError("Qdrant client not initialized.")
        if not vectors: return

        points = []
        for v in vectors:
            # Qdrant uses 'points' for upserting
            points.append(
                models.PointStruct(
                    id=v['id'],
                    vector=v['vector'],
                    payload=v['metadata']
                )
            )

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
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

    def check_connection(self) -> bool:
        return self.client is not None and self.client.get_collection(self.collection_name) is not None