from fastapi.testclient import TestClient

from backend.main import create_app


def cafe_payload(**overrides):
    payload = {
        "name": "Lumbre Café",
        "neighborhood": "Boedo",
        "description": "Una barra tranquila con espresso y pastelería artesanal.",
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
    assert response.json()["neighborhood"] == "Boedo"
    assert response.json()["description"] == "Una descripción válida."
    assert response.json()["image_url"] is None


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
    first_app = create_app(database_url=database_url)
    with TestClient(first_app) as first_client:
        created = first_client.post("/api/cafes", json=cafe_payload()).json()

    second_app = create_app(database_url=database_url)
    with TestClient(second_app) as second_client:
        response = second_client.get(f"/api/cafes/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Lumbre Café"
