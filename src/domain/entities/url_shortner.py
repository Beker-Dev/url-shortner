from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UrlShortnerEntity:
    id: UUID
    target_url: str
    short_code: str
    created_at: datetime
    updated_at: datetime
    