import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from src.application.controller.routers import router as api_router
from src.infrastructure.database.cassandra import (
    CassandraSettings,
    connect_cassandra,
)
from src.infrastructure.repositories.url_shortner_repository import (
    UrlShortnerRepository,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = CassandraSettings.from_env()
    cluster, session = await asyncio.to_thread(connect_cassandra, settings)
    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )
    try:
        await redis.ping()
        repository = UrlShortnerRepository(
            session,
            redis,
            settings.short_code_secret_key,
        )
        await repository.initialize_counter()
        app.state.url_shortner_repository = repository
        yield
    finally:
        try:
            await redis.aclose()
        finally:
            try:
                await asyncio.to_thread(session.shutdown)
            finally:
                await asyncio.to_thread(cluster.shutdown)


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
