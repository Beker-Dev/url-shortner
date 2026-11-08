import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from src.infrastructure.config import EnvSettings


class EnvSettingsTests(unittest.TestCase):
    def test_reads_environment_variables_and_splits_contact_points(self) -> None:
        environment = {
            "CASSANDRA_CONTACT_POINTS": " cassandra-1, cassandra-2 ",
            "CASSANDRA_PORT": "9142",
            "CASSANDRA_KEYSPACE": "short_links",
            "CASSANDRA_USERNAME": "user",
            "CASSANDRA_PASSWORD": "password",
            "REDIS_URL": "redis://redis:6379/2",
            "SHORT_CODE_SECRET_KEY": "a-secret-key",
        }

        with patch.dict(os.environ, environment, clear=True):
            settings = EnvSettings(_env_file=None)

        self.assertEqual(settings.cassandra_contact_points, ("cassandra-1", "cassandra-2"))
        self.assertEqual(settings.cassandra_port, 9142)
        self.assertEqual(settings.cassandra_keyspace, "short_links")
        self.assertEqual(settings.cassandra_username, "user")
        self.assertEqual(settings.cassandra_password, "password")
        self.assertEqual(settings.redis_url, "redis://redis:6379/2")
        self.assertEqual(settings.short_code_secret_key, "a-secret-key")

    def test_requires_all_configuration_values(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"SHORT_CODE_SECRET_KEY": "a-secret-key"},
                clear=True,
            ),
            self.assertRaises(ValidationError),
        ):
            EnvSettings(_env_file=None)

    def test_accepts_empty_cassandra_credentials_without_authentication(self) -> None:
        environment = {
            "CASSANDRA_CONTACT_POINTS": "127.0.0.1",
            "CASSANDRA_PORT": "9042",
            "CASSANDRA_KEYSPACE": "url_shortner",
            "CASSANDRA_USERNAME": "",
            "CASSANDRA_PASSWORD": "",
            "REDIS_URL": "redis://127.0.0.1:6379/0",
            "SHORT_CODE_SECRET_KEY": "a-secret-key",
        }

        with patch.dict(os.environ, environment, clear=True):
            settings = EnvSettings(_env_file=None)

        self.assertIsNone(settings.cassandra_username)
        self.assertIsNone(settings.cassandra_password)

    def test_rejects_empty_contact_points(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "CASSANDRA_CONTACT_POINTS": " , ",
                    "SHORT_CODE_SECRET_KEY": "a-secret-key",
                },
                clear=True,
            ),
            self.assertRaises(ValidationError),
        ):
            EnvSettings(_env_file=None)

    def test_rejects_unpaired_cassandra_credentials(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "CASSANDRA_USERNAME": "user",
                    "SHORT_CODE_SECRET_KEY": "a-secret-key",
                },
                clear=True,
            ),
            self.assertRaises(ValidationError),
        ):
            EnvSettings(_env_file=None)
