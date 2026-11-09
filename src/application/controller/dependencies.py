from fastapi import Request

from src.application.commands.create_url_shortner import (
    CreateUrlShortnerCommandHandler,
)
from src.application.queries.get_url_shortner import GetUrlShortnerQueryHandler
from src.application.queries.list_url_shortners import ListUrlShortnersQueryHandler


def get_create_url_shortner_handler(
    request: Request,
) -> CreateUrlShortnerCommandHandler:
    return request.app.state.handlers.create_url_shortner


def get_get_url_shortner_handler(request: Request) -> GetUrlShortnerQueryHandler:
    return request.app.state.handlers.get_url_shortner


def get_list_url_shortners_handler(
    request: Request,
) -> ListUrlShortnersQueryHandler:
    return request.app.state.handlers.list_url_shortners
