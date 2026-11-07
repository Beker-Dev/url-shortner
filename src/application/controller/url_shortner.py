from fastapi_utils.cbv import cbv
from fastapi import APIRouter, Depends

from typing import List

from src.domain.dtos.url_shortner import UrlShortnerCreate, UrlShortnerRead

router = APIRouter(prefix="/url-shortner", tags=["url-shortner"])

@cbv(router)
class UrlShortnerController:
    # session: Session = Depends(get_session)
    
    @router.post(
        "/new",
        response_model=UrlShortnerRead,
        summary="Create URL Shortener"
    )
    async def create_url_shortner(self, url_shortner: UrlShortnerCreate):
        # Logic to create a new URL shortener entry
        pass
    
    @router.get(
        "/",
        response_model=List[UrlShortnerRead],
        summary="Get All URL Shorteners"
    )
    async def get_all_url_shortners(self):
        # Logic to retrieve all URL shortener entries
        pass    
    
    @router.get(
        "/{short_code}",
        response_model=UrlShortnerRead,
        summary="Get URL Shortener by Short Code"
    )
    async def get_url_shortner_by_short_code(self, short_code: str):
        # Logic to retrieve a URL shortener entry by short code
        pass
    
    
