from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.models import User
from backend.services.auth import create_session_token


def test_catalog_requires_session(client: TestClient) -> None:
    assert client.get("/api/v1/products").status_code == 401


def test_wrong_role_session_is_forbidden(client: TestClient, db_session: Session) -> None:
    admin = db_session.scalar(select(User).where(User.username == "admin.demo"))
    token = create_session_token(admin.id, get_settings().session_secret)
    client.cookies.set("dentist_session", token)
    assert client.get("/api/v1/auth/me").status_code == 403
    assert client.get("/api/v1/products").status_code == 403
