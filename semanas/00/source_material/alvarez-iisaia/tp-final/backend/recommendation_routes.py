from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from backend.auth_routes import AuthContext, require_csrf
from backend.db import get_session
from backend.geo import validate_caba_location, location_is_fresh
from backend.google_places import Coordinates, PlacesError
from backend.locations import location_values, places_provider, verify_place_selection
from backend.models import Cafe, PlaceDiscovery, Visit, utc_now
from backend.recommendations import (
    candidate_distance,
    novelty_for,
    personal_affinity_by_neighborhood,
    score_candidate,
)
from backend.schemas import RecommendationRead, RecommendationSave, RecommendationSearch


router = APIRouter(prefix="/api/recommendations")
_requests: dict[int, deque[datetime]] = defaultdict(deque)


def _rate_limit(user_id: int) -> None:
    now = datetime.now(timezone.utc)
    history = _requests[user_id]
    while history and history[0] < now - timedelta(minutes=1):
        history.popleft()
    if len(history) >= 10:
        raise HTTPException(status_code=429, detail="Esperá antes de pedir más recomendaciones.")
    history.append(now)


def _origin(payload: RecommendationSearch, context: AuthContext) -> Coordinates:
    if payload.origin.type == "current":
        return Coordinates(payload.origin.latitude, payload.origin.longitude)
    user = context.user
    if not location_is_fresh(user.home_location_expires_at):
        raise HTTPException(status_code=409, detail="El domicilio no tiene coordenadas vigentes.")
    return Coordinates(user.home_latitude, user.home_longitude)


@router.post("/search", response_model=list[RecommendationRead])
async def search_recommendations(
    payload: RecommendationSearch,
    request: Request,
    response: Response,
    db: Session = Depends(get_session),
    context: AuthContext = Depends(require_csrf),
):
    response.headers["Cache-Control"] = "no-store"
    _rate_limit(context.user.id)
    origin = _origin(payload, context)
    try:
        candidates = await places_provider(request).nearby(
            origin=origin, radius_meters=payload.radius_km * 1000, max_results=20
        )
    except PlacesError:
        raise HTTPException(
            status_code=503,
            detail="Google Places no está disponible en este momento.",
        ) from None

    cafes = db.exec(select(Cafe).where(Cafe.owner_id == context.user.id)).all()
    cafes_by_place = {cafe.place_id: cafe for cafe in cafes if cafe.place_id}
    visited_ids = set(
        db.exec(select(Visit.cafe_id).where(Visit.owner_id == context.user.id)).all()
    )
    affinities = personal_affinity_by_neighborhood(db, context.user.id)
    now = utc_now()
    result = []
    for candidate in candidates:
        if candidate.business_status == "CLOSED_PERMANENTLY":
            continue
        try:
            neighborhood = validate_caba_location(
                candidate.location, candidate.address_components
            )
        except ValueError:
            continue
        distance = candidate_distance(candidate, origin)
        if distance > payload.radius_km:
            continue
        novelty, novelty_label = novelty_for(candidate, cafes_by_place, visited_ids)
        affinity = affinities.get(neighborhood) if affinities else None
        score, factors = score_candidate(
            candidate,
            distance_km=distance,
            radius_km=payload.radius_km,
            novelty=novelty,
            affinity=affinity,
        )
        discovery = db.exec(
            select(PlaceDiscovery).where(
                PlaceDiscovery.owner_id == context.user.id,
                PlaceDiscovery.place_id == candidate.place_id,
            )
        ).first()
        if discovery is None:
            discovery = PlaceDiscovery(
                owner_id=context.user.id,
                place_id=candidate.place_id,
                first_seen_at=now,
                last_seen_at=now,
            )
        else:
            discovery.last_seen_at = now
        db.add(discovery)
        result.append(
            RecommendationRead(
                place_id=candidate.place_id,
                display_name=candidate.display_name,
                formatted_address=candidate.formatted_address,
                latitude=candidate.location.latitude,
                longitude=candidate.location.longitude,
                distance_km=distance,
                business_status=candidate.business_status,
                rating=candidate.rating,
                user_rating_count=candidate.user_rating_count,
                opening_date=(candidate.opening_date.isoformat() if candidate.opening_date else None),
                google_maps_uri=candidate.google_maps_uri,
                novelty_label=novelty_label,
                score=score,
                factors=factors,
            )
        )
    db.commit()
    result.sort(
        key=lambda item: (
            -item.score,
            item.distance_km,
            -(item.user_rating_count or 0),
            (item.display_name or "").casefold(),
        )
    )
    return result


@router.post("/{place_id}/prepare-save")
async def prepare_save(
    place_id: str,
    request: Request,
    _context: AuthContext = Depends(require_csrf),
):
    try:
        details = await places_provider(request).details(place_id)
    except PlacesError:
        raise HTTPException(status_code=503, detail="Google Places no está disponible.") from None
    try:
        neighborhood = validate_caba_location(details.location, details.address_components)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    return {
        "place_id": details.place_id,
        "formatted_address": details.formatted_address,
        "neighborhood": neighborhood,
        "attribution": "Google Maps",
    }


@router.post("/{place_id}/save", status_code=status.HTTP_201_CREATED)
async def save_recommendation(
    place_id: str,
    payload: RecommendationSave,
    request: Request,
    db: Session = Depends(get_session),
    context: AuthContext = Depends(require_csrf),
):
    verified = await verify_place_selection(
        places_provider(request),
        place_id=place_id,
        selected_address=payload.selected_address,
    )
    values = location_values(verified)
    values["location_status"] = "VERIFIED"
    cafe = Cafe(
        owner_id=context.user.id,
        name=payload.name,
        description=payload.description,
        is_favorite=payload.is_favorite,
        **values,
    )
    try:
        db.add(cafe)
        db.commit()
        db.refresh(cafe)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Esa cafetería ya está en tu atlas.") from None
    return {"id": cafe.id, "name": cafe.name, "place_id": cafe.place_id}
