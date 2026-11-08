from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi_utils.cbv import cbv

from src.application.commands.create_url_shortner import (
    CreateUrlShortnerCommand,
    CreateUrlShortnerCommandHandler,
)
from src.application.controller.dependencies import (
    get_create_url_shortner_handler,
    get_get_url_shortner_handler,
    get_list_url_shortners_handler,
)
from src.application.dtos.url_shortner import (
    UrlShortnerCreate,
    UrlShortnerRead,
)
from src.application.queries.get_url_shortner import (
    GetUrlShortnerQuery,
    GetUrlShortnerQueryHandler,
)
from src.application.queries.list_url_shortners import ListUrlShortnersQueryHandler


router = APIRouter(prefix="/url-shortner", tags=["url-shortner"])


@cbv(router)
class UrlShortnerController:
    @router.post(
        "/new",
        response_model=UrlShortnerRead,
        summary="Create URL Shortener",
    )
    async def create_url_shortner(
        self,
        url_shortner: UrlShortnerCreate,
        handler: Annotated[
            CreateUrlShortnerCommandHandler,
            Depends(get_create_url_shortner_handler),
        ],
    ) -> UrlShortnerRead:
        entity = await handler.handle(
            CreateUrlShortnerCommand(target_url=str(url_shortner.target_url))
        )
        return UrlShortnerRead.model_validate(entity)

    @router.get(
        "/",
        response_model=list[UrlShortnerRead],
        summary="Get All URL Shorteners",
    )
    async def get_all_url_shortners(
        self,
        handler: Annotated[
            ListUrlShortnersQueryHandler,
            Depends(get_list_url_shortners_handler),
        ],
    ) -> list[UrlShortnerRead]:
        entities = await handler.handle()
        return [UrlShortnerRead.model_validate(entity) for entity in entities]

    @router.get(
        "/{short_code}",
        response_model=UrlShortnerRead,
        summary="Get URL Shortener by Short Code",
    )
    async def get_url_shortner_by_short_code(
        self,
        short_code: str,
        handler: Annotated[
            GetUrlShortnerQueryHandler,
            Depends(get_get_url_shortner_handler),
        ],
    ) -> UrlShortnerRead:
        entity = await handler.handle(GetUrlShortnerQuery(short_code=short_code))
        if entity is None:
            raise HTTPException(status_code=404, detail="URL shortener not found.")
        return UrlShortnerRead.model_validate(entity)
