import json
from datetime import datetime
from uuid import UUID

from redis.asyncio import Redis

from src.domain.entities.url_shortner import UrlShortnerEntity
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository


HOT_ACCESS_THRESHOLD = 5
ACCESS_WINDOW_SECONDS = 600
CACHE_TTL_SECONDS = 3600

_INCREMENT_ACCESS_COUNT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


class RedisCachedUrlShortnerRepository(UrlShortnerRepository):
    def __init__(
        self,
        repository: UrlShortnerRepository,
        redis: Redis,
    ) -> None:
        self._repository = repository
        self._redis = redis

    async def save(self, entity: UrlShortnerEntity) -> bool:
        saved = await self._repository.save(entity)
        if saved:
            await self._redis.delete(self._cache_key(entity.short_code))
        return saved

    async def get_by_short_code(self, short_code: str) -> UrlShortnerEntity | None:
        cache_key = self._cache_key(short_code)
        cached_entity = await self._redis.get(cache_key)
        if cached_entity is not None:
            await self._increment_access_count(short_code)
            return self._deserialize(cached_entity)

        entity = await self._repository.get_by_short_code(short_code)
        if entity is None:
            return None

        access_count = await self._increment_access_count(short_code)
        if access_count >= HOT_ACCESS_THRESHOLD:
            await self._redis.set(
                cache_key,
                self._serialize(entity),
                ex=CACHE_TTL_SECONDS,
            )
        return entity

    async def get_all(self) -> list[UrlShortnerEntity]:
        return await self._repository.get_all()

    async def _increment_access_count(self, short_code: str) -> int:
        return int(
            await self._redis.eval(
                _INCREMENT_ACCESS_COUNT,
                1,
                self._access_count_key(short_code),
                ACCESS_WINDOW_SECONDS,
            )
        )

    @staticmethod
    def _cache_key(short_code: str) -> str:
        return f"url-shortner:cache:{short_code}"

    @staticmethod
    def _access_count_key(short_code: str) -> str:
        return f"url-shortner:access:{short_code}"

    @staticmethod
    def _serialize(entity: UrlShortnerEntity) -> str:
        return json.dumps(
            {
                "id": str(entity.id),
                "target_url": entity.target_url,
                "short_code": entity.short_code,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat(),
            }
        )

    @staticmethod
    def _deserialize(value: str) -> UrlShortnerEntity:
        data = json.loads(value)
        return UrlShortnerEntity(
            id=UUID(data["id"]),
            target_url=data["target_url"],
            short_code=data["short_code"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
