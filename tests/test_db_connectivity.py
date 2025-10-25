import pytest
import socket
from unittest.mock import patch, MagicMock
from src.eless.database.qdrant_connector import QdrantConnector
from src.eless.database.postgresql_connector import PostgreSQLConnector


class TestDatabaseConnectivity:
    """Tests for checking if database servers are running."""

    def test_qdrant_server_running(self):
        """Test if Qdrant server is accessible."""
        config = {
            "databases": {
                "connections": {
                    "qdrant": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "test_collection"
                    }
                }
            }
        }
        connector = QdrantConnector(config, "qdrant", dimension=384)

        # Test when server is running (mock successful connection)
        with patch.object(socket.socket, 'connect_ex', return_value=0):
            try:
                connector._check_qdrant_running()
                assert True  # Should not raise
            except ConnectionError:
                pytest.fail("Qdrant server should be considered running")

    def test_qdrant_server_not_running(self):
        """Test if Qdrant server is not accessible."""
        config = {
            "databases": {
                "connections": {
                    "qdrant": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "test_collection"
                    }
                }
            }
        }
        connector = QdrantConnector(config, "qdrant", dimension=384)

        # Test when server is not running (mock connection failure)
        with patch.object(socket.socket, 'connect_ex', return_value=1):
            with pytest.raises(ConnectionError, match="Qdrant instance not running"):
                connector._check_qdrant_running()

    def test_postgresql_server_running(self):
        """Test if PostgreSQL server is accessible."""
        config = {
            "databases": {
                "connections": {
                    "postgresql": {
                        "host": "localhost",
                        "port": 5432,
                        "user": "test",
                        "password": "test",
                        "database": "test"
                    }
                }
            }
        }
        connector = PostgreSQLConnector(config, "postgresql", dimension=384)

        # Mock successful connection
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            try:
                connector._check_postgresql_running()
                assert True  # Should not raise
            except ConnectionError:
                pytest.fail("PostgreSQL server should be considered running")

    def test_postgresql_server_not_running(self):
        """Test if PostgreSQL server is not accessible."""
        config = {
            "databases": {
                "connections": {
                    "postgresql": {
                        "host": "localhost",
                        "port": 5432,
                        "user": "test",
                        "password": "test",
                        "database": "test"
                    }
                }
            }
        }
        connector = PostgreSQLConnector(config, "postgresql", dimension=384)

        # Mock connection failure
        with patch('psycopg2.connect', side_effect=Exception("Connection refused")):
            with pytest.raises(ConnectionError, match="PostgreSQL instance not running"):
                connector._check_postgresql_running()

    def test_qdrant_check_connection_method(self):
        """Test Qdrant check_connection method."""
        config = {
            "databases": {
                "connections": {
                    "qdrant": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "test_collection"
                    }
                }
            }
        }
        connector = QdrantConnector(config, "qdrant", dimension=384)

        # Initially not connected
        assert not connector.check_connection()

        # After connecting (mock)
        with patch.object(connector, 'client', MagicMock()):
            with patch.object(connector.client, 'get_collection', return_value=MagicMock()):
                assert connector.check_connection()

    def test_postgresql_check_connection_method(self):
        """Test PostgreSQL check_connection method."""
        config = {
            "databases": {
                "connections": {
                    "postgresql": {
                        "host": "localhost",
                        "port": 5432,
                        "user": "test",
                        "password": "test",
                        "database": "test"
                    }
                }
            }
        }
        connector = PostgreSQLConnector(config, "postgresql", dimension=384)

        # Initially not connected
        assert not connector.check_connection()

        # After connecting (mock)
        connector.conn = MagicMock()
        assert connector.check_connection()