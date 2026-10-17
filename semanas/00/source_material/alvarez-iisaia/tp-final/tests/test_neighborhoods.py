import json
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.models import Cafe
from backend.neighborhoods import (
    EXPECTED_NEIGHBORHOOD_COUNT,
    NEIGHBORHOODS_PATH,
    canonical_neighborhood,
    official_neighborhoods,
    spanish_sort_key,
)


def _login(client: TestClient, code: str):
    start = client.get("/auth/login", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": code, "state": state},
        follow_redirects=False,
    )


def test_official_catalog_matches_every_geojson_feature():
    payload = json.loads(NEIGHBORHOODS_PATH.read_text(encoding="utf-8"))
    raw_names = [feature["properties"]["BARRIO"] for feature in payload["features"]]
    catalog = official_neighborhoods()

    assert len(raw_names) == EXPECTED_NEIGHBORHOOD_COUNT == 48
    assert len(set(raw_names)) == 48
    assert len(catalog) == len(set(catalog)) == 48
    assert list(catalog) == sorted(catalog, key=spanish_sort_key)
    assert "Villa del Parque" in catalog
    assert {
        "Agronomía",
        "Constitución",
        "Núñez",
        "San Nicolás",
        "Vélez Sarsfield",
    } <= set(catalog)
    assert {canonical_neighborhood(name) for name in raw_names} == set(catalog)
    assert all(
        feature["properties"]["OBJETO"] == "BARRIO"
        for feature in payload["features"]
    )
    assert all(
        feature["geometry"]["type"] == "MultiPolygon"
        for feature in payload["features"]
    )


def test_safe_aliases_handle_case_accents_spaces_and_punctuation():
    assert canonical_neighborhood("san nicolas") == "San Nicolás"
    assert canonical_neighborhood("SAN NICOLÁS") == "San Nicolás"
    assert canonical_neighborhood("  Núñez  ") == "Núñez"
    assert canonical_neighborhood("Villa Gral Mitre") == "Villa Gral. Mitre"
    assert canonical_neighborhood("villa pueyrredon") == "Villa Pueyrredón"
    assert canonical_neighborhood("Centro") is None


def test_catalog_separates_historical_values_by_owner(client, app):
    owner_id = client.get("/api/session").json()["user"]["id"]
    with TestClient(app, base_url="http://127.0.0.1:8000") as second:
        _login(second, "second")
        second_id = second.get("/api/session").json()["user"]["id"]
        with Session(app.state.engine) as session:
            session.add(
                Cafe(
                    owner_id=owner_id,
                    name="Histórica",
                    neighborhood="Centro",
                    description="Valor anterior.",
                )
            )
            session.add(
                Cafe(
                    owner_id=owner_id,
                    name="Alias",
                    neighborhood="San Nicolas",
                    description="Alias seguro.",
                )
            )
            session.add(
                Cafe(
                    owner_id=second_id,
                    name="Ajena",
                    neighborhood="Microcentro",
                    description="Valor ajeno.",
                )
            )
            session.commit()

        owner_catalog = client.get("/api/neighborhoods")
        second_catalog = second.get("/api/neighborhoods")

    assert owner_catalog.status_code == 200
    assert len(owner_catalog.json()["official"]) == 48
    assert owner_catalog.json()["historical"] == ["Centro"]
    assert second_catalog.json()["historical"] == ["Microcentro"]


def test_official_aliases_and_historical_values_remain_filterable(client, app):
    owner_id = client.get("/api/session").json()["user"]["id"]
    with Session(app.state.engine) as session:
        session.add(
            Cafe(
                owner_id=owner_id,
                name="Con alias",
                neighborhood="San Nicolas",
                description="Alias seguro.",
            )
        )
        session.add(
            Cafe(
                owner_id=owner_id,
                name="Histórica",
                neighborhood="Centro",
                description="Valor anterior.",
            )
        )
        session.commit()

    official = client.get("/api/cafes", params={"neighborhood": "San Nicolás"})
    historical = client.get("/api/cafes", params={"neighborhood": "Centro"})

    assert official.status_code == historical.status_code == 200
    assert [item["name"] for item in official.json()] == ["Con alias"]
    assert official.json()[0]["neighborhood"] == "San Nicolás"
    assert [item["name"] for item in historical.json()] == ["Histórica"]
    assert [
        item["name"]
        for item in client.post(
            "/api/cafes/search", json={"neighborhood": "SAN NICOLAS"}
        ).json()
    ] == ["Con alias"]
    assert [
        item["name"]
        for item in client.post(
            "/api/cafes/search", json={"neighborhood": "Centro"}
        ).json()
    ] == ["Histórica"]


def test_catalog_requires_authentication(app):
    with TestClient(app, base_url="http://127.0.0.1:8000") as anonymous:
        assert anonymous.get("/api/neighborhoods").status_code == 401
