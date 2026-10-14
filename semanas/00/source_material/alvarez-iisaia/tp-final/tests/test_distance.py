from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

from backend.distance import haversine_km
from backend.google_places import Coordinates
from backend.models import Cafe, User


def test_haversine_known_distance_and_symmetry():
    buenos_aires = Coordinates(-34.6037, -58.3816)
    montevideo = Coordinates(-34.9011, -56.1645)

    distance = haversine_km(buenos_aires, montevideo)

    assert distance == pytest.approx(205.5, abs=1.5)
    assert distance == pytest.approx(haversine_km(montevideo, buenos_aires))
    assert haversine_km(buenos_aires, buenos_aires) == 0


def test_current_location_search_is_post_no_store_and_not_persisted(client, app):
    now = datetime.now(timezone.utc)
    with Session(app.state.engine) as db:
        owner = db.exec(select(User).where(User.auth0_sub == "auth0|owner")).one()
        db.add(
            Cafe(
                owner_id=owner.id,
                name="Cercana",
                neighborhood="San Nicolas",
                description="Con ubicación vigente.",
                place_id="nearby-local",
                selected_address="Av. Corrientes 1000, CABA",
                latitude=-34.6038,
                longitude=-58.3817,
                location_fetched_at=now,
                location_expires_at=now + timedelta(days=29),
                location_status="VERIFIED",
            )
        )
        db.commit()

    response = client.post(
        "/api/cafes/search",
        json={
            "origin": {"type": "current", "latitude": -34.6037, "longitude": -58.3816},
            "radius_km": 1,
        },
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()[0]["name"] == "Cercana"
    assert response.json()[0]["distance_km"] == pytest.approx(0.014, abs=0.005)
    assert "latitude" not in str(response.request.url)
    with app.state.engine.connect() as connection:
        user_columns = {
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(users)")
        }
        session_columns = {
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(sessions)")
        }
    assert "current_latitude" not in user_columns | session_columns


def test_expired_coordinates_are_not_used_for_distance(client, app):
    now = datetime.now(timezone.utc)
    with Session(app.state.engine) as db:
        cafe = db.exec(select(Cafe).where(Cafe.owner_id.is_not(None))).first()
        cafe.place_id = "expired-place"
        cafe.latitude = -34.6038
        cafe.longitude = -58.3817
        cafe.location_expires_at = now - timedelta(seconds=1)
        cafe.location_status = "VERIFIED"
        db.add(cafe)
        db.commit()

    response = client.post(
        "/api/cafes/search",
        json={
            "origin": {"type": "current", "latitude": -34.6037, "longitude": -58.3816},
            "radius_km": 1,
        },
    )

    assert all(item["place_id"] != "expired-place" for item in response.json())


def test_home_origin_rejects_client_coordinates_and_missing_home(client):
    injected = client.post(
        "/api/cafes/search",
        json={"origin": {"type": "home", "latitude": -34.6, "longitude": -58.4}},
    )
    missing = client.post("/api/cafes/search", json={"origin": {"type": "home"}})

    assert injected.status_code == 422
    assert missing.status_code == 409
