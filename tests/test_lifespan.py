import os
import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi import FastAPI

from src.infrastructure.lifespan import lifespan
from src.infrastructure.repositories.redis_cached_url_shortner_repository import (
    RedisCachedUrlShortnerRepository,
)


class LifespanTests(unittest.IsolatedAsyncioTestCase):
    async def test_initializes_services_and_closes_resources(self) -> None:
        environment = patch.dict(
            os.environ,
            {
                "CASSANDRA_CONTACT_POINTS": "cassandra",
                "CASSANDRA_PORT": "9042",
                "CASSANDRA_KEYSPACE": "url_shortner",
                "CASSANDRA_USERNAME": "user",
                "CASSANDRA_PASSWORD": "password",
                "REDIS_URL": "redis://counter:6379/0",
                "URL_CACHE_REDIS_URL": "redis://cache:6379/0",
                "SHORT_CODE_SECRET_KEY": "test-secret",
            },
            clear=True,
        )
        cluster = Mock()
        session = Mock()
        counter_redis = Mock()
        counter_redis.ping = AsyncMock()
        counter_redis.aclose = AsyncMock()
        counter_redis.eval = AsyncMock()
        cache_redis = Mock()
        cache_redis.ping = AsyncMock()
        cache_redis.aclose = AsyncMock()
        handlers = object()
        app = FastAPI()

        with (
            environment,
            patch(
                "src.infrastructure.lifespan.connect_cassandra",
                return_value=(cluster, session),
            ),
            patch(
                "src.infrastructure.lifespan.Redis.from_url",
                side_effect=[counter_redis, cache_redis],
            ) as redis_from_url,
            patch(
                "src.infrastructure.lifespan.create_application_handlers",
                return_value=handlers,
            ) as create_handlers,
        ):
            async with lifespan(app):
                self.assertIs(app.state.handlers, handlers)

            self.assertEqual(redis_from_url.call_count, 2)
            self.assertEqual(
                create_handlers.call_args.args[1].__class__.__name__,
                "RedisHashidsShortCodeGenerator",
            )
            self.assertIsInstance(
                create_handlers.call_args.args[0],
                RedisCachedUrlShortnerRepository,
            )
            self.assertEqual(
                [call.args[0] for call in redis_from_url.call_args_list],
                ["redis://counter:6379/0", "redis://cache:6379/0"],
            )
            counter_redis.ping.assert_awaited_once()
            cache_redis.ping.assert_awaited_once()
            counter_redis.aclose.assert_awaited_once()
            cache_redis.aclose.assert_awaited_once()
            cluster.shutdown.assert_called_once()
            session.shutdown.assert_called_once()
