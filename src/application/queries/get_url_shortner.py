from dataclasses import dataclass

from src.domain.entities.url_shortner import UrlShortnerEntity
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository


@dataclass(frozen=True, slots=True)
class GetUrlShortnerQuery:
    short_code: str


class GetUrlShortnerQueryHandler:
    def __init__(self, repository: UrlShortnerRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetUrlShortnerQuery) -> UrlShortnerEntity | None:
        return await self._repository.get_by_short_code(query.short_code)
