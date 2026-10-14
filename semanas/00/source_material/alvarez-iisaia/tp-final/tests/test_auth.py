import asyncio
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

import backend.auth as auth_module
from backend.auth import Auth0Provider, AuthIdentity
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
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        login = client.get("/auth/login", follow_redirects=False)
        signup = client.get("/auth/signup", follow_redirects=False)

    assert login.status_code == 302
    assert signup.status_code == 302
    assert provider.authorization_calls[0][2] is None
    assert provider.authorization_calls[1][2] == "signup"


def test_callback_rejects_missing_or_mismatched_state(database_url):
    app, provider = auth_client(database_url)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
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
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
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
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
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


def test_auth0_provider_exchanges_and_validates_id_token_without_network(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url):
            calls.append(("GET", url))
            if url.endswith("openid-configuration"):
                return FakeResponse(
                    {
                        "issuer": "https://identity.test/",
                        "token_endpoint": "https://identity.test/oauth/token",
                        "jwks_uri": "https://identity.test/.well-known/jwks.json",
                    }
                )
            return FakeResponse({"keys": [{"kid": "test-key"}]})

        async def post(self, url, *, data, headers):
            calls.append(("POST", url, data, headers))
            return FakeResponse({"id_token": "signed-id-token"})

    class FakeClaims(dict):
        def validate(self):
            calls.append(("VALIDATE",))

    def fake_decode(encoded, jwks, *, claims_options):
        calls.append(("DECODE", encoded, jwks, claims_options))
        assert claims_options["nonce"]["value"] == "expected-nonce"
        return FakeClaims(
            sub="auth0|owner", email="owner@example.test", name="Propietaria"
        )

    fake_client = FakeClient()
    monkeypatch.setattr(
        auth_module.httpx, "AsyncClient", lambda **_kwargs: fake_client
    )
    monkeypatch.setattr(auth_module.jwt, "decode", fake_decode)
    settings = Settings(
        session_secret="s" * 32,
        auth0_domain="identity.test",
        auth0_client_id="client-id",
        auth0_client_secret="client-secret",
    ).validated()

    identity = asyncio.run(
        Auth0Provider(settings).exchange_code(
            code="authorization-code", nonce="expected-nonce"
        )
    )

    assert identity == AuthIdentity(
        sub="auth0|owner", email="owner@example.test", name="Propietaria"
    )
    assert [call[0] for call in calls] == ["GET", "POST", "GET", "DECODE", "VALIDATE"]
    token_request = calls[1]
    assert token_request[2]["grant_type"] == "authorization_code"
    assert token_request[2]["redirect_uri"] == "http://127.0.0.1:8000/auth/callback"
