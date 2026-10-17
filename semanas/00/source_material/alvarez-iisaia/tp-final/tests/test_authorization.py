from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from conftest import TEST_ADDRESS


def login(client: TestClient, code: str):
    start = client.get("/auth/login", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": code, "state": state},
        follow_redirects=False,
    )
    payload = client.get("/api/session").json()
    client.headers.update(
        {
            "Origin": "http://127.0.0.1:8000",
            "X-CSRF-Token": payload["csrf_token"],
        }
    )
    return payload


def test_endpoints_require_authentication(app):
    with TestClient(app, base_url="http://127.0.0.1:8000") as anonymous:
        assert anonymous.get("/api/cafes").status_code == 401
        assert anonymous.get("/api/stats").status_code == 401
        assert anonymous.get("/api/neighborhoods").status_code == 401
        assert anonymous.post("/api/cafes", json={}).status_code == 401
        assert anonymous.post("/api/places/place-id/prepare-cafe").status_code == 401


def test_two_users_cannot_access_each_others_cafes(app):
    with TestClient(app, base_url="http://127.0.0.1:8000") as owner:
        login(owner, "owner")
        created = owner.post(
            "/api/cafes",
            json={
                "name": "Privada",
                "neighborhood": "Boedo",
                "description": "Sólo visible para su propietaria.",
                "place_id": "place-private",
                "selected_address": TEST_ADDRESS,
            },
        ).json()

    with TestClient(app, base_url="http://127.0.0.1:8000") as second:
        login(second, "second")
        assert second.get(f"/api/cafes/{created['id']}").status_code == 404
        assert second.patch(f"/api/cafes/{created['id']}", json={"name": "Intrusión"}).status_code == 404
        assert second.delete(f"/api/cafes/{created['id']}").status_code == 404
        assert second.get("/api/cafes").json() == []
        assert second.get("/api/stats").json() == {
            "total": 0,
            "visited": 0,
            "pending": 0,
            "favorites": 0,
        }


def test_mutations_require_matching_origin_and_csrf(client):
    payload = {
        "name": "CSRF",
        "neighborhood": "Flores",
        "description": "Caso de seguridad.",
        "place_id": "place-csrf",
        "selected_address": TEST_ADDRESS,
    }
    csrf = client.headers["X-CSRF-Token"]
    assert client.post(
        "/api/cafes",
        json=payload,
        headers={"Origin": "https://attacker.invalid", "X-CSRF-Token": csrf},
    ).status_code == 403
    assert client.post(
        "/api/cafes",
        json=payload,
        headers={"Origin": "http://127.0.0.1:8000", "X-CSRF-Token": "bad"},
    ).status_code == 403
