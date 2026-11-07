from fastapi import APIRouter

from src.application.controller.url_shortner import router as url_shortner_router


router = APIRouter(prefix="/api")
router.include_router(url_shortner_router)
