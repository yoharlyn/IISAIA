from __future__ import annotations

from urllib.parse import urlparse

from fastapi import Cookie, Depends, Header, Request
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.db import get_db
from backend.errors import APIError
from backend.models import User, UserRole
from backend.services.auth import read_session_token


def verify_csrf(
    request: Request,
    protection: str | None = Header(default=None, alias="X-CSRF-Protection"),
    settings: Settings = Depends(get_settings),
) -> None:
    if (
        protection != "1"
        or request.headers.get("content-type", "").split(";", 1)[0] != "application/json"
    ):
        raise APIError(403, "CSRF_REJECTED", "La solicitud no superó la validación de seguridad.")
    source = request.headers.get("origin")
    if not source:
        referer = request.headers.get("referer")
        if referer:
            parsed = urlparse(referer)
            source = (
                f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else None
            )
    if not source or source.rstrip("/") not in settings.trusted_origins:
        raise APIError(403, "CSRF_REJECTED", "La solicitud no superó la validación de seguridad.")


def get_authenticated_user(
    token: str | None = Cookie(default=None, alias="dentist_session"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if not token:
        raise APIError(401, "NOT_AUTHENTICATED", "Se requiere iniciar sesión.")
    user_id = read_session_token(token, settings.session_secret, settings.session_max_age_seconds)
    if user_id is None:
        raise APIError(401, "NOT_AUTHENTICATED", "La sesión no es válida o expiró.")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise APIError(401, "NOT_AUTHENTICATED", "La sesión no es válida o expiró.")
    return user


def require_dentist(user: User = Depends(get_authenticated_user)) -> User:
    if user.role != UserRole.DENTIST:
        raise APIError(403, "FORBIDDEN_ROLE", "No tiene permisos para acceder a este recurso.")
    return user
