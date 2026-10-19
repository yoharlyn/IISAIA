import asyncio

import httpx
import pytest

from backend.google_places import (
    DETAILS_FIELD_MASK,
    NEARBY_FIELD_MASK,
    Coordinates,
    GooglePlacesProvider,
    PlacesInvalidResponse,
    PlacesQuotaExceeded,
    PlacesUnavailable,
)


def run(awaitable):
    return asyncio.run(awaitable)


def test_details_uses_minimal_field_mask_and_parses_required_fields():
    def handler(request: httpx.Request):
        assert request.method == "GET"
        assert request.url.raw_path == b"/v1/places/place%2Fid"
        assert request.headers["X-Goog-FieldMask"] == DETAILS_FIELD_MASK
        return httpx.Response(
            200,
            json={
                "id": "place/id",
                "displayName": {"text": "Café de prueba"},
                "formattedAddress": "Av. Corrientes 1000, CABA",
                "addressComponents": [
                    {
                        "longText": "Ciudad Autónoma de Buenos Aires",
                        "shortText": "CABA",
                        "types": ["administrative_area_level_1"],
                    }
                ],
                "location": {"latitude": -34.6037, "longitude": -58.3816},
            },
        )

    provider = GooglePlacesProvider("fake-key", transport=httpx.MockTransport(handler))
    result = run(provider.details("place/id"))

    assert result.place_id == "place/id"
    assert result.display_name == "Café de prueba"
    assert result.location == Coordinates(-34.6037, -58.3816)
    assert result.address_components[0].short_text == "CABA"


def test_nearby_caps_results_and_uses_declared_field_mask():
    def handler(request: httpx.Request):
        assert request.headers["X-Goog-FieldMask"] == NEARBY_FIELD_MASK
        body = __import__("json").loads(request.content)
        assert body["maxResultCount"] == 20
        assert body["locationRestriction"]["circle"]["radius"] == 2500
        return httpx.Response(
            200,
            json={
                "places": [
                    {
                        "id": "candidate-1",
                        "displayName": {"text": "Café de prueba"},
                        "location": {"latitude": -34.6, "longitude": -58.4},
                        "rating": 4.5,
                        "userRatingCount": 120,
                    }
                ]
            },
        )

    provider = GooglePlacesProvider("fake-key", transport=httpx.MockTransport(handler))
    results = run(
        provider.nearby(
            origin=Coordinates(-34.6, -58.4), radius_meters=2500, max_results=99
        )
    )

    assert results[0].display_name == "Café de prueba"
    assert results[0].rating == 4.5


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [(429, PlacesQuotaExceeded), (500, PlacesUnavailable)],
)
def test_places_maps_quota_and_service_errors(status_code, error_type):
    provider = GooglePlacesProvider(
        "fake-key",
        transport=httpx.MockTransport(lambda _request: httpx.Response(status_code)),
    )

    with pytest.raises(error_type):
        run(provider.details("place-id"))


def test_places_rejects_incomplete_responses():
    provider = GooglePlacesProvider(
        "fake-key",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, json={"id": "missing-location"})
        ),
    )

    with pytest.raises(PlacesInvalidResponse):
        run(provider.details("place-id"))


def test_places_timeout_is_safe_and_does_not_retry():
    calls = 0

    def handler(request: httpx.Request):
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("timeout", request=request)

    provider = GooglePlacesProvider("fake-key", transport=httpx.MockTransport(handler))

    with pytest.raises(PlacesUnavailable):
        run(provider.details("place-id"))
    assert calls == 1


def test_missing_key_blocks_network_before_request():
    calls = 0

    def handler(_request: httpx.Request):
        nonlocal calls
        calls += 1
        return httpx.Response(200)

    provider = GooglePlacesProvider("", transport=httpx.MockTransport(handler))

    with pytest.raises(PlacesUnavailable):
        run(provider.details("place-id"))
    assert calls == 0
