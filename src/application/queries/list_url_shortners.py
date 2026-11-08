from src.domain.entities.url_shortner import UrlShortnerEntity
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository


class ListUrlShortnersQueryHandler:
    def __init__(self, repository: UrlShortnerRepository) -> None:
        self._repository = repository

    async def handle(self) -> list[UrlShortnerEntity]:
        return await self._repository.get_all()
