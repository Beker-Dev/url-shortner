import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from cassandra.cluster import Session
from fastapi import Request
from hashids import Hashids
from redis.asyncio import Redis

from src.domain.entities.url_shortner import UrlShortnerEntity


class UrlShortnerRepository:
    _COUNTER_KEY = "url_shortner:short_code:sequence"
    _COUNTER_MINIMUM = 62**3 - 1
    _BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    def __init__(self, session: Session, redis: Redis, secret_key: str) -> None:
        self._session = session
        self._redis = redis
        self._hashids = Hashids(
            salt=secret_key,
            min_length=4,
            alphabet=self._BASE62_ALPHABET,
        )
        self._insert = session.prepare(
            """
            INSERT INTO url_shortner
                (short_code, id, target_url, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            IF NOT EXISTS
            """
        )
        self._get_by_short_code = session.prepare(
            """
            SELECT id, target_url, short_code, created_at, updated_at
            FROM url_shortner
            WHERE short_code = ?
            """
        )

    async def initialize_counter(self) -> None:
        await self._redis.eval(
            """
            local current = redis.call('GET', KEYS[1])
            local minimum = tonumber(ARGV[1])
            if not current or tonumber(current) < minimum then
                redis.call('SET', KEYS[1], minimum)
                return minimum
            end
            return tonumber(current)
            """,
            1,
            self._COUNTER_KEY,
            self._COUNTER_MINIMUM,
        )

    async def create(self, target_url: str) -> UrlShortnerEntity:
        while True:
            sequence = await self._redis.incr(self._COUNTER_KEY)
            now = datetime.now(timezone.utc)
            entity = UrlShortnerEntity(
                id=uuid4(),
                target_url=target_url,
                short_code=self._hashids.encode(sequence),
                created_at=now,
                updated_at=now,
            )
            result = await asyncio.to_thread(
                self._session.execute,
                self._insert,
                (
                    entity.short_code,
                    entity.id,
                    entity.target_url,
                    entity.created_at,
                    entity.updated_at,
                ),
            )
            row = result.one()
            if row is not None and row["[applied]"]:
                return entity

    async def get_by_short_code(self, short_code: str) -> UrlShortnerEntity | None:
        result = await asyncio.to_thread(
            self._session.execute,
            self._get_by_short_code,
            (short_code,),
        )
        row = result.one()
        return self._to_entity(row) if row is not None else None

    async def get_all(self) -> list[UrlShortnerEntity]:
        result = await asyncio.to_thread(
            self._session.execute,
            """
            SELECT id, target_url, short_code, created_at, updated_at
            FROM url_shortner
            ALLOW FILTERING
            """,
        )
        return [self._to_entity(row) for row in result]

    @staticmethod
    def _to_entity(row: Mapping[str, Any]) -> UrlShortnerEntity:
        return UrlShortnerEntity(
            id=row["id"],
            target_url=row["target_url"],
            short_code=row["short_code"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def get_url_shortner_repository(request: Request) -> UrlShortnerRepository:
    return request.app.state.url_shortner_repository
