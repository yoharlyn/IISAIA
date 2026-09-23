from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(
        value.strip().rstrip("/") for value in os.getenv(name, default).split(",") if value.strip()
    )


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    session_secret: str
    session_max_age_seconds: int
    session_cookie_secure: bool
    allowed_origins: tuple[str, ...]
    trusted_origins: tuple[str, ...]
    log_level: str

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "development").lower()
    secret = os.getenv("SESSION_SECRET", "development-only-secret-change-me-32")
    secure = _bool("SESSION_COOKIE_SECURE", app_env == "production")
    if app_env == "production" and (len(secret) < 32 or not secure):
        raise RuntimeError("Production requires a 32+ character secret and Secure cookies")
    return Settings(
        app_env=app_env,
        database_url=os.getenv("DATABASE_URL", "sqlite:///./var/app.db"),
        session_secret=secret,
        session_max_age_seconds=int(os.getenv("SESSION_MAX_AGE_SECONDS", "28800")),
        session_cookie_secure=secure,
        allowed_origins=_csv("ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000"),
        trusted_origins=_csv("TRUSTED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
