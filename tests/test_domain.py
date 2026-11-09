import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID

from src.domain.entities.url_shortner import UrlShortnerEntity
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository
from src.domain.services.short_code_generator import ShortCodeGenerator


class DomainTests(unittest.TestCase):
    def test_entity_preserves_domain_values_and_is_immutable(self) -> None:
        now = datetime.now(timezone.utc)
        entity = UrlShortnerEntity(
            id=UUID("d6ecbe11-f91a-4bd0-878c-9d6cae941819"),
            target_url="https://example.com",
            short_code="code",
            created_at=now,
            updated_at=now,
        )

        self.assertEqual(entity.target_url, "https://example.com")
        self.assertIs(entity.created_at, now)
        with self.assertRaises(FrozenInstanceError):
            entity.short_code = "changed"  # type: ignore[misc]

    def test_domain_ports_are_abstract(self) -> None:
        with self.assertRaises(TypeError):
            UrlShortnerRepository()
        with self.assertRaises(TypeError):
            ShortCodeGenerator()
