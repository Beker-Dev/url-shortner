from abc import ABC, abstractmethod

from src.domain.entities.url_shortner import UrlShortnerEntity


class UrlShortnerRepository(ABC):
    @abstractmethod
    async def save(self, entity: UrlShortnerEntity) -> bool:
        """Persist an entity and return False when its short code already exists."""

    @abstractmethod
    async def get_by_short_code(self, short_code: str) -> UrlShortnerEntity | None:
        pass

    @abstractmethod
    async def get_all(self) -> list[UrlShortnerEntity]:
        pass
