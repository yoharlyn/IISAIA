from dataclasses import dataclass
from os import environ
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_BASE_URL = "http://127.0.0.1:8000"


class ConfigurationError(ValueError):
    """Indica una configuración insegura o incoherente."""


def _env(name: str, default: str = "") -> str:
    return environ.get(name, default).strip()


@dataclass(frozen=True, slots=True)
class Settings:
    app_base_url: str = CANONICAL_BASE_URL
    app_env: str = "development"
    session_secret: str = ""
    auth0_domain: str = ""
    auth0_client_id: str = ""
    auth0_client_secret: str = ""
    auth0_callback_url: str = f"{CANONICAL_BASE_URL}/auth/callback"
    auth0_logout_return_url: str = f"{CANONICAL_BASE_URL}/"
    legacy_owner_auth0_sub: str = ""
    database_url: str = ""
    upload_dir: str = ""

    @classmethod
    def from_env(cls, *, load_file: bool = True) -> "Settings":
        if load_file:
            load_dotenv(PROJECT_ROOT / ".env", override=False)
        return cls(
            app_base_url=_env("APP_BASE_URL", CANONICAL_BASE_URL),
            app_env=_env("APP_ENV", "development"),
            session_secret=_env("SESSION_SECRET"),
            auth0_domain=_env("AUTH0_DOMAIN"),
            auth0_client_id=_env("AUTH0_CLIENT_ID"),
            auth0_client_secret=_env("AUTH0_CLIENT_SECRET"),
            auth0_callback_url=_env(
                "AUTH0_CALLBACK_URL", f"{CANONICAL_BASE_URL}/auth/callback"
            ),
            auth0_logout_return_url=_env(
                "AUTH0_LOGOUT_RETURN_URL", f"{CANONICAL_BASE_URL}/"
            ),
            legacy_owner_auth0_sub=_env("LEGACY_OWNER_AUTH0_SUB"),
            database_url=_env("DATABASE_URL"),
            upload_dir=_env("UPLOAD_DIR"),
        ).validated()

    def validated(self, *, require_auth0: bool = False) -> "Settings":
        if self.app_base_url != CANONICAL_BASE_URL:
            raise ConfigurationError(
                f"APP_BASE_URL debe ser exactamente {CANONICAL_BASE_URL}."
            )
        expected_callback = f"{CANONICAL_BASE_URL}/auth/callback"
        if self.auth0_callback_url != expected_callback:
            raise ConfigurationError(
                f"AUTH0_CALLBACK_URL debe ser exactamente {expected_callback}."
            )
        if self.auth0_logout_return_url != f"{CANONICAL_BASE_URL}/":
            raise ConfigurationError(
                "AUTH0_LOGOUT_RETURN_URL debe usar el origen canónico y terminar en /."
            )
        if self.session_secret and len(self.session_secret) < 32:
            raise ConfigurationError("SESSION_SECRET debe tener al menos 32 caracteres.")
        if require_auth0:
            missing = [
                name
                for name, value in (
                    ("SESSION_SECRET", self.session_secret),
                    ("AUTH0_DOMAIN", self.auth0_domain),
                    ("AUTH0_CLIENT_ID", self.auth0_client_id),
                    ("AUTH0_CLIENT_SECRET", self.auth0_client_secret),
                )
                if not value
            ]
            if missing:
                raise ConfigurationError(
                    "Faltan variables requeridas: " + ", ".join(missing) + "."
                )
        if self.auth0_domain:
            parsed = urlparse(f"https://{self.auth0_domain}")
            if parsed.hostname != self.auth0_domain or parsed.path not in ("", "/"):
                raise ConfigurationError("AUTH0_DOMAIN debe contener sólo el hostname.")
        return self

    def public_summary(self) -> dict[str, str]:
        """Expone únicamente valores no secretos para diagnóstico."""
        return {
            "app_base_url": self.app_base_url,
            "app_env": self.app_env,
            "auth0_configured": str(
                bool(self.auth0_domain and self.auth0_client_id and self.auth0_client_secret)
            ).lower(),
        }
