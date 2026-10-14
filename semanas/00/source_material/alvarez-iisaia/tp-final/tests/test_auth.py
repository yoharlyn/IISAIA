from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from backend.auth import AuthIdentity
from backend.config import Settings
from backend.main import create_app
from backend.models import LocalSession, User
from backend.security import SESSION_COOKIE_NAME


class FakeAuthProvider:
    def __init__(self, *, fail_exchange: bool = False):
        self.fail_exchange = fail_exchange
        self.authorization_calls = []
        self.exchange_calls = []

    def authorization_url(self, *, state, nonce, screen_hint=None):
        self.authorization_calls.append((state, nonce, screen_hint))
        return f"https://identity.test/authorize?state={state}"

    async def exchange_code(self, *, code, nonce):
        self.exchange_calls.append((code, nonce))
        if self.fail_exchange:
            raise RuntimeError("El proveedor falso falló")
        return AuthIdentity(
            sub="auth0|owner", email="owner@example.test", name="Propietaria"
        )

    def logout_url(self):
        return "https://identity.test/logout"


def auth_client(database_url, provider=None):
    provider = provider or FakeAuthProvider()
    settings = Settings(session_secret="t" * 32).validated()
    app = create_app(
        database_url=database_url,
        seed_on_startup=False,
        settings=settings,
        auth_provider=provider,
    )
    return app, provider


def complete_login(client, provider):
    start = client.get("/auth/login", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    return client.get(
        "/auth/callback",
        params={"code": "valid-code", "state": state},
        follow_redirects=False,
    )


def test_login_and_signup_create_signed_transactions_without_network(database_url):
    app, provider = auth_client(database_url)
    with TestClient(app) as client:
        login = client.get("/auth/login", follow_redirects=False)
        signup = client.get("/auth/signup", follow_redirects=False)

    assert login.status_code == 302
    assert signup.status_code == 302
    assert provider.authorization_calls[0][2] is None
    assert provider.authorization_calls[1][2] == "signup"


def test_callback_rejects_missing_or_mismatched_state(database_url):
    app, provider = auth_client(database_url)
    with TestClient(app) as client:
        missing = client.get(
            "/auth/callback",
            params={"code": "code", "state": "missing"},
        )
        client.get("/auth/login", follow_redirects=False)
        mismatch = client.get(
            "/auth/callback",
            params={"code": "code", "state": "wrong"},
        )

    assert missing.status_code == 400
    assert mismatch.status_code == 400
    assert provider.exchange_calls == []


def test_callback_creates_user_and_opaque_local_session(database_url):
    app, provider = auth_client(database_url)
    with TestClient(app) as client:
        response = complete_login(client, provider)
        raw_cookie = client.cookies.get(SESSION_COOKIE_NAME)

        assert response.status_code == 303
        assert raw_cookie
        session = client.get("/api/session")
        assert session.status_code == 200
        assert session.json()["user"]["display_name"] == "Propietaria"

    with Session(app.state.engine) as db:
        assert db.exec(select(func.count()).select_from(User)).one() == 1
        stored = db.exec(select(LocalSession)).one()
        assert stored.token_hash != raw_cookie


def test_callback_handles_provider_failure_without_creating_session(database_url):
    app, provider = auth_client(database_url, FakeAuthProvider(fail_exchange=True))
    with TestClient(app) as client:
        response = complete_login(client, provider)
        assert response.status_code == 503
        assert client.cookies.get(SESSION_COOKIE_NAME) is None


def test_logout_requires_csrf_and_invalidates_local_session(database_url):
    app, provider = auth_client(database_url)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        complete_login(client, provider)
        session_payload = client.get("/api/session").json()

        rejected = client.post("/auth/logout", follow_redirects=False)
        accepted = client.post(
            "/auth/logout",
            headers={
                "Origin": "http://127.0.0.1:8000",
                "X-CSRF-Token": session_payload["csrf_token"],
            },
            follow_redirects=False,
        )

        assert rejected.status_code == 403
        assert accepted.status_code == 303
        assert accepted.headers["location"] == "https://identity.test/logout"
        assert client.get("/api/session").status_code == 401
