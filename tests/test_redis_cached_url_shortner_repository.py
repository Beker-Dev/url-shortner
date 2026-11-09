import unittest
from datetime import datetime, timezone
from uuid import UUID

from src.domain.entities.url_shortner import UrlShortnerEntity
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository
from src.infrastructure.repositories.redis_cached_url_shortner_repository import (
    CACHE_TTL_SECONDS,
    HOT_ACCESS_THRESHOLD,
    RedisCachedUrlShortnerRepository,
)


class InMemoryUrlShortnerRepository(UrlShortnerRepository):
    def __init__(self, entity: UrlShortnerEntity | None) -> None:
        self.entity = entity
        self.lookup_count = 0

    async def save(self, entity: UrlShortnerEntity) -> bool:
        self.entity = entity
        return True

    async def get_by_short_code(self, short_code: str) -> UrlShortnerEntity | None:
        self.lookup_count += 1
        if self.entity is not None and self.entity.short_code == short_code:
            return self.entity
        return None

    async def get_all(self) -> list[UrlShortnerEntity]:
        return [self.entity] if self.entity is not None else []


class InMemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.counters: dict[str, int] = {}
        self.expirations: dict[str, int] = {}

    async def get(self, name: str) -> str | None:
        return self.values.get(name)

    async def eval(
        self,
        script: str,
        numkeys: int,
        key: str,
        expiry: int,
    ) -> int:
        count = self.counters.get(key, 0) + 1
        self.counters[key] = count
        if count == 1:
            self.expirations[key] = expiry
        return count

    async def set(self, name: str, value: str, ex: int) -> None:
        self.values[name] = value
        self.expirations[name] = ex

    async def delete(self, *names: str) -> int:
        deleted = 0
        for name in names:
            if name in self.values:
                del self.values[name]
                deleted += 1
            self.counters.pop(name, None)
            self.expirations.pop(name, None)
        return deleted


class RedisCachedUrlShortnerRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_caches_url_after_hot_access_threshold_and_serves_cache_hits(self) -> None:
        entity = self._entity()
        repository = InMemoryUrlShortnerRepository(entity)
        redis = InMemoryRedis()
        api_repositories = [
            RedisCachedUrlShortnerRepository(repository, redis),
            RedisCachedUrlShortnerRepository(repository, redis),
        ]

        for index in range(HOT_ACCESS_THRESHOLD):
            cached_repository = api_repositories[index % len(api_repositories)]
            self.assertEqual(await cached_repository.get_by_short_code("hot"), entity)

        self.assertIn("url-shortner:cache:hot", redis.values)
        self.assertEqual(
            redis.expirations["url-shortner:cache:hot"],
            CACHE_TTL_SECONDS,
        )

        self.assertEqual(await api_repositories[0].get_by_short_code("hot"), entity)
        self.assertEqual(repository.lookup_count, HOT_ACCESS_THRESHOLD)
        self.assertEqual(
            redis.counters["url-shortner:access:hot"],
            HOT_ACCESS_THRESHOLD + 1,
        )

    async def test_successful_save_invalidates_cached_url(self) -> None:
        entity = self._entity()
        repository = InMemoryUrlShortnerRepository(None)
        redis = InMemoryRedis()
        redis.values["url-shortner:cache:hot"] = "stale"
        cached_repository = RedisCachedUrlShortnerRepository(repository, redis)

        self.assertTrue(await cached_repository.save(entity))

        self.assertNotIn("url-shortner:cache:hot", redis.values)

    async def test_missing_urls_are_not_counted_or_cached(self) -> None:
        repository = InMemoryUrlShortnerRepository(None)
        redis = InMemoryRedis()
        cached_repository = RedisCachedUrlShortnerRepository(repository, redis)

        self.assertIsNone(await cached_repository.get_by_short_code("missing"))

        self.assertEqual(redis.counters, {})
        self.assertEqual(redis.values, {})

    @staticmethod
    def _entity() -> UrlShortnerEntity:
        now = datetime.now(timezone.utc)
        return UrlShortnerEntity(
            id=UUID("d6ecbe11-f91a-4bd0-878c-9d6cae941819"),
            target_url="https://example.com",
            short_code="hot",
            created_at=now,
            updated_at=now,
        )
