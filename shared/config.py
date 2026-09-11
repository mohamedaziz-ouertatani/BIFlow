"""Shared configuration loading for all BIFlow services."""

import os

from pydantic import BaseModel

DEFAULT_DATABASE_URL = "postgresql://biflow:biflow@localhost:5433/biflow"


class Settings(BaseModel):
    """Application-wide settings shared across agents."""

    database_url: str = DEFAULT_DATABASE_URL
    log_level: str = "INFO"


def get_settings() -> Settings:
    """Load and return the shared Settings instance from environment variables.

    Defaults `database_url` to the host-side connection string (the docker
    .env overrides it to use the `db` service hostname when running inside
    containers).
    """
    return Settings(
        database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )
