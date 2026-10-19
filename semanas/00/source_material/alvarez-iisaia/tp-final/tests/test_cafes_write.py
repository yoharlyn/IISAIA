from fastapi.testclient import TestClient
from urllib.parse import parse_qs, urlparse

from backend.auth import AuthIdentity
from backend.config import Settings
from backend.main import create_app
from conftest import FakePlacesProvider, TEST_ADDRESS


class PersistenceAuthProvider:
    def authorization_url(self, *, state, nonce, screen_hint=None):
        return f"https://identity.test/authorize?state={state}"

    async def exchange_code(self, *, code, nonce):
        return AuthIdentity(sub="auth0|persistent", email=None, name="Persistente")

    def logout_url(self):
        return "https://identity.test/logout"


def login_for_persistence(client):
    start = client.get("/auth/login", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    client.get("/auth/callback", params={"code": "ok", "state": state}, follow_redirects=False)
    session = client.get("/api/session").json()
    client.headers.update({
        "Origin": "http://127.0.0.1:8000",
        "X-CSRF-Token": session["csrf_token"],
    })


def cafe_payload(**overrides):
    payload = {
        "name": "Lumbre Café",
        "neighborhood": "Boedo",
        "description": "Una barra tranquila con espresso y pastelería artesanal.",
        "place_id": "place-lumbre",
        "selected_address": TEST_ADDRESS,
        "image_url": "https://example.com/cafe.jpg",
        "visit_status": "VISITED",
        "is_favorite": True,
        "coffee_rating": 5,
        "food_rating": 4,
        "ambience_rating": 4,
        "service_rating": 5,
    }
    payload.update(overrides)
    return payload


def test_create_cafe_returns_201_and_updates_stats(client):
    response = client.post("/api/cafes", json=cafe_payload())

    assert response.status_code == 201
    cafe = response.json()
    assert cafe["id"] > 0
    assert cafe["name"] == "Lumbre Café"
    assert cafe["created_at"].endswith("Z")
    assert cafe["updated_at"].endswith("Z")
    assert client.get("/api/stats").json() == {
        "total": 8,
        "visited": 5,
        "pending": 3,
        "favorites": 4,
    }


def test_create_normalizes_strings_and_empty_image(client):
    response = client.post(
        "/api/cafes",
        json=cafe_payload(
            name="  Lumbre Café  ",
            neighborhood="  Boedo ",
            description="  Una descripción válida.  ",
            image_url="   ",
        ),
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Lumbre Café"
    assert response.json()["neighborhood"] == "San Nicolás"
    assert response.json()["description"] == "Una descripción válida."
    assert response.json()["image_url"] is None


def test_create_accepts_optional_description_and_enforces_its_limits(client):
    omitted = cafe_payload(place_id="description-omitted")
    omitted.pop("description")
    responses = [
        client.post("/api/cafes", json=omitted),
        client.post(
            "/api/cafes",
            json=cafe_payload(place_id="description-null", description=None),
        ),
        client.post(
            "/api/cafes",
            json=cafe_payload(place_id="description-empty", description=""),
        ),
        client.post(
            "/api/cafes",
            json=cafe_payload(place_id="description-spaces", description="   "),
        ),
        client.post(
            "/api/cafes",
            json=cafe_payload(place_id="description-one", description=" x "),
        ),
        client.post(
            "/api/cafes",
            json=cafe_payload(place_id="description-600", description="x" * 600),
        ),
    ]

    assert [response.status_code for response in responses] == [201] * 6
    assert [response.json()["description"] for response in responses[:4]] == [
        None,
        None,
        None,
        None,
    ]
    assert responses[4].json()["description"] == "x"
    assert responses[5].json()["description"] == "x" * 600
    assert client.post(
        "/api/cafes",
        json=cafe_payload(place_id="description-601", description="x" * 601),
    ).status_code == 422


def test_create_rejects_invalid_payloads(client):
    invalid_payloads = [
        cafe_payload(name="   "),
        cafe_payload(coffee_rating=0),
        cafe_payload(service_rating=6),
        cafe_payload(image_url="ftp://example.com/cafe.jpg"),
        cafe_payload(visit_status="UNKNOWN"),
        cafe_payload(unexpected="value"),
    ]

    for payload in invalid_payloads:
        assert client.post("/api/cafes", json=payload).status_code == 422


def test_patch_is_partial_and_refreshes_updated_at(client):
    original = client.get("/api/cafes").json()[0]

    response = client.patch(
        f"/api/cafes/{original['id']}",
        json={"name": "  Surco Renovado  ", "coffee_rating": 4},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Surco Renovado"
    assert updated["coffee_rating"] == 4
    assert updated["neighborhood"] == original["neighborhood"]
    assert updated["created_at"] == original["created_at"]
    assert updated["updated_at"] != original["updated_at"]


def test_patch_accepts_null_only_for_image_and_ratings(client):
    cafe_id = client.get("/api/cafes").json()[0]["id"]

    valid = client.patch(
        f"/api/cafes/{cafe_id}",
        json={"image_url": None, "coffee_rating": None},
    )
    invalid = client.patch(f"/api/cafes/{cafe_id}", json={"name": None})

    assert valid.status_code == 200
    assert valid.json()["image_url"] is None
    assert valid.json()["coffee_rating"] is None
    assert invalid.status_code == 422


def test_patch_can_add_change_and_remove_description(client):
    cafe_id = client.post(
        "/api/cafes",
        json=cafe_payload(place_id="description-patch", description=None),
    ).json()["id"]

    added = client.patch(
        f"/api/cafes/{cafe_id}", json={"description": "  Primera nota.  "}
    )
    changed = client.patch(
        f"/api/cafes/{cafe_id}", json={"description": "Nota actualizada."}
    )
    removed = client.patch(
        f"/api/cafes/{cafe_id}", json={"description": "   "}
    )

    assert added.json()["description"] == "Primera nota."
    assert changed.json()["description"] == "Nota actualizada."
    assert removed.json()["description"] is None


def test_patch_rejects_empty_body_and_unknown_fields(client):
    cafe_id = client.get("/api/cafes").json()[0]["id"]

    assert client.patch(f"/api/cafes/{cafe_id}", json={}).status_code == 422
    assert client.patch(
        f"/api/cafes/{cafe_id}", json={"created_at": "2020-01-01T00:00:00Z"}
    ).status_code == 422


def test_patch_toggles_favorite(client):
    original = client.get("/api/cafes", params={"q": "Surco"}).json()[0]

    response = client.patch(
        f"/api/cafes/{original['id']}",
        json={"is_favorite": not original["is_favorite"]},
    )

    assert response.status_code == 200
    assert response.json()["is_favorite"] is True


def test_delete_returns_empty_204_and_removes_cafe(client):
    cafe_id = client.get("/api/cafes").json()[0]["id"]

    response = client.delete(f"/api/cafes/{cafe_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/cafes/{cafe_id}").status_code == 404
    assert client.get("/api/stats").json()["total"] == 6


def test_mutations_return_404_for_missing_cafe(client):
    expected = {"detail": "Cafetería no encontrada."}

    patch = client.patch("/api/cafes/9999", json={"is_favorite": True})
    delete = client.delete("/api/cafes/9999")

    assert patch.status_code == 404 and patch.json() == expected
    assert delete.status_code == 404 and delete.json() == expected


def test_created_cafe_persists_in_a_new_application(database_url):
    settings = Settings(session_secret="p" * 32).validated()
    provider = PersistenceAuthProvider()
    first_app = create_app(
        database_url=database_url, seed_on_startup=False, settings=settings,
        auth_provider=provider, places_provider=FakePlacesProvider()
    )
    with TestClient(first_app, base_url="http://127.0.0.1:8000") as first_client:
        login_for_persistence(first_client)
        created = first_client.post("/api/cafes", json=cafe_payload()).json()

    second_app = create_app(
        database_url=database_url, seed_on_startup=False, settings=settings,
        auth_provider=provider, places_provider=FakePlacesProvider()
    )
    with TestClient(second_app, base_url="http://127.0.0.1:8000") as second_client:
        login_for_persistence(second_client)
        response = second_client.get(f"/api/cafes/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Lumbre Café"
