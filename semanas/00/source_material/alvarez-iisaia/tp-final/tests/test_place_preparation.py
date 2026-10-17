from dataclasses import replace

from sqlmodel import Session, select

from backend.google_places import Coordinates, PlacesInvalidResponse, PlacesUnavailable
from backend.models import Cafe, User
from conftest import TEST_ADDRESS


def cafe_payload(**overrides):
    payload = {
        "name": "Nombre enviado por el navegador",
        "neighborhood": "Palermo",
        "description": "La descripción continúa siendo obligatoria en V3.3.",
        "place_id": "place-new",
        "selected_address": "Dirección manipulada",
    }
    payload.update(overrides)
    return payload


def test_prepare_returns_canonical_details_without_persisting(client, app):
    with Session(app.state.engine) as db:
        before = len(db.exec(select(Cafe)).all())

    response = client.post("/api/places/place-new/prepare-cafe")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "place_id": "place-new",
        "display_name": "Lumbre Café",
        "formatted_address": TEST_ADDRESS,
        "neighborhood": "San Nicolás",
        "attribution": "Google Maps",
        "already_saved": False,
        "existing_cafe_id": None,
    }
    with Session(app.state.engine) as db:
        assert len(db.exec(select(Cafe)).all()) == before


def test_prepare_requires_origin_and_csrf(client):
    csrf = client.headers["X-CSRF-Token"]

    wrong_origin = client.post(
        "/api/places/place-new/prepare-cafe",
        headers={"Origin": "https://attacker.invalid", "X-CSRF-Token": csrf},
    )
    wrong_csrf = client.post(
        "/api/places/place-new/prepare-cafe",
        headers={"Origin": "http://127.0.0.1:8000", "X-CSRF-Token": "incorrecto"},
    )

    assert wrong_origin.status_code == 403
    assert wrong_csrf.status_code == 403


def test_prepare_rejects_mismatched_id_and_outside_caba(client, app):
    original = app.state.places_provider.details

    async def mismatched(_place_id):
        return replace(await original("different"), place_id="different")

    app.state.places_provider.details = mismatched
    mismatch = client.post("/api/places/requested/prepare-cafe")
    assert mismatch.status_code == 422
    assert mismatch.json()["detail"] == "El Place ID no coincide."

    async def outside(place_id):
        return replace(
            await original(place_id),
            location=Coordinates(-34.9215, -57.9545),
        )

    app.state.places_provider.details = outside
    response = client.post("/api/places/outside/prepare-cafe")
    assert response.status_code == 422
    assert "dentro de CABA" in response.json()["detail"]


def test_prepare_maps_provider_failures_to_safe_responses(client, app):
    async def unavailable(_place_id):
        raise PlacesUnavailable("secreto-del-proveedor")

    app.state.places_provider.details = unavailable
    down = client.post("/api/places/down/prepare-cafe")
    assert down.status_code == 503
    assert "secreto-del-proveedor" not in down.text

    async def invalid(_place_id):
        raise PlacesInvalidResponse("payload-privado")

    app.state.places_provider.details = invalid
    malformed = client.post("/api/places/invalid/prepare-cafe")
    assert malformed.status_code == 502
    assert "payload-privado" not in malformed.text

    async def malformed_object(_place_id):
        return object()

    app.state.places_provider.details = malformed_object
    wrong_shape = client.post("/api/places/wrong-shape/prepare-cafe")
    assert wrong_shape.status_code == 502
    assert wrong_shape.json()["detail"] == "Google Places devolvió una respuesta inválida."


def test_prepare_reports_only_the_authenticated_users_duplicate(client, app):
    created = client.post(
        "/api/cafes", json=cafe_payload(place_id="own-place")
    ).json()
    own = client.post("/api/places/own-place/prepare-cafe")

    with Session(app.state.engine) as db:
        other = User(
            auth0_sub="auth0|other-preparation",
            display_name="Otra identidad",
            identity_status="ACTIVE",
        )
        db.add(other)
        db.commit()
        db.refresh(other)
        db.add(
            Cafe(
                owner_id=other.id,
                name="Privada de otra persona",
                neighborhood="San Nicolás",
                description="No debe filtrarse su existencia.",
                place_id="other-place",
                selected_address=TEST_ADDRESS,
            )
        )
        db.commit()

    other_user_place = client.post("/api/places/other-place/prepare-cafe")

    assert own.json()["already_saved"] is True
    assert own.json()["existing_cafe_id"] == created["id"]
    assert other_user_place.json()["already_saved"] is False
    assert other_user_place.json()["existing_cafe_id"] is None


def test_create_revalidates_and_ignores_manipulated_canonical_fields(client):
    response = client.post("/api/cafes", json=cafe_payload())

    assert response.status_code == 201
    cafe = response.json()
    assert cafe["name"] == "Lumbre Café"
    assert cafe["selected_address"] == TEST_ADDRESS
    assert cafe["neighborhood"] == "San Nicolás"
    assert cafe["latitude"] == -34.6037
    assert cafe["longitude"] == -58.3816

    coordinates = client.post(
        "/api/cafes",
        json=cafe_payload(place_id="coordinates", latitude=0, longitude=0),
    )
    assert coordinates.status_code == 422


def test_update_with_a_new_place_uses_the_revalidated_canonical_name(client):
    cafe_id = client.get("/api/cafes").json()[0]["id"]

    response = client.patch(
        f"/api/cafes/{cafe_id}",
        json={
            "name": "Nombre manipulado",
            "place_id": "updated-place",
            "selected_address": "Dirección manipulada",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Lumbre Café"
    assert response.json()["selected_address"] == TEST_ADDRESS
