from dataclasses import dataclass
from datetime import date
from typing import Protocol
from urllib.parse import quote

import httpx


PLACES_BASE_URL = "https://places.googleapis.com/v1"
DETAILS_FIELD_MASK = "id,formattedAddress,addressComponents,location"
NEARBY_FIELD_MASK = ",".join(
    (
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.addressComponents",
        "places.location",
        "places.primaryType",
        "places.businessStatus",
        "places.rating",
        "places.userRatingCount",
        "places.openingDate",
        "places.googleMapsUri",
    )
)


class PlacesError(RuntimeError):
    """Error seguro de la integración Places, sin contenido de la respuesta."""


class PlacesUnavailable(PlacesError):
    pass


class PlacesQuotaExceeded(PlacesError):
    pass


class PlacesInvalidResponse(PlacesError):
    pass


@dataclass(frozen=True, slots=True)
class Coordinates:
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class AddressComponent:
    long_text: str
    short_text: str
    types: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlaceDetails:
    place_id: str
    formatted_address: str
    address_components: tuple[AddressComponent, ...]
    location: Coordinates


@dataclass(frozen=True, slots=True)
class PlaceCandidate:
    place_id: str
    display_name: str | None
    formatted_address: str | None
    address_components: tuple[AddressComponent, ...]
    location: Coordinates
    primary_type: str | None = None
    business_status: str | None = None
    rating: float | None = None
    user_rating_count: int | None = None
    opening_date: date | None = None
    google_maps_uri: str | None = None


class PlacesProvider(Protocol):
    async def details(self, place_id: str) -> PlaceDetails: ...

    async def nearby(
        self, *, origin: Coordinates, radius_meters: float, max_results: int = 20
    ) -> list[PlaceCandidate]: ...


def _coordinates(payload: object) -> Coordinates:
    if not isinstance(payload, dict):
        raise PlacesInvalidResponse("location")
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        raise PlacesInvalidResponse("location")
    return Coordinates(float(latitude), float(longitude))


def _components(payload: object) -> tuple[AddressComponent, ...]:
    if not isinstance(payload, list):
        return ()
    result = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        types = item.get("types")
        result.append(
            AddressComponent(
                long_text=str(item.get("longText") or ""),
                short_text=str(item.get("shortText") or ""),
                types=tuple(str(value) for value in types) if isinstance(types, list) else (),
            )
        )
    return tuple(result)


def _opening_date(payload: object) -> date | None:
    if not isinstance(payload, dict):
        return None
    try:
        return date(int(payload["year"]), int(payload["month"]), int(payload["day"]))
    except (KeyError, TypeError, ValueError):
        return None


class GooglePlacesProvider:
    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = 8.0,
    ):
        self.api_key = api_key
        self.transport = transport
        self.timeout_seconds = timeout_seconds

    def _headers(self, field_mask: str) -> dict[str, str]:
        if not self.api_key:
            raise PlacesUnavailable("not_configured")
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": field_mask,
        }

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = await client.request(method, url, **kwargs)
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise PlacesUnavailable("network") from error
        if response.status_code == 429:
            raise PlacesQuotaExceeded("quota")
        try:
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise PlacesUnavailable("response") from error
        if not isinstance(payload, dict):
            raise PlacesInvalidResponse("payload")
        return payload

    async def details(self, place_id: str) -> PlaceDetails:
        normalized = place_id.strip()
        if not normalized:
            raise PlacesInvalidResponse("place_id")
        payload = await self._request(
            "GET",
            f"{PLACES_BASE_URL}/places/{quote(normalized, safe='')}",
            headers=self._headers(DETAILS_FIELD_MASK),
        )
        returned_id = payload.get("id")
        formatted_address = payload.get("formattedAddress")
        if not isinstance(returned_id, str) or not isinstance(formatted_address, str):
            raise PlacesInvalidResponse("details")
        return PlaceDetails(
            place_id=returned_id,
            formatted_address=formatted_address,
            address_components=_components(payload.get("addressComponents")),
            location=_coordinates(payload.get("location")),
        )

    async def nearby(
        self, *, origin: Coordinates, radius_meters: float, max_results: int = 20
    ) -> list[PlaceCandidate]:
        payload = await self._request(
            "POST",
            f"{PLACES_BASE_URL}/places:searchNearby",
            headers=self._headers(NEARBY_FIELD_MASK),
            json={
                "includedTypes": ["cafe"],
                "maxResultCount": max(1, min(max_results, 20)),
                "locationRestriction": {
                    "circle": {
                        "center": {
                            "latitude": origin.latitude,
                            "longitude": origin.longitude,
                        },
                        "radius": radius_meters,
                    }
                },
            },
        )
        places = payload.get("places", [])
        if not isinstance(places, list):
            raise PlacesInvalidResponse("places")
        result = []
        for item in places:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise PlacesInvalidResponse("candidate")
            display_name = item.get("displayName")
            result.append(
                PlaceCandidate(
                    place_id=item["id"],
                    display_name=(
                        display_name.get("text")
                        if isinstance(display_name, dict)
                        and isinstance(display_name.get("text"), str)
                        else None
                    ),
                    formatted_address=item.get("formattedAddress"),
                    address_components=_components(item.get("addressComponents")),
                    location=_coordinates(item.get("location")),
                    primary_type=item.get("primaryType"),
                    business_status=item.get("businessStatus"),
                    rating=float(item["rating"]) if isinstance(item.get("rating"), (int, float)) else None,
                    user_rating_count=(
                        item["userRatingCount"]
                        if isinstance(item.get("userRatingCount"), int)
                        else None
                    ),
                    opening_date=_opening_date(item.get("openingDate")),
                    google_maps_uri=item.get("googleMapsUri"),
                )
            )
        return result
