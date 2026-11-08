import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from src.application.commands.create_url_shortner import (
    CreateUrlShortnerCommandHandler,
)
from src.application.controller.routers import router as api_router
from src.application.queries.get_url_shortner import GetUrlShortnerQueryHandler
from src.application.queries.list_url_shortners import ListUrlShortnersQueryHandler
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository
from src.infrastructure.config import EnvSettings
from src.infrastructure.database.cassandra import connect_cassandra
from src.infrastructure.repositories.cassandra_url_shortner_repository import (
    CassandraUrlShortnerRepository,
)
from src.infrastructure.services.redis_hashids_short_code_generator import (
    RedisHashidsShortCodeGenerator,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = EnvSettings()
    cluster, session = await asyncio.to_thread(
        connect_cassandra,
        settings,
    )
    redis: Redis | None = None
    try:
        redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        await redis.ping()
        repository: UrlShortnerRepository = CassandraUrlShortnerRepository(session)
        short_code_generator = RedisHashidsShortCodeGenerator(
            redis,
            settings.short_code_secret_key,
        )
        await short_code_generator.initialize()
        app.state.create_url_shortner_handler = CreateUrlShortnerCommandHandler(
            repository,
            short_code_generator,
        )
        app.state.get_url_shortner_handler = GetUrlShortnerQueryHandler(repository)
        app.state.list_url_shortners_handler = ListUrlShortnersQueryHandler(repository)
        yield
    finally:
        try:
            if redis is not None:
                await redis.aclose()
        finally:
            try:
                await asyncio.to_thread(session.shutdown)
            finally:
                await asyncio.to_thread(cluster.shutdown)


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
