from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, Response
from sqlmodel import Session

from backend.auth_routes import AuthContext, require_csrf
from backend.db import get_session
from backend.locations import places_provider
from backend.place_preparation import prepare_cafe
from backend.schemas import PreparedCafeRead


router = APIRouter(prefix="/api/places")
PlaceId = Annotated[str, Path(min_length=1, max_length=255)]


@router.post("/{place_id}/prepare-cafe", response_model=PreparedCafeRead)
async def prepare_place_for_cafe(
    place_id: PlaceId,
    request: Request,
    response: Response,
    db: Session = Depends(get_session),
    context: AuthContext = Depends(require_csrf),
):
    response.headers["Cache-Control"] = "no-store"
    return await prepare_cafe(
        places_provider(request),
        db,
        owner_id=context.user.id,
        place_id=place_id,
    )
