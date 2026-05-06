from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import structlog
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CUDDLY_",
        env_file=".env",
        extra="ignore",
    )

    db_path: Path = Field(default_factory=lambda: Path.home() / ".cuddly" / "cuddly.db")
    embed_model: str = "all-MiniLM-L6-v2"
    embed_device: str = "cpu"
    log_level: str = "INFO"
    project_root: Path = Field(default_factory=Path.cwd)


@lru_cache(maxsize=1)
def get_config() -> Config:
    return Config()


def setup_logging(level: str = "INFO", *, json_logs: bool = False) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
    processors: list = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(processors=processors)
