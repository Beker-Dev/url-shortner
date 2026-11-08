from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, Session
from cassandra.query import dict_factory

from src.infrastructure.config import EnvSettings


def connect_cassandra(settings: EnvSettings) -> tuple[Cluster, Session]:
    auth_provider = (
        PlainTextAuthProvider(
            username=settings.cassandra_username,
            password=settings.cassandra_password,
        )
        if settings.cassandra_username is not None
        and settings.cassandra_password is not None
        else None
    )
    cluster = Cluster(
        contact_points=list(settings.cassandra_contact_points),
        port=settings.cassandra_port,
        auth_provider=auth_provider,
    )
    try:
        session = cluster.connect(settings.cassandra_keyspace)
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
