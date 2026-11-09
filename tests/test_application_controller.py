import unittest
from datetime import datetime, timezone
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.application.controller.routers import router
from src.application.handlers import create_application_handlers
from src.domain.entities.url_shortner import UrlShortnerEntity
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository
from src.domain.services.short_code_generator import ShortCodeGenerator


class InMemoryRepository(UrlShortnerRepository):
    def __init__(self) -> None:
        self.entities: dict[str, UrlShortnerEntity] = {}

    async def save(self, entity: UrlShortnerEntity) -> bool:
        if entity.short_code in self.entities:
            return False
        self.entities[entity.short_code] = entity
        return True

    async def get_by_short_code(self, short_code: str) -> UrlShortnerEntity | None:
        return self.entities.get(short_code)

    async def get_all(self) -> list[UrlShortnerEntity]:
        return list(self.entities.values())


class SequenceGenerator(ShortCodeGenerator):
    def __init__(self) -> None:
        self._counter = 0

    async def generate(self) -> str:
        self._counter += 1
        return f"code{self._counter}"


class ApplicationControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryRepository()
        app = FastAPI()
        app.include_router(router)
        app.state.handlers = create_application_handlers(
            self.repository,
            SequenceGenerator(),
        )
        self.client = TestClient(app)

    def test_create_and_get_short_url(self) -> None:
        created = self.client.post(
            "/api/url-shortner/new",
            json={"target_url": "https://example.com/path"},
        )

        self.assertEqual(created.status_code, 200)
        payload = created.json()
        self.assertEqual(payload["short_code"], "code1")
        self.assertEqual(payload["target_url"], "https://example.com/path")

        fetched = self.client.get(f"/api/url-shortner/{payload['short_code']}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json(), payload)

    def test_create_rejects_invalid_url(self) -> None:
        response = self.client.post(
            "/api/url-shortner/new",
            json={"target_url": "not a url"},
        )

        self.assertEqual(response.status_code, 422)

    def test_get_returns_404_for_missing_short_code(self) -> None:
        response = self.client.get("/api/url-shortner/unknown")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "URL shortener not found.")

    def test_list_returns_all_created_urls(self) -> None:
        now = datetime.now(timezone.utc)
        entity = UrlShortnerEntity(
            id=UUID("d6ecbe11-f91a-4bd0-878c-9d6cae941819"),
            target_url="https://example.com",
            short_code="known",
            created_at=now,
            updated_at=now,
        )
        self.repository.entities[entity.short_code] = entity

        response = self.client.get("/api/url-shortner/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["short_code"], "known")
