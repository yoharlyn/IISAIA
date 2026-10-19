from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from backend.geo import CABA_POLYGON_VERSION, location_expiry, validate_caba_location
from backend.google_places import (
    Coordinates,
    PlaceDetails,
    PlacesError,
    PlacesInvalidResponse,
    PlacesProvider,
)
from backend.models import utc_now


@dataclass(frozen=True, slots=True)
class VerifiedLocation:
    details: PlaceDetails
    selected_address: str
    neighborhood: str
    fetched_at: object
    expires_at: object


def places_provider(request: Request) -> PlacesProvider:
    return request.app.state.places_provider


async def verify_place_selection(
    provider: PlacesProvider, *, place_id: str, selected_address: str
) -> VerifiedLocation:
    return await fetch_verified_location(provider, place_id=place_id)


async def fetch_verified_location(
    provider: PlacesProvider, *, place_id: str
) -> VerifiedLocation:
    try:
        details = await provider.details(place_id)
    except PlacesInvalidResponse:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google Places devolvió una respuesta inválida.",
        ) from None
    except PlacesError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Places no está disponible en este momento.",
        ) from None
    if not isinstance(details, PlaceDetails):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google Places devolvió una respuesta inválida.",
        )
    if details.place_id != place_id:
        raise HTTPException(status_code=422, detail="El Place ID no coincide.")
    coordinates = details.location
    invalid_coordinates = (
        not isinstance(coordinates, Coordinates)
        or isinstance(coordinates.latitude, bool)
        or isinstance(coordinates.longitude, bool)
        or not isinstance(coordinates.latitude, (int, float))
        or not isinstance(coordinates.longitude, (int, float))
        or not -90 <= coordinates.latitude <= 90
        or not -180 <= coordinates.longitude <= 180
    )
    if (
        not isinstance(details.display_name, str)
        or not details.display_name.strip()
        or not isinstance(details.formatted_address, str)
        or not details.formatted_address.strip()
        or invalid_coordinates
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google Places devolvió una respuesta inválida.",
        )
    try:
        neighborhood = validate_caba_location(
            details.location, details.address_components
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    except (AttributeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google Places devolvió una respuesta inválida.",
        ) from None
    fetched_at = utc_now()
    return VerifiedLocation(
        details=details,
        selected_address=details.formatted_address,
        neighborhood=neighborhood,
        fetched_at=fetched_at,
        expires_at=location_expiry(fetched_at),
    )


def location_values(location: VerifiedLocation) -> dict:
    return {
        "place_id": location.details.place_id,
        "place_id_checked_at": location.fetched_at,
        "selected_address": location.selected_address,
        "latitude": location.details.location.latitude,
        "longitude": location.details.location.longitude,
        "location_fetched_at": location.fetched_at,
        "location_expires_at": location.expires_at,
        "neighborhood": location.neighborhood,
        "caba_verified_at": location.fetched_at,
        "caba_polygon_version": CABA_POLYGON_VERSION,
    }
