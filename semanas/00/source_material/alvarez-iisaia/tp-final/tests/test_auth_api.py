from fastapi.testclient import TestClient

from backend.config import Settings, get_settings
from backend.main import app
from backend.services.auth import create_session_token, read_session_token


def test_login_me_logout_flow(client: TestClient, csrf_headers: dict[str, str]) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"username": " DENTISTA.DEMO ", "password": "DemoSegura123!"},
        headers=csrf_headers,
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "DENTIST"
    cookie = login.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Max-Age=28800" in cookie
    assert "Secure" not in cookie

    assert client.get("/api/v1/auth/me").status_code == 200
    logout = client.post("/api/v1/auth/logout", json={}, headers=csrf_headers)
    assert logout.status_code == 204
    assert 'dentist_session=""' in logout.headers["set-cookie"]
    assert client.get("/api/v1/auth/me").status_code == 401


def test_invalid_inactive_and_wrong_role_are_generic(
    client: TestClient, csrf_headers: dict[str, str]
) -> None:
    attempts = [
        ("no-existe", "DemoSegura123!"),
        ("dentista.demo", "ClaveMala123!"),
        ("inactivo.demo", "Inactiva123!"),
        ("admin.demo", "AdminSegura123!"),
    ]
    messages = set()
    for username, password in attempts:
        response = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
            headers=csrf_headers,
        )
        assert response.status_code == 401
        messages.add((response.json()["error"]["code"], response.json()["error"]["message"]))
    assert len(messages) == 1


def test_me_without_or_with_tampered_session_is_unauthorized(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set("dentist_session", "tampered")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_session_token_expiration() -> None:
    secret = "expiration-test-secret-at-least-32-characters"
    token = create_session_token(7, secret)
    assert read_session_token(token, secret, 60) == 7
    assert read_session_token(token, secret, -1) is None


def test_production_cookie_is_secure(client: TestClient, csrf_headers: dict[str, str]) -> None:
    production = Settings(
        app_env="production",
        database_url="sqlite:///:memory:",
        session_secret="production-test-secret-at-least-32-characters",
        session_max_age_seconds=28800,
        session_cookie_secure=True,
        allowed_origins=("http://testserver",),
        trusted_origins=("http://testserver",),
        log_level="INFO",
    )
    app.dependency_overrides[get_settings] = lambda: production
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "dentista.demo", "password": "DemoSegura123!"},
        headers=csrf_headers,
    )
    assert response.status_code == 200
    assert "Secure" in response.headers["set-cookie"]
