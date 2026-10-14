from datetime import date

import pytest
from sqlmodel import Session, select

from backend.google_places import AddressComponent, Coordinates, PlaceCandidate
from backend.models import Cafe, PlaceDiscovery


CABA_COMPONENTS = (
    AddressComponent(
        long_text="Ciudad Autónoma de Buenos Aires",
        short_text="CABA",
        types=("administrative_area_level_1",),
    ),
)


def candidate(**overrides):
    values = {
        "place_id": "recommendation-1",
        "display_name": "Café recomendado",
        "formatted_address": "Av. Corrientes 1000, CABA",
        "address_components": CABA_COMPONENTS,
        "location": Coordinates(-34.6038, -58.3817),
        "primary_type": "cafe",
        "business_status": "OPERATIONAL",
        "rating": 4.5,
        "user_rating_count": 120,
        "opening_date": None,
        "google_maps_uri": "https://maps.google.com/?cid=test",
    }
    values.update(overrides)
    return PlaceCandidate(**values)


def test_recommendations_score_sort_and_persist_only_discovery_metadata(client, app):
    async def nearby(**_kwargs):
        return [
            candidate(),
            candidate(
                place_id="recommendation-2",
                display_name="Sin rating",
                location=Coordinates(-34.604, -58.382),
                rating=None,
                user_rating_count=None,
                opening_date=date(2027, 1, 1),
            ),
        ]

    app.state.places_provider.nearby = nearby
    response = client.post(
        "/api/recommendations/search",
        json={
            "origin": {"type": "current", "latitude": -34.6037, "longitude": -58.3816},
            "radius_km": 3,
        },
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    rows = response.json()
    assert {row["place_id"] for row in rows} == {"recommendation-1", "recommendation-2"}
    assert [row["score"] for row in rows] == sorted(
        [row["score"] for row in rows], reverse=True
    )
    assert all(row["attribution"] == "Google Maps" for row in rows)
    without_rating = next(row for row in rows if row["place_id"] == "recommendation-2")
    assert without_rating["opening_date"] == "2027-01-01"
    assert sum(without_rating["factors"].values()) == pytest.approx(
        without_rating["score"]
    )
    with Session(app.state.engine) as db:
        discoveries = db.exec(select(PlaceDiscovery)).all()
        assert {item.place_id for item in discoveries} == {
            "recommendation-1",
            "recommendation-2",
        }
    with app.state.engine.connect() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(place_discoveries)"
            ).fetchall()
        }
    assert columns == {"id", "owner_id", "place_id", "first_seen_at", "last_seen_at"}


def test_recommendations_drop_outside_caba_and_permanently_closed(client, app):
    async def nearby(**_kwargs):
        return [
            candidate(place_id="closed", business_status="CLOSED_PERMANENTLY"),
            candidate(
                place_id="outside",
                location=Coordinates(-34.9215, -57.9545),
            ),
        ]

    app.state.places_provider.nearby = nearby
    response = client.post(
        "/api/recommendations/search",
        json={
            "origin": {"type": "current", "latitude": -34.6037, "longitude": -58.3816},
            "radius_km": 5,
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_prepare_and_save_require_confirmed_address_and_local_name(client, app):
    prepare = client.post("/api/recommendations/recommendation-1/prepare-save")
    mismatch = client.post(
        "/api/recommendations/recommendation-1/save",
        json={
            "name": "Nombre local",
            "description": "Confirmada por la persona usuaria.",
            "selected_address": "Dirección diferente",
        },
    )
    saved = client.post(
        "/api/recommendations/recommendation-1/save",
        json={
            "name": "Nombre local",
            "description": "Confirmada por la persona usuaria.",
            "selected_address": "Av. Corrientes 1000, CABA",
        },
    )

    assert prepare.status_code == 200
    assert prepare.json()["attribution"] == "Google Maps"
    assert mismatch.status_code == 422
    assert saved.status_code == 201
    with Session(app.state.engine) as db:
        cafe = db.exec(select(Cafe).where(Cafe.place_id == "recommendation-1")).one()
        assert cafe.name == "Nombre local"
        assert cafe.selected_address == "Av. Corrientes 1000, CABA"


def test_recommendation_radius_is_capped_at_five_km(client):
    response = client.post(
        "/api/recommendations/search",
        json={
            "origin": {"type": "current", "latitude": -34.6, "longitude": -58.4},
            "radius_km": 5.1,
        },
    )
    assert response.status_code == 422
