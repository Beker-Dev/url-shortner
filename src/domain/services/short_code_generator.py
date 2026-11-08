from abc import ABC, abstractmethod


class ShortCodeGenerator(ABC):
    @abstractmethod
    async def generate(self) -> str:
        pass
