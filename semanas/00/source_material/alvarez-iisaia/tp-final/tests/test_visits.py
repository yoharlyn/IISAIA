from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient


def _login(client: TestClient, code: str):
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


def _pending_cafe(client: TestClient) -> dict:
    return client.get("/api/cafes", params={"visit_status": "PENDING"}).json()[0]


def test_visit_crud_drives_status_and_rating_averages(client):
    cafe = _pending_cafe(client)
    first = client.post(
        f"/api/cafes/{cafe['id']}/visits",
        json={
            "visited_at": "2026-09-01T14:30:00-03:00",
            "note": "  Primera visita  ",
            "coffee_rating": 5,
            "food_rating": 3,
            "ambience_rating": 4,
            "service_rating": 5,
        },
    )
    assert first.status_code == 201
    assert first.json()["note"] == "Primera visita"
    assert first.json()["visited_at"] == "2026-09-01T17:30:00Z"

    second = client.post(
        f"/api/cafes/{cafe['id']}/visits",
        json={
            "visited_at": "2026-10-01T12:00:00Z",
            "coffee_rating": 3,
            "food_rating": 5,
            "ambience_rating": 2,
            "service_rating": 3,
            "date_is_estimated": True,
        },
    )
    assert second.status_code == 201

    visits = client.get(f"/api/cafes/{cafe['id']}/visits").json()
    assert [row["id"] for row in visits] == [second.json()["id"], first.json()["id"]]
    refreshed = client.get(f"/api/cafes/{cafe['id']}").json()
    assert refreshed["visit_status"] == "VISITED"
    assert refreshed["coffee_rating"] == 4.0
    assert refreshed["food_rating"] == 4.0
    assert refreshed["ambience_rating"] == 3.0
    assert refreshed["service_rating"] == 4.0

    patched = client.patch(
        f"/api/visits/{second.json()['id']}",
        json={"note": "Volvería", "service_rating": 5},
    )
    assert patched.status_code == 200
    assert patched.json()["note"] == "Volvería"
    assert patched.json()["service_rating"] == 5

    assert client.delete(f"/api/visits/{first.json()['id']}").status_code == 204
    assert client.delete(f"/api/visits/{second.json()['id']}").status_code == 204
    assert client.get(f"/api/cafes/{cafe['id']}").json()["visit_status"] == "PENDING"


def test_visit_validation_and_cross_owner_isolation(client, app):
    cafe = _pending_cafe(client)
    invalid = client.post(
        f"/api/cafes/{cafe['id']}/visits",
        json={"coffee_rating": 6},
    )
    assert invalid.status_code == 422

    created = client.post(
        f"/api/cafes/{cafe['id']}/visits",
        json={"note": "Privada", "coffee_rating": 4},
    ).json()
    assert client.patch(f"/api/visits/{created['id']}", json={}).status_code == 422

    with TestClient(app, base_url="http://127.0.0.1:8000") as second:
        _login(second, "second")
        assert second.get(f"/api/cafes/{cafe['id']}/visits").status_code == 404
        assert second.post(f"/api/cafes/{cafe['id']}/visits", json={}).status_code == 404
        assert second.patch(
            f"/api/visits/{created['id']}", json={"note": "Intrusión"}
        ).status_code == 404
        assert second.delete(f"/api/visits/{created['id']}").status_code == 404
