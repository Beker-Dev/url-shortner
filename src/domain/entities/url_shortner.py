import sqlalchemy as sa
from src.domain.entities.base_entity import BaseEntity


class UrlShortnerEntity(BaseEntity):
    __tablename__ = "url_shortner"
    target_url = sa.Column(sa.String(2048), nullable=False)
    short_code = sa.Column(sa.String(7), nullable=False, unique=True, index=True)
    