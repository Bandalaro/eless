import logging
from typing import Dict, Any, List
from .db_connector_base import DBConnectorBase
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.cqlengine.query import BatchQuery
from cassandra.query import SimpleStatement

logger = logging.getLogger("ELESS.CassandraConnector")


class CassandraConnector(DBConnectorBase):
    """
    Concrete connector for Apache Cassandra/DataStax Astra DB with Vector Search.
    """

    def __init__(self, config: Dict[str, Any], connection_name: str, dimension: int):
        super().__init__(config, connection_name, dimension)
        self.session = None
        self.cluster = None
        self.keyspace = self.db_config.get("keyspace", "eless_keyspace")
        self.table_name = self.db_config.get("table_name", "eless_vectors")
        self.contact_points = self.db_config.get("contact_points", ["localhost"])
        self.port = self.db_config.get("port", 9042)

        # Authentication details
        self.username = self.db_config.get("username")
        self.password = self.db_config.get("password")

    def _check_cassandra_running(self):
        """Check if Cassandra instance is running."""
        import socket

        try:
            # Try to connect to the first contact point
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.contact_points[0], self.port))
            sock.close()
            if result != 0:
                raise ConnectionError(
                    f"Cassandra instance not running at cassandra://{self.contact_points[0]}:{self.port}. "
                    "Start the Cassandra server and ensure the port is accessible."
                )
            logger.info(
                f"Cassandra instance confirmed running on {self.contact_points[0]}:{self.port}"
            )
        except Exception as e:
            raise ConnectionError(f"Failed to check Cassandra status: {e}")

    def connect(self):
        try:
            # Check if Cassandra instance is running
            self._check_cassandra_running()

            auth_provider = None
            if self.username and self.password:
                auth_provider = PlainTextAuthProvider(self.username, self.password)

            self.cluster = Cluster(
                contact_points=self.contact_points,
                port=self.port,
                auth_provider=auth_provider,
            )
            self.session = self.cluster.connect()

            # 1. Create keyspace (if not exists)
            self.session.execute(
                f"CREATE KEYSPACE IF NOT EXISTS {self.keyspace} WITH replication = "
                "{{'class': 'SimpleStrategy', 'replication_factor': '1'}}"
            )
            self.session.set_keyspace(self.keyspace)

            # 2. Create table with vector column (if not exists)
            # The vector column type is 'vector<float, dimension>'
            create_table_cql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id text PRIMARY KEY,
                vector vector<float, {self.dimension}>,
                metadata_json text
            )
            """
            self.session.execute(create_table_cql)

            logger.info(
                f"Cassandra connection successful. Keyspace '{self.keyspace}' and table "
                f"'{self.table_name}' ready."
            )

        except Exception as e:
            logger.error(f"Failed to connect or set up Cassandra: {e}")
            self.session = None
            self.cluster = None
            raise

    def upsert_batch(self, vectors: List[Dict[str, Any]]):
        if not self.session:
            raise ConnectionError("Cassandra session not initialized.")
        if not vectors:
            return

        # CQL for upsert
        upsert_cql = f"""
        INSERT INTO {self.table_name} (id, vector, metadata_json)
        VALUES (%s, %s, %s)
        """

        # Prepare data for batching
        data_tuples = [
            (
                v["id"],
                v["vector"],
                str(v["metadata"]),
            )  # Convert metadata to JSON string
            for v in vectors
        ]

        try:
            # Execute as a batch
            prepared_statement = self.session.prepare(upsert_cql)
            batch = BatchQuery()
            for row in data_tuples:
                batch.add(prepared_statement, row)

            self.session.execute(batch)
            logger.debug(f"Successfully upserted {len(vectors)} vectors to Cassandra.")

        except Exception as e:
            logger.error(f"Cassandra upsert failed: {e}")
            raise

    def close(self):
        if self.session:
            self.session.shutdown()
            self.session = None
            self.cluster = None
            logger.debug("Cassandra connection closed.")

    def check_connection(self) -> bool:
        return self.session is not None
