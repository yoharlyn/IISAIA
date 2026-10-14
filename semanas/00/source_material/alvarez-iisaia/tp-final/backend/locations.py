from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from backend.geo import CABA_POLYGON_VERSION, location_expiry, validate_caba_location
from backend.google_places import PlaceDetails, PlacesError, PlacesProvider
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


def _comparable_address(value: str) -> str:
    return " ".join(value.casefold().split()).rstrip(".")


async def verify_place_selection(
    provider: PlacesProvider, *, place_id: str, selected_address: str
) -> VerifiedLocation:
    try:
        details = await provider.details(place_id)
    except PlacesError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Places no está disponible en este momento.",
        ) from None
    if details.place_id != place_id:
        raise HTTPException(status_code=422, detail="El Place ID no coincide.")
    if _comparable_address(details.formatted_address) != _comparable_address(
        selected_address
    ):
        raise HTTPException(
            status_code=422,
            detail="La dirección seleccionada no coincide con Place Details.",
        )
    try:
        neighborhood = validate_caba_location(
            details.location, details.address_components
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    fetched_at = utc_now()
    return VerifiedLocation(
        details=details,
        selected_address=selected_address,
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
