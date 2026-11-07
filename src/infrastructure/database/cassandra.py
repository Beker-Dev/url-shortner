import os
import re
from dataclasses import dataclass

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, Session
from cassandra.query import dict_factory


_KEYSPACE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass(frozen=True, slots=True)
class CassandraSettings:
    contact_points: tuple[str, ...]
    port: int
    keyspace: str
    username: str | None
    password: str | None
    redis_url: str
    short_code_secret_key: str

    @classmethod
    def from_env(cls) -> "CassandraSettings":
        contact_points = tuple(
            point.strip()
            for point in os.getenv("CASSANDRA_CONTACT_POINTS", "127.0.0.1").split(",")
            if point.strip()
        )
        if not contact_points:
            raise ValueError("CASSANDRA_CONTACT_POINTS must not be empty.")

        port = int(os.getenv("CASSANDRA_PORT", "9042"))
        if not 1 <= port <= 65535:
            raise ValueError("CASSANDRA_PORT must be between 1 and 65535.")

        keyspace = os.getenv("CASSANDRA_KEYSPACE", "url_shortner")
        if not _KEYSPACE_PATTERN.fullmatch(keyspace):
            raise ValueError(
                "CASSANDRA_KEYSPACE must start with a letter and contain only "
                "letters, digits, or underscores."
            )

        username = os.getenv("CASSANDRA_USERNAME")
        password = os.getenv("CASSANDRA_PASSWORD")
        if bool(username) != bool(password):
            raise ValueError(
                "CASSANDRA_USERNAME and CASSANDRA_PASSWORD must be set together."
            )

        short_code_secret_key = os.getenv("SHORT_CODE_SECRET_KEY")
        if short_code_secret_key is None or len(short_code_secret_key) < 6:
            raise ValueError(
                "SHORT_CODE_SECRET_KEY must be configured with at least 6 characters."
            )

        return cls(
            contact_points=contact_points,
            port=port,
            keyspace=keyspace,
            username=username,
            password=password,
            redis_url=os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"),
            short_code_secret_key=short_code_secret_key,
        )


def connect_cassandra(settings: CassandraSettings) -> tuple[Cluster, Session]:
    auth_provider = (
        PlainTextAuthProvider(
            username=settings.username,
            password=settings.password,
        )
        if settings.username is not None and settings.password is not None
        else None
    )
    cluster = Cluster(
        contact_points=list(settings.contact_points),
        port=settings.port,
        auth_provider=auth_provider,
    )
    try:
        session = cluster.connect(settings.keyspace)
        session.row_factory = dict_factory
        session.execute(
            """
            CREATE TABLE IF NOT EXISTS url_shortner (
                short_code text PRIMARY KEY,
                id uuid,
                target_url text,
                created_at timestamp,
                updated_at timestamp
            )
            """
        )
    except Exception:
        cluster.shutdown()
        raise
    return cluster, session
