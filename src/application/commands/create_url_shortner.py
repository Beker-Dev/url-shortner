from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from src.domain.entities.url_shortner import UrlShortnerEntity
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository
from src.domain.services.short_code_generator import ShortCodeGenerator


@dataclass(frozen=True, slots=True)
class CreateUrlShortnerCommand:
    target_url: str


class CreateUrlShortnerCommandHandler:
    def __init__(
        self,
        repository: UrlShortnerRepository,
        short_code_generator: ShortCodeGenerator,
    ) -> None:
        self._repository = repository
        self._short_code_generator = short_code_generator

    async def handle(self, command: CreateUrlShortnerCommand) -> UrlShortnerEntity:
        while True:
            now = datetime.now(timezone.utc)
            entity = UrlShortnerEntity(
                id=uuid4(),
                target_url=command.target_url,
                short_code=await self._short_code_generator.generate(),
                created_at=now,
                updated_at=now,
            )
            if await self._repository.save(entity):
                return entity
