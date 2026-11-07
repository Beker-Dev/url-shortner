import sqlalchemy as sa
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class BaseEntity(Base):
    __abstract__ = True
    id = sa.Column(sa.UUID, primary_key=True, index=True)
    created_at = sa.Column(sa.DateTime, nullable=False)
    updated_at = sa.Column(sa.DateTime, nullable=False)
