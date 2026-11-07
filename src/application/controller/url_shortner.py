from fastapi_utils.cbv import cbv
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from src.domain.dtos.url_shortner import UrlShortnerCreate, UrlShortnerRead
from src.infrastructure.repositories.url_shortner_repository import (
    UrlShortnerRepository,
    get_url_shortner_repository,
)

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
        repository: Annotated[
            UrlShortnerRepository, Depends(get_url_shortner_repository)
        ],
    ) -> UrlShortnerRead:
        entity = await repository.create(str(url_shortner.target_url))
        return UrlShortnerRead.model_validate(entity)

    @router.get(
        "/",
        response_model=list[UrlShortnerRead],
        summary="Get All URL Shorteners",
    )
    async def get_all_url_shortners(
        self,
        repository: Annotated[
            UrlShortnerRepository, Depends(get_url_shortner_repository)
        ],
    ) -> list[UrlShortnerRead]:
        entities = await repository.get_all()
        return [UrlShortnerRead.model_validate(entity) for entity in entities]

    @router.get(
        "/{short_code}",
        response_model=UrlShortnerRead,
        summary="Get URL Shortener by Short Code",
    )
    async def get_url_shortner_by_short_code(
        self,
        short_code: str,
        repository: Annotated[
            UrlShortnerRepository, Depends(get_url_shortner_repository)
        ],
    ) -> UrlShortnerRead:
        entity = await repository.get_by_short_code(short_code)
        if entity is None:
            raise HTTPException(status_code=404, detail="URL shortener not found.")
        return UrlShortnerRead.model_validate(entity)
