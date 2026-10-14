from datetime import datetime, timezone

from sqlmodel import Session

from backend.models import Cafe, VisitStatus


def test_list_returns_seed_in_update_order(client):
    response = client.get("/api/cafes")

    assert response.status_code == 200
    cafes = response.json()
    assert len(cafes) == 7
    ordering = [(item["updated_at"], item["id"]) for item in cafes]
    assert ordering == sorted(ordering, reverse=True)
    assert cafes[0]["name"] == "Surco Café"
    assert cafes[0]["created_at"].endswith("Z")


def test_get_cafe_returns_all_public_fields(client):
    cafe_id = client.get("/api/cafes").json()[0]["id"]

    response = client.get(f"/api/cafes/{cafe_id}")

    assert response.status_code == 200
    assert set(response.json()) == {
        "id",
        "name",
        "neighborhood",
        "description",
        "image_url",
        "visit_status",
        "is_favorite",
        "coffee_rating",
        "food_rating",
        "ambience_rating",
        "service_rating",
        "created_at",
        "updated_at",
    }


def test_search_is_case_insensitive_and_partial(client):
    response = client.get("/api/cafes", params={"q": "bRuMa"})

    assert response.status_code == 200
    assert [cafe["name"] for cafe in response.json()] == ["Bruma Café"]


def test_search_treats_sql_wildcards_as_literals(client, app):
    now = datetime.now(timezone.utc)
    with Session(app.state.engine) as session:
        session.add(
            Cafe(
                owner_id=client.get("/api/session").json()["user"]["id"],
                name="Café 100%",
                neighborhood="Centro",
                description="Nombre usado para comprobar búsqueda literal.",
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    percent = client.get("/api/cafes", params={"q": "%"})
    underscore = client.get("/api/cafes", params={"q": "_"})

    assert [cafe["name"] for cafe in percent.json()] == ["Café 100%"]
    assert underscore.json() == []


def test_filters_are_case_insensitive_and_combined(client):
    response = client.get(
        "/api/cafes",
        params={
            "neighborhood": "palermo",
            "visit_status": "VISITED",
            "is_favorite": "true",
        },
    )

    assert response.status_code == 200
    assert [cafe["name"] for cafe in response.json()] == ["Bruma Café"]


def test_valid_filters_can_return_an_empty_list(client):
    response = client.get("/api/cafes", params={"q": "No existe"})

    assert response.status_code == 200
    assert response.json() == []


def test_stats_are_global(client):
    response = client.get("/api/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total": 7,
        "visited": 4,
        "pending": 3,
        "favorites": 3,
    }


def test_missing_cafe_returns_domain_error(client):
    response = client.get("/api/cafes/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Cafetería no encontrada."}


def test_invalid_query_and_path_return_422(client):
    assert client.get("/api/cafes", params={"q": ""}).status_code == 422
    assert client.get("/api/cafes", params={"q": "   "}).status_code == 422
    assert client.get("/api/cafes", params={"visit_status": "UNKNOWN"}).status_code == 422
    assert client.get("/api/cafes/0").status_code == 422
