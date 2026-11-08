import unittest
from datetime import datetime, timezone
from uuid import UUID

from src.application.commands.create_url_shortner import (
    CreateUrlShortnerCommand,
    CreateUrlShortnerCommandHandler,
)
from src.application.queries.get_url_shortner import (
    GetUrlShortnerQuery,
    GetUrlShortnerQueryHandler,
)
from src.application.queries.list_url_shortners import ListUrlShortnersQueryHandler
from src.domain.entities.url_shortner import UrlShortnerEntity
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository
from src.domain.services.short_code_generator import ShortCodeGenerator


class InMemoryUrlShortnerRepository(UrlShortnerRepository):
    def __init__(self) -> None:
        self.entities: list[UrlShortnerEntity] = []
        self.conflicting_codes: set[str] = set()

    async def save(self, entity: UrlShortnerEntity) -> bool:
        if entity.short_code in self.conflicting_codes:
            return False
        self.entities.append(entity)
        return True

    async def get_by_short_code(self, short_code: str) -> UrlShortnerEntity | None:
        return next(
            (entity for entity in self.entities if entity.short_code == short_code),
            None,
        )

    async def get_all(self) -> list[UrlShortnerEntity]:
        return list(self.entities)


class SequenceShortCodeGenerator(ShortCodeGenerator):
    def __init__(self, codes: list[str]) -> None:
        self._codes = iter(codes)

    async def generate(self) -> str:
        return next(self._codes)


class UrlShortnerUseCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_retries_when_repository_reports_code_collision(self) -> None:
        repository = InMemoryUrlShortnerRepository()
        repository.conflicting_codes.add("taken")
        handler = CreateUrlShortnerCommandHandler(
            repository,
            SequenceShortCodeGenerator(["taken", "available"]),
        )

        entity = await handler.handle(
            CreateUrlShortnerCommand(target_url="https://example.com")
        )

        self.assertEqual(entity.short_code, "available")
        self.assertEqual(entity.target_url, "https://example.com")
        self.assertIsInstance(entity.id, UUID)
        self.assertEqual(entity.created_at.tzinfo, timezone.utc)
        self.assertEqual(entity.updated_at, entity.created_at)
        self.assertEqual(repository.entities, [entity])

    async def test_get_by_short_code_returns_repository_result(self) -> None:
        repository = InMemoryUrlShortnerRepository()
        entity = self._entity("known")
        repository.entities.append(entity)

        handler = GetUrlShortnerQueryHandler(repository)
        result = await handler.handle(GetUrlShortnerQuery(short_code="known"))

        self.assertIs(result, entity)
        self.assertIsNone(await handler.handle(GetUrlShortnerQuery(short_code="missing")))

    async def test_list_returns_repository_results(self) -> None:
        repository = InMemoryUrlShortnerRepository()
        entities = [self._entity("first"), self._entity("second")]
        repository.entities.extend(entities)

        result = await ListUrlShortnersQueryHandler(repository).handle()

        self.assertEqual(result, entities)

    @staticmethod
    def _entity(short_code: str) -> UrlShortnerEntity:
        now = datetime.now(timezone.utc)
        return UrlShortnerEntity(
            id=UUID("d6ecbe11-f91a-4bd0-878c-9d6cae941819"),
            target_url="https://example.com",
            short_code=short_code,
            created_at=now,
            updated_at=now,
        )
