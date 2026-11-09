import unittest
from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import UUID

from src.domain.entities.url_shortner import UrlShortnerEntity
from src.infrastructure.repositories.cassandra_url_shortner_repository import (
    CassandraUrlShortnerRepository,
)


class CassandraUrlShortnerRepositoryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.now = datetime.now(timezone.utc)
        self.row = {
            "id": UUID("d6ecbe11-f91a-4bd0-878c-9d6cae941819"),
            "target_url": "https://example.com",
            "short_code": "code",
            "created_at": self.now,
            "updated_at": self.now,
        }
        self.session = Mock()
        self.prepared_insert = object()
        self.prepared_select = object()
        self.session.prepare.side_effect = [self.prepared_insert, self.prepared_select]
        self.repository = CassandraUrlShortnerRepository(self.session)

    async def test_save_returns_applied_status(self) -> None:
        self.session.execute.return_value.one.return_value = {"[applied]": True}

        saved = await self.repository.save(self._entity())

        self.assertTrue(saved)
        self.assertIs(self.session.execute.call_args.args[0], self.prepared_insert)

    async def test_save_returns_false_on_duplicate_short_code(self) -> None:
        self.session.execute.return_value.one.return_value = {"[applied]": False}

        self.assertFalse(await self.repository.save(self._entity()))

    async def test_get_by_short_code_maps_row_to_entity(self) -> None:
        self.session.execute.return_value.one.return_value = self.row

        entity = await self.repository.get_by_short_code("code")

        self.assertEqual(entity.short_code, "code")
        self.assertEqual(entity.target_url, "https://example.com")
        self.assertIs(self.session.execute.call_args.args[0], self.prepared_select)

    async def test_get_by_short_code_returns_none_when_missing(self) -> None:
        self.session.execute.return_value.one.return_value = None

        self.assertIsNone(await self.repository.get_by_short_code("missing"))

    async def test_get_all_maps_every_row(self) -> None:
        self.session.execute.return_value = [self.row, self.row]

        entities = await self.repository.get_all()

        self.assertEqual(len(entities), 2)
        self.assertEqual(entities[0].short_code, "code")

    def _entity(self) -> UrlShortnerEntity:
        return UrlShortnerEntity(**self.row)
