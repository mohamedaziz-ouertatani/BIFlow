"""Shared configuration loading for all BIFlow services.

TODO (owner): load settings from environment variables / .env (see
.env.example) using pydantic-settings or similar, and expose a single
`get_settings()` accessor used by the orchestrator, agents, and dashboard.
"""

from pydantic import BaseModel


class Settings(BaseModel):
    """Application-wide settings shared across agents.

    TODO: confirm fields — e.g. database_url, log_level, llm_provider,
    llm_model, data_dir.
    """

    database_url: str = ""
    log_level: str = "INFO"


def get_settings() -> Settings:
    """Load and return the shared Settings instance.

    TODO (owner): implement loading from environment/.env.
    """
    raise NotImplementedError("TODO: implement settings loading")
