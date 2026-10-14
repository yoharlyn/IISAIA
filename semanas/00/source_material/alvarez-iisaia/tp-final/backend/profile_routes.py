from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from backend.auth_routes import AuthContext, require_auth, require_csrf
from backend.db import get_session
from backend.geo import CABA_POLYGON_VERSION
from backend.locations import places_provider, verify_place_selection
from backend.models import utc_now
from backend.schemas import ProfileRead, ProfileUpdate


router = APIRouter(prefix="/api/profile")


def _read(user) -> ProfileRead:
    return ProfileRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        home_place_id=user.home_place_id,
        home_selected_address=user.home_selected_address,
        home_neighborhood=user.home_neighborhood,
        home_latitude=user.home_latitude,
        home_longitude=user.home_longitude,
        home_location_expires_at=user.home_location_expires_at,
    )


@router.get("", response_model=ProfileRead)
def get_profile(context: AuthContext = Depends(require_auth)):
    return _read(context.user)


@router.patch("", response_model=ProfileRead)
async def update_profile(
    payload: ProfileUpdate,
    request: Request,
    db: Session = Depends(get_session),
    context: AuthContext = Depends(require_csrf),
):
    user = context.user
    if "display_name" in payload.model_fields_set:
        user.display_name = payload.display_name
    if "home" in payload.model_fields_set:
        if payload.home is None:
            user.home_place_id = None
            user.home_selected_address = None
            user.home_latitude = None
            user.home_longitude = None
            user.home_location_fetched_at = None
            user.home_location_expires_at = None
            user.home_neighborhood = None
            user.home_caba_verified_at = None
            user.home_caba_polygon_version = None
        else:
            verified = await verify_place_selection(
                places_provider(request),
                place_id=payload.home.place_id,
                selected_address=payload.home.selected_address,
            )
            user.home_place_id = verified.details.place_id
            user.home_selected_address = verified.selected_address
            user.home_latitude = verified.details.location.latitude
            user.home_longitude = verified.details.location.longitude
            user.home_location_fetched_at = verified.fetched_at
            user.home_location_expires_at = verified.expires_at
            user.home_neighborhood = verified.neighborhood
            user.home_caba_verified_at = verified.fetched_at
            user.home_caba_polygon_version = CABA_POLYGON_VERSION
    user.updated_at = utc_now()
    db.add(user)
    db.commit()
    db.refresh(user)
    return _read(user)
