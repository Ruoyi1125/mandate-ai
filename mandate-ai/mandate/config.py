"""Configuration helpers for MANDATE."""

from __future__ import annotations

from pathlib import Path
import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime settings loaded from environment variables."""

    env: str = Field(default_factory=lambda: os.getenv("MANDATE_ENV", "development"))
    rules_path: Path = Field(
        default_factory=lambda: Path(
            os.getenv("MANDATE_RULES_PATH", "rules/authorization_rules.yaml")
        )
    )


def get_settings() -> Settings:
    """Return application settings."""

    return Settings()
