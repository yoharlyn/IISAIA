from sqlmodel import Session, select

from backend.models import Cafe, User
from conftest import TEST_ADDRESS


def test_profile_stores_user_selection_coordinates_ttl_and_derived_evidence(client, app):
    response = client.patch(
        "/api/profile",
        json={
            "display_name": "Dueña del atlas",
            "home": {"place_id": "home-place", "selected_address": TEST_ADDRESS},
        },
    )

    assert response.status_code == 200
    profile = response.json()
    assert profile["display_name"] == "Dueña del atlas"
    assert profile["home_place_id"] == "home-place"
    assert profile["home_selected_address"] == TEST_ADDRESS
    assert profile["home_neighborhood"] == "San Nicolas"
    assert profile["home_location_expires_at"]
    with Session(app.state.engine) as db:
        user = db.exec(select(User)).one()
        assert user.home_caba_polygon_version == "gcba-2026-07-29"
        assert user.home_location_fetched_at is not None


def test_free_text_without_place_selection_is_rejected(client):
    response = client.post(
        "/api/cafes",
        json={
            "name": "Texto libre",
            "neighborhood": "Palermo",
            "description": "No alcanza para crear una ubicación.",
        },
    )

    assert response.status_code == 422


def test_profile_accepts_an_address_variant_for_the_same_place_id(client):
    response = client.patch(
        "/api/profile",
        json={
            "home": {
                "place_id": "home-place",
                "selected_address": "Av Corrientes 1000",
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["home_place_id"] == "home-place"
    assert response.json()["home_selected_address"] == TEST_ADDRESS


def test_profile_never_persists_a_client_manipulated_address(client, app):
    manipulated = "Dirección manipulada por el cliente 999"

    response = client.patch(
        "/api/profile",
        json={
            "home": {
                "place_id": "home-place",
                "selected_address": manipulated,
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["home_selected_address"] == TEST_ADDRESS
    with Session(app.state.engine) as db:
        user = db.exec(select(User)).one()
        assert user.home_selected_address == TEST_ADDRESS
        assert user.home_selected_address != manipulated


def test_profile_still_rejects_a_mismatched_place_id(client, app):
    original_details = app.state.places_provider.details

    async def mismatched_details(_place_id):
        return await original_details("different-place")

    app.state.places_provider.details = mismatched_details
    response = client.patch(
        "/api/profile",
        json={
            "home": {
                "place_id": "home-place",
                "selected_address": "Av Corrientes 1000",
            }
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "El Place ID no coincide."
    with Session(app.state.engine) as db:
        user = db.exec(select(User)).one()
        assert user.home_place_id is None
        assert user.home_selected_address is None


def test_same_place_is_unique_per_owner_but_allowed_for_different_users(client, app):
    payload = {
        "name": "Primera",
        "description": "Ubicación verificada.",
        "place_id": "shared-place",
        "selected_address": TEST_ADDRESS,
    }
    first = client.post("/api/cafes", json=payload)
    duplicate = client.post("/api/cafes", json={**payload, "name": "Duplicada"})

    assert first.status_code == 201
    assert duplicate.status_code == 409
    with Session(app.state.engine) as db:
        first_user = db.exec(select(User)).first()
        second_user = User(
            auth0_sub="auth0|other", display_name="Otra", identity_status="ACTIVE"
        )
        db.add(second_user)
        db.commit()
        db.refresh(second_user)
        db.add(
            Cafe(
                owner_id=second_user.id,
                name="También válida",
                neighborhood="San Nicolas",
                description="El Place ID se puede repetir entre propietarios.",
                place_id="shared-place",
                selected_address=TEST_ADDRESS,
            )
        )
        db.commit()
        assert len(db.exec(select(Cafe).where(Cafe.place_id == "shared-place")).all()) == 2
        assert first_user.id != second_user.id


def test_raw_google_address_components_are_not_persisted(client, app):
    client.patch(
        "/api/profile",
        json={"home": {"place_id": "home-place", "selected_address": TEST_ADDRESS}},
    )
    with app.state.engine.connect() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(users)").fetchall()
        }
    assert "address_components" not in columns
