import pytest
from fastapi.testclient import TestClient
from urllib.parse import parse_qs, urlparse

from backend.auth import AuthIdentity
from backend.config import Settings
from backend.main import create_app
from backend.seed import seed_cafes


class FakeAuthProvider:
    def authorization_url(self, *, state, nonce, screen_hint=None):
        return f"https://identity.test/authorize?state={state}"

    async def exchange_code(self, *, code, nonce):
        sub = "auth0|second" if code == "second" else "auth0|owner"
        return AuthIdentity(sub=sub, email=f"{sub}@example.test", name=sub)

    def logout_url(self):
        return "https://identity.test/logout"


@pytest.fixture
def database_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def app(database_url):
    return create_app(
        database_url=database_url,
        seed_on_startup=False,
        settings=Settings(session_secret="t" * 32).validated(),
        auth_provider=FakeAuthProvider(),
    )


@pytest.fixture
def client(app):
    with TestClient(app, base_url="http://127.0.0.1:8000") as test_client:
        start = test_client.get("/auth/login", follow_redirects=False)
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        test_client.get(
            "/auth/callback",
            params={"code": "owner", "state": state},
            follow_redirects=False,
        )
        session_payload = test_client.get("/api/session").json()
        seed_cafes(app.state.engine, session_payload["user"]["id"])
        test_client.headers.update(
            {
                "Origin": "http://127.0.0.1:8000",
                "X-CSRF-Token": session_payload["csrf_token"],
            }
        )
        yield test_client
