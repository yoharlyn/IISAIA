from fastapi.testclient import TestClient


def test_mutations_require_csrf_headers(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "dentista.demo", "password": "DemoSegura123!"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_REJECTED"


def test_rate_limit_after_five_failures(client: TestClient, csrf_headers: dict[str, str]) -> None:
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "dentista.demo", "password": "Equivocada123!"},
            headers=csrf_headers,
        )
        assert response.status_code == 401
    blocked = client.post(
        "/api/v1/auth/login",
        json={"username": "dentista.demo", "password": "DemoSegura123!"},
        headers=csrf_headers,
    )
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_request_id_is_preserved_or_generated(client: TestClient) -> None:
    assert (
        client.get("/api/v1/auth/me", headers={"X-Request-ID": "demo-123"}).headers["X-Request-ID"]
        == "demo-123"
    )
    assert (
        client.get("/api/v1/auth/me", headers={"X-Request-ID": "bad value"}).headers["X-Request-ID"]
        != "bad value"
    )


def test_cors_allows_only_configured_origin(client: TestClient) -> None:
    allowed = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://testserver",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,X-CSRF-Protection",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://testserver"
    denied = client.options(
        "/api/v1/auth/login",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers
