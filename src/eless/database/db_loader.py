import logging
from typing import Dict, Any, List, Generator, Optional

# Import the base connector and components from other layers
from .db_connector_base import DBConnectorBase
from ..core.state_manager import StateManager, FileStatus
from ..core.logging_config import log_performance

# Import ModelLoader instead of Embedder to match the actual usage
from ..embedding.model_loader import ModelLoader

# Initialize logger early
logger = logging.getLogger("ELESS.DBLoader")

# Import all concrete connector classes with fallback
try:
    from .chroma_connector import ChromaDBConnector

    CHROMA_AVAILABLE = True
except ImportError:
    logger.warning(
        "ChromaDB connector not available - install chromadb and langchain-community"
    )
    ChromaDBConnector = None
    CHROMA_AVAILABLE = False

try:
    from .qdrant_connector import QdrantConnector

    QDRANT_AVAILABLE = True
except ImportError:
    logger.warning("Qdrant connector not available - install qdrant-client")
    QdrantConnector = None
    QDRANT_AVAILABLE = False

try:
    from .faiss_connector import FaissConnector

    FAISS_AVAILABLE = True
except ImportError:
    logger.warning("FAISS connector not available - install faiss-cpu or faiss-gpu")
    FaissConnector = None
    FAISS_AVAILABLE = False

try:
    from .postgresql_connector import PostgreSQLConnector

    POSTGRESQL_AVAILABLE = True
except ImportError:
    logger.warning("PostgreSQL connector not available - install psycopg2-binary")
    PostgreSQLConnector = None
    POSTGRESQL_AVAILABLE = False

try:
    from .cassandra_connector import CassandraConnector

    CASSANDRA_AVAILABLE = True
except ImportError:
    logger.warning("Cassandra connector not available - install cassandra-driver")
    CassandraConnector = None
    CASSANDRA_AVAILABLE = False


class DatabaseLoader:
    """
    Manages connections to multiple vector databases and loads batches
    of vectors and chunks into them.
    """

    def __init__(
        self, config: Dict[str, Any], state_manager: StateManager, embedding_model
    ):
        self.config = config
        self.state_manager = state_manager
        self.embedding_model = embedding_model
        self.batch_size = config["databases"]["batch_size"]

        # Get the embedding dimension from the config or model
        if embedding_model and hasattr(
            embedding_model, "get_sentence_embedding_dimension"
        ):
            self.embedding_dimension = (
                embedding_model.get_sentence_embedding_dimension()
            )
        else:
            self.embedding_dimension = config["embedding"]["dimension"]

        logger.info(
            f"DatabaseLoader initializing with dimension: {self.embedding_dimension}"
        )

        # Dictionary to hold active database connector instances
        self.active_connectors: Dict[str, DBConnectorBase] = {}

        # Call the updated initialization method
        self._initialize_connectors()
        logger.info(
            f"DatabaseLoader initialized. Active targets: {list(self.active_connectors.keys())}"
        )

    def initialize_database_connections(self):
        """Public method to initialize database connections."""
        self._initialize_connectors()

    @log_performance("ELESS.DBLoader")
    def _initialize_connectors(self):
        """
        Loads the target connection names from the config and initializes
        the corresponding connector classes.
        """
        logger.info("Initializing database connectors...")

        # --- CONNECTOR MAPPING ---
        # Maps the 'type' field in the config to the concrete Python class
        CONNECTOR_MAP = {}

        # Add connectors conditionally based on availability
        if CHROMA_AVAILABLE:
            CONNECTOR_MAP["chroma"] = ChromaDBConnector
        if QDRANT_AVAILABLE:
            CONNECTOR_MAP["qdrant"] = QdrantConnector
        if FAISS_AVAILABLE:
            CONNECTOR_MAP["faiss"] = FaissConnector
        if POSTGRESQL_AVAILABLE:
            CONNECTOR_MAP["postgresql"] = PostgreSQLConnector
        if CASSANDRA_AVAILABLE:
            CONNECTOR_MAP["cassandra"] = CassandraConnector
        # -------------------------

        target_names = self.config["databases"]["targets"]
        # Filter to only available types
        available_targets = [name for name in target_names if name in CONNECTOR_MAP]
        if set(target_names) != set(available_targets):
            logger.warning(
                f"Some targets not available: {set(target_names) - set(available_targets)}. Using: {available_targets}"
            )
        target_names = available_targets
        logger.info(f"Target databases from config: {target_names}")

        for name in target_names:
            logger.debug(f"Initializing connector for: {name}")
            connection_config = self.config["databases"]["connections"].get(name)

            if not connection_config:
                logger.error(
                    f"Configuration for database connection '{name}' not found in 'connections'. Skipping."
                )
                continue

            db_type = connection_config.get("type")

            if not db_type:
                logger.error(
                    f"Connection '{name}' is missing the required 'type' field. Skipping."
                )
                continue

            if db_type in CONNECTOR_MAP:
                try:
                    connector_class = CONNECTOR_MAP[db_type]
                    logger.debug(f"Creating {db_type} connector for '{name}'")

                    # 1. Instantiate the connector
                    connector = connector_class(
                        self.config, name, self.embedding_dimension
                    )

                    # 2. Attempt connection and setup
                    logger.debug(f"Connecting to '{name}'...")
                    connector.connect()

                    # 3. Verify connection status
                    if connector.check_connection():
                        self.active_connectors[name] = connector
                        logger.info(f"✓ Successfully connected to '{name}' ({db_type})")
                    else:
                        logger.error(
                            f"✗ Connector '{name}' failed connection check after setup"
                        )

                except Exception as e:
                    logger.error(
                        f"✗ Failed to initialize/connect to DB '{name}' (Type: {db_type}): {e}",
                        exc_info=True,
                    )
            else:
                logger.error(
                    f"Unknown database type '{db_type}' configured for connection '{name}'. Available types: {list(CONNECTOR_MAP.keys())}"
                )

        logger.info(
            f"Database connector initialization complete. Active: {len(self.active_connectors)}/{len(target_names)}"
        )

    def load_data(
        self, embedded_chunk_generator: Generator[Dict[str, Any], None, None]
    ):
        """
        Receives embedded chunks, organizes them into batches, and upserts
        them to all active database targets.
        """
        if not self.active_connectors:
            logger.warning(
                "No active database connections. Data will not be persisted."
            )
            return

        batch: List[Dict[str, Any]] = []
        # Use a set to track file hashes that were processed in this run
        file_hashes_in_run: Dict[str, bool] = (
            {}
        )  # {file_hash: True if all DBs upserted}

        for chunk_data in embedded_chunk_generator:

            # 1. Prepare data for upsert
            file_hash = chunk_data["metadata"]["file_hash"]
            chunk_id = chunk_data["metadata"]["chunk_id"]

            # Structure required by the DB connectors
            db_entry = {
                # Ensure vector is a List or tuple for JSON serialization/DB API, not NumPy array
                "id": chunk_id,
                "vector": chunk_data["vector"].tolist(),
                "metadata": chunk_data["metadata"],  # Includes hash, index, etc.
            }
            batch.append(db_entry)
            file_hashes_in_run[file_hash] = file_hashes_in_run.get(file_hash, True)

            # 2. Process batch if full
            if len(batch) >= self.batch_size:
                self._upsert_batch(batch, file_hashes_in_run)
                batch = []

        # 3. Process the final, partial batch
        if batch:
            self._upsert_batch(batch, file_hashes_in_run)

        # 4. Final state update
        self._update_file_status(file_hashes_in_run)
        logger.info("Database loading process complete.")

    def _upsert_batch(
        self, batch: List[Dict[str, Any]], file_hashes_in_run: Dict[str, bool]
    ):
        """Sends the batch to all active database connectors and tracks success."""
        logger.info(
            f"Upserting batch of size {len(batch)} to {len(self.active_connectors)} targets."
        )

        # Fan-out to all target databases
        for name, connector in self.active_connectors.items():
            try:
                connector.upsert_batch(batch)
                logger.debug(f"Successfully upserted batch to {name}.")
            except Exception as e:
                logger.error(f"Failed to upsert batch to {name}. Error: {e}")
                # CRITICAL: Mark all files in this failed batch as NOT fully loaded
                for entry in batch:
                    file_hash = entry["metadata"]["file_hash"]
                    file_hashes_in_run[file_hash] = False

    def _update_file_status(self, file_hashes_in_run: Dict[str, bool]):
        """Updates the status of files that were successfully loaded to *all* targets."""
        for file_hash, success in file_hashes_in_run.items():
            if success:
                # Only update status if ALL upsert batches that touched this file were successful.
                # Files with FileStatus.LOADED are already skipped by the Dispatcher,
                # so this marks files that were *just* processed and successfully loaded.
                current_path = self.state_manager.manifest[file_hash]["path"]
                self.state_manager.add_or_update_file(
                    file_hash, status=FileStatus.LOADED, file_path=current_path
                )
                logger.info(f"File {file_hash[:8]} status set to LOADED.")
            else:
                # If loading failed for any reason (DB connection lost, upsert error),
                # we revert the status to EMBEDDED so it can be re-tried on the next run.
                # This assumes the file's chunks and vectors are still in cache.
                current_path = self.state_manager.manifest[file_hash]["path"]
                self.state_manager.add_or_update_file(
                    file_hash,
                    status=FileStatus.EMBEDDED,
                    file_path=current_path,
                )
                logger.warning(
                    f"File {file_hash[:8]} failed to load to one or more databases. Status reverted to EMBEDDED."
                )

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search across all active database connectors.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of search results
        """
        # Embed the query
        query_vector = self.embedding_model.embed_chunks([query])[0]

        all_results = []
        for name, connector in self.active_connectors.items():
            try:
                results = connector.search(query_vector, limit)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Search failed on {name}: {e}")

        # Sort by score if available and limit
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_results[:limit]

    def batch_upsert(self, batch: List[Dict[str, Any]]):
        """
        Upsert a batch of data to all active databases.

        Args:
            batch: List of data entries to upsert
        """
        for name, connector in self.active_connectors.items():
            try:
                connector.upsert_batch(batch)
                logger.debug(f"Batch upserted to {name}")
            except Exception as e:
                logger.error(f"Batch upsert failed on {name}: {e}")

    def close(self):
        """Closes all active database connections."""
        for name, connector in self.active_connectors.items():
            try:
                connector.close()
                logger.info(f"Closed connection to {name}.")
            except Exception as e:
                logger.warning(f"Error closing connection to {name}: {e}")
        self.initialized = False
