import logging
from typing import Dict, Any, List
import os
from .db_connector_base import DBConnectorBase
import psycopg
from psycopg import sql

logger = logging.getLogger("ELESS.PostgreSQLConnector")


class PostgreSQLConnector(DBConnectorBase):
    """Concrete connector for PostgreSQL using the pgvector extension."""

    def __init__(self, config: Dict[str, Any], connection_name: str, dimension: int):
        super().__init__(config, connection_name, dimension)
        self.conn = None
        self.table_name = self.db_config.get("table_name", "eless_vectors")
        self.vector_column = self.db_config.get("vector_column", "embedding")
        self.dsn = self.db_config.get("dsn") or os.environ.get("POSTGRES_DSN")

    def connect(self):
        if not self.dsn:
            raise ConnectionError("PostgreSQL DSN not configured.")
        try:
            # Connect to the database
            self.conn = psycopg.connect(self.dsn)
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
                data = [(v["id"], v["vector"], v["metadata"]) for v in vectors]

                # Use execute_many for batch insertion
                cur.executemany(insert_query, data)
                self.conn.commit()
                logger.debug(
                    f"Successfully upserted {len(vectors)} vectors to PostgreSQL."
                )

        except Exception as e:
            logger.error(f"PostgreSQL upsert failed: {e}")
            self.conn.rollback()
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("PostgreSQL connection closed.")

    def check_connection(self) -> bool:
        return self.conn is not None
