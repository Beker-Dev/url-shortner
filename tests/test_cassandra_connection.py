import os
import unittest
from unittest.mock import Mock, patch

from src.infrastructure.config import EnvSettings
from src.infrastructure.database.cassandra import connect_cassandra


class CassandraConnectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(
            os.environ,
            {
                "CASSANDRA_CONTACT_POINTS": "host-1,host-2",
                "CASSANDRA_PORT": "9142",
                "CASSANDRA_KEYSPACE": "short_links",
                "CASSANDRA_USERNAME": "user",
                "CASSANDRA_PASSWORD": "password",
                "REDIS_URL": "redis://redis:6379/0",
                "URL_CACHE_REDIS_URL": "redis://cache:6379/0",
                "SHORT_CODE_SECRET_KEY": "test-secret",
            },
            clear=True,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.settings = EnvSettings(_env_file=None)

    @patch("src.infrastructure.database.cassandra.Cluster")
    @patch("src.infrastructure.database.cassandra.PlainTextAuthProvider")
    def test_connects_and_creates_url_table(self, auth_provider, cluster_factory) -> None:
        cluster = cluster_factory.return_value
        session = cluster.connect.return_value

        returned_cluster, returned_session = connect_cassandra(self.settings)

        self.assertIs(returned_cluster, cluster)
        self.assertIs(returned_session, session)
        auth_provider.assert_called_once_with(username="user", password="password")
        cluster_factory.assert_called_once_with(
            contact_points=["host-1", "host-2"],
            port=9142,
            auth_provider=auth_provider.return_value,
        )
        self.assertTrue(session.row_factory)
        session.execute.assert_called_once()

    @patch("src.infrastructure.database.cassandra.Cluster")
    def test_shuts_down_cluster_when_connection_fails(self, cluster_factory) -> None:
        cluster = cluster_factory.return_value
        cluster.connect.side_effect = RuntimeError("connection failed")

        with self.assertRaisesRegex(RuntimeError, "connection failed"):
            connect_cassandra(self.settings)

        cluster.shutdown.assert_called_once()

    @patch("src.infrastructure.database.cassandra.Cluster")
    def test_shuts_down_cluster_when_table_creation_fails(self, cluster_factory) -> None:
        cluster = cluster_factory.return_value
        cluster.connect.return_value.execute.side_effect = RuntimeError("DDL failed")

        with self.assertRaisesRegex(RuntimeError, "DDL failed"):
            connect_cassandra(self.settings)

        cluster.shutdown.assert_called_once()
