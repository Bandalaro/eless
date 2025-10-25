import logging
from typing import Dict, Any, List
import os
import json
from .db_connector_base import DBConnectorBase
import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json

logger = logging.getLogger("ELESS.PostgreSQLConnector")


class PostgreSQLConnector(DBConnectorBase):
    """Concrete connector for PostgreSQL using the pgvector extension."""

    def __init__(self, config: Dict[str, Any], connection_name: str, dimension: int):
        super().__init__(config, connection_name, dimension)
        self.conn = None
        self.table_name = self.db_config.get("table_name", "eless_vectors")
        self.vector_column = self.db_config.get("vector_column", "embedding")
        
        # Support both DSN and individual parameters
        self.dsn = self.db_config.get("dsn") or os.environ.get("POSTGRES_DSN")
        if not self.dsn:
            # Construct DSN from individual parameters
            host = self.db_config.get("host", "localhost")
            port = self.db_config.get("port", 5432)
            user = self.db_config.get("user", "postgres")
            password = self.db_config.get("password", "")
            database = self.db_config.get("database", "postgres")
            self.dsn = f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def connect(self):
        if not self.dsn:
            raise ConnectionError("PostgreSQL DSN not configured.")
        try:
            # Check if PostgreSQL instance is running
            self._check_postgresql_running()

            # Connect to the database
            self.conn = psycopg2.connect(self.dsn)
            self.conn.autocommit = True

            with self.conn.cursor() as cur:
                # 1. Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

                # 2. Create the table if it doesn't exist
                # Define a generic metadata column (JSONB)
                create_table_query = sql.SQL(
                    "CREATE TABLE IF NOT EXISTS {} ("
                    "id TEXT PRIMARY KEY,"
                    "{} vector({}),"
                    "metadata JSONB"
                    ")"
                ).format(
                    sql.Identifier(self.table_name),
                    sql.Identifier(self.vector_column),
                    sql.Literal(self.dimension),
                )
                cur.execute(create_table_query)

            logger.info(
                f"PostgreSQL connection successful. Table '{self.table_name}' ready."
            )
        except Exception as e:
            logger.error(f"Failed to connect or set up PostgreSQL/pgvector: {e}")
            self.conn = None
            raise

    def _check_postgresql_running(self):
        """Check if PostgreSQL instance is running."""
        try:
            # Try to connect with a short timeout
            conn = psycopg2.connect(self.dsn, connect_timeout=5)
            conn.close()
            logger.info("PostgreSQL instance confirmed running")
        except Exception as e:
            raise ConnectionError(
                f"PostgreSQL instance not running or not accessible at {self.dsn}. "
                "Start the PostgreSQL server and ensure the pgvector extension is installed. "
                "Example: Install pgvector and restart PostgreSQL."
            )

    def upsert_batch(self, vectors: List[Dict[str, Any]]):
        if not self.conn:
            raise ConnectionError("PostgreSQL connection not initialized.")
        if not vectors:
            return

        try:
            with self.conn.cursor() as cur:
                insert_query = sql.SQL(
                    "INSERT INTO {} (id, {}, metadata) VALUES (%s, %s, %s) "
                    "ON CONFLICT (id) DO UPDATE SET {} = EXCLUDED.{}, metadata = EXCLUDED.metadata"
                ).format(
                    sql.Identifier(self.table_name),
                    sql.Identifier(self.vector_column),
                    sql.Identifier(self.vector_column),
                    sql.Identifier(self.vector_column),
                )

                # Prepare data tuples: (id, vector, metadata_json)
                # Use Json() for proper JSONB handling
                data = [(v["id"], v["vector"], Json(v["metadata"])) for v in vectors]

                # Use executemany for batch insertion
                cur.executemany(insert_query, data)
                # No need for commit() since autocommit is True
                logger.debug(
                    f"Successfully upserted {len(vectors)} vectors to PostgreSQL."
                )

        except Exception as e:
            logger.error(f"PostgreSQL upsert failed: {e}")
            # No need for rollback() since autocommit is True
            raise

    def search(
        self, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using cosine similarity.
        
        Args:
            query_vector: Query vector
            limit: Maximum number of results to return
            
        Returns:
            List of search results with scores and metadata
        """
        if not self.conn:
            raise ConnectionError("PostgreSQL connection not initialized.")
        
        try:
            with self.conn.cursor() as cur:
                # Use cosine distance operator from pgvector
                search_query = sql.SQL(
                    "SELECT id, metadata, 1 - ({} <=> %s::vector) AS score "
                    "FROM {} "
                    "ORDER BY {} <=> %s::vector "
                    "LIMIT %s"
                ).format(
                    sql.Identifier(self.vector_column),
                    sql.Identifier(self.table_name),
                    sql.Identifier(self.vector_column),
                )
                
                cur.execute(search_query, (query_vector, query_vector, limit))
                results = []
                for row in cur.fetchall():
                    results.append({
                        "id": row[0],
                        "metadata": row[1],
                        "score": float(row[2])
                    })
                return results
        except Exception as e:
            logger.error(f"PostgreSQL search failed: {e}")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("PostgreSQL connection closed.")

    def check_connection(self) -> bool:
        return self.conn is not None
