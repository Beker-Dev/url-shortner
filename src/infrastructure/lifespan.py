import asyncio
from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from src.application.handlers import create_application_handlers
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository
from src.infrastructure.config import EnvSettings
from src.infrastructure.database.cassandra import connect_cassandra
from src.infrastructure.repositories.cassandra_url_shortner_repository import (
    CassandraUrlShortnerRepository,
)
from src.infrastructure.repositories.redis_cached_url_shortner_repository import (
    RedisCachedUrlShortnerRepository,
)
from src.infrastructure.services.redis_hashids_short_code_generator import (
    RedisHashidsShortCodeGenerator,
)


async def _create_repository(
    settings: EnvSettings,
    stack: AsyncExitStack,
) -> UrlShortnerRepository:
    cluster, session = await asyncio.to_thread(connect_cassandra, settings)
    stack.push_async_callback(asyncio.to_thread, cluster.shutdown)
    stack.push_async_callback(asyncio.to_thread, session.shutdown)
    return CassandraUrlShortnerRepository(session)


async def _create_redis(
    settings: EnvSettings,
    stack: AsyncExitStack,
) -> Redis:
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    stack.push_async_callback(redis.aclose)
    await redis.ping()
    return redis


async def _create_short_code_generator(
    redis: Redis,
    settings: EnvSettings,
) -> RedisHashidsShortCodeGenerator:
    generator = RedisHashidsShortCodeGenerator(
        redis,
        settings.short_code_secret_key,
    )
    await generator.initialize()
    return generator


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = EnvSettings()
    async with AsyncExitStack() as stack:
        repository = await _create_repository(settings, stack)
        redis = await _create_redis(settings, stack)
        url_cache_redis = Redis.from_url(
            settings.url_cache_redis_url,
            decode_responses=True,
        )
        stack.push_async_callback(url_cache_redis.aclose)
        await url_cache_redis.ping()
        short_code_generator = await _create_short_code_generator(redis, settings)
        app.state.handlers = create_application_handlers(
            RedisCachedUrlShortnerRepository(repository, url_cache_redis),
            short_code_generator,
        )
        yield
