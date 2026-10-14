import json
from datetime import datetime, timedelta, timezone

import pytest

from backend.geo import (
    LOCATION_TTL,
    PERIMETER_PATH,
    components_indicate_caba,
    is_in_caba,
    location_expiry,
    location_is_fresh,
    neighborhood_for,
    validate_caba_location,
)
from backend.google_places import AddressComponent, Coordinates


CABA_COMPONENTS = (
    AddressComponent(
        long_text="Ciudad Autónoma de Buenos Aires",
        short_text="CABA",
        types=("administrative_area_level_1",),
    ),
)


def test_official_polygon_accepts_interior_boundary_and_rejects_exterior():
    interior = Coordinates(-34.6037, -58.3816)
    exterior = Coordinates(-34.9215, -57.9545)
    payload = json.loads(PERIMETER_PATH.read_text(encoding="utf-8"))
    first_point = payload["features"][0]["geometry"]["coordinates"][0][0]
    boundary = Coordinates(latitude=first_point[1], longitude=first_point[0])

    assert is_in_caba(interior)
    assert is_in_caba(boundary)
    assert not is_in_caba(exterior)


def test_neighborhood_is_derived_from_official_polygons():
    assert neighborhood_for(Coordinates(-34.6037, -58.3816)) == "San Nicolas"


def test_caba_requires_components_and_polygon():
    assert components_indicate_caba(CABA_COMPONENTS)
    assert validate_caba_location(
        Coordinates(-34.6037, -58.3816), CABA_COMPONENTS
    ) == "San Nicolas"

    with pytest.raises(ValueError, match="dentro de CABA"):
        validate_caba_location(Coordinates(-34.9215, -57.9545), CABA_COMPONENTS)
    with pytest.raises(ValueError, match="dentro de CABA"):
        validate_caba_location(Coordinates(-34.6037, -58.3816), ())


def test_coordinate_ttl_is_exactly_29_days_and_expired_values_are_rejected():
    fetched_at = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    expires_at = location_expiry(fetched_at)

    assert expires_at - fetched_at == LOCATION_TTL == timedelta(days=29)
    assert location_is_fresh(expires_at, now=expires_at - timedelta(microseconds=1))
    assert not location_is_fresh(expires_at, now=expires_at)
    assert not location_is_fresh(None, now=fetched_at)
