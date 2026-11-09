import re
from typing import Annotated, Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


_KEYSPACE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    cassandra_contact_points: Annotated[tuple[str, ...], NoDecode] = Field(
        validation_alias="CASSANDRA_CONTACT_POINTS",
    )
    cassandra_port: int = Field(
        ge=1,
        le=65535,
        validation_alias="CASSANDRA_PORT",
    )
    cassandra_keyspace: str = Field(
        validation_alias="CASSANDRA_KEYSPACE",
    )
    cassandra_username: str | None = Field(
        validation_alias="CASSANDRA_USERNAME",
    )
    cassandra_password: str | None = Field(
        validation_alias="CASSANDRA_PASSWORD",
    )
    redis_url: str = Field(
        validation_alias="REDIS_URL",
    )
    url_cache_redis_url: str = Field(
        validation_alias="URL_CACHE_REDIS_URL",
    )
    short_code_secret_key: str = Field(
        min_length=6,
        validation_alias="SHORT_CODE_SECRET_KEY",
    )

    @field_validator("cassandra_contact_points", mode="before")
    @classmethod
    def parse_contact_points(cls, value: Any) -> tuple[str, ...]:
        if isinstance(value, str):
            contact_points = tuple(point.strip() for point in value.split(","))
        else:
            contact_points = tuple(str(point).strip() for point in value)

        contact_points = tuple(point for point in contact_points if point)
        if not contact_points:
            raise ValueError("CASSANDRA_CONTACT_POINTS must not be empty.")
        return contact_points

    @field_validator("cassandra_username", "cassandra_password", mode="before")
    @classmethod
    def empty_credentials_are_missing(cls, value: Any) -> Any:
        return None if value == "" else value

    @field_validator("cassandra_keyspace")
    @classmethod
    def validate_keyspace(cls, value: str) -> str:
        if not _KEYSPACE_PATTERN.fullmatch(value):
            raise ValueError(
                "CASSANDRA_KEYSPACE must start with a letter and contain only "
                "letters, digits, or underscores."
            )
        return value

    @model_validator(mode="after")
    def validate_cassandra_credentials(self) -> "EnvSettings":
        if bool(self.cassandra_username) != bool(self.cassandra_password):
            raise ValueError(
                "CASSANDRA_USERNAME and CASSANDRA_PASSWORD must be set together."
            )
        return self
