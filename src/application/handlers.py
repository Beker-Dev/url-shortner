from dataclasses import dataclass

from src.application.commands.create_url_shortner import (
    CreateUrlShortnerCommandHandler,
)
from src.application.queries.get_url_shortner import GetUrlShortnerQueryHandler
from src.application.queries.list_url_shortners import ListUrlShortnersQueryHandler
from src.domain.repositories.url_shortner_repository import UrlShortnerRepository
from src.domain.services.short_code_generator import ShortCodeGenerator


@dataclass(frozen=True, slots=True)
class ApplicationHandlers:
    create_url_shortner: CreateUrlShortnerCommandHandler
    get_url_shortner: GetUrlShortnerQueryHandler
    list_url_shortners: ListUrlShortnersQueryHandler


def create_application_handlers(
    repository: UrlShortnerRepository,
    short_code_generator: ShortCodeGenerator,
) -> ApplicationHandlers:
    return ApplicationHandlers(
        create_url_shortner=CreateUrlShortnerCommandHandler(
            repository,
            short_code_generator,
        ),
        get_url_shortner=GetUrlShortnerQueryHandler(repository),
        list_url_shortners=ListUrlShortnersQueryHandler(repository),
    )
