from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl


class UrlShortnerCreate(BaseModel):
    target_url: HttpUrl


class UrlShortnerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_url: HttpUrl
    short_code: str
    created_at: datetime
    updated_at: datetime