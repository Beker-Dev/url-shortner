from fastapi import FastAPI

from src.application.controller.routers import router as api_router
from src.infrastructure.lifespan import lifespan


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
