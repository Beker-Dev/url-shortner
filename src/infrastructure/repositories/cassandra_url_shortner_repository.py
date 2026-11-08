import asyncio
from collections.abc import Mapping
from typing import Any

from cassandra.cluster import Session

from src.domain.entities.url_shortner import UrlShortnerEntity
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository


class CassandraUrlShortnerRepository(UrlShortnerRepository):
    def __init__(self, session: Session) -> None:
        self._session = session
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

    async def save(self, entity: UrlShortnerEntity) -> bool:
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
        return bool(row is not None and row["[applied]"])

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
