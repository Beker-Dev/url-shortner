import pydantic
from uuid import UUID
from datetime import datetime


class UrlShortnerBase(pydantic.BaseModel):
    id: UUID
    target_url: pydantic.HttpUrl
    short_code: str

    class Config:
        orm_mode = True


class UrlShortnerCreate(UrlShortnerBase):
    target_url: pydantic.HttpUrl
    short_code: str

    class Config:
        orm_mode = True
        
class UrlShortnerRead(UrlShortnerBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
    