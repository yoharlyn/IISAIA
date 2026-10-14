from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from backend.auth_routes import AuthContext, require_auth, require_csrf
from backend.db import get_session
from backend.models import Cafe, Visit, VisitStatus, utc_now
from backend.schemas import CafeCreate, CafeRead, CafeUpdate, StatsRead
from backend.locations import location_values, places_provider, verify_place_selection

router = APIRouter(prefix="/api")
SessionDep = Annotated[Session, Depends(get_session)]
AuthDep = Annotated[AuthContext, Depends(require_auth)]
CsrfDep = Annotated[AuthContext, Depends(require_csrf)]
CafeId = Annotated[int, Path(gt=0)]
RATING_FIELDS = ("coffee_rating", "food_rating", "ambience_rating", "service_rating")


def find_cafe(session: Session, cafe_id: int, owner_id: int) -> Cafe:
    cafe = session.exec(
        select(Cafe).where(Cafe.id == cafe_id, Cafe.owner_id == owner_id)
    ).first()
    if cafe is None:
        raise HTTPException(status_code=404, detail="Cafetería no encontrada.")
    return cafe


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def latest_visit(session: Session, cafe: Cafe) -> Visit | None:
    return session.exec(
        select(Visit)
        .where(Visit.cafe_id == cafe.id, Visit.owner_id == cafe.owner_id)
        .order_by(Visit.visited_at.desc(), Visit.id.desc())
    ).first()


def serialize_cafe(session: Session, cafe: Cafe) -> CafeRead:
    visit = latest_visit(session, cafe)
    return CafeRead(
        id=cafe.id,
        name=cafe.name,
        neighborhood=cafe.neighborhood,
        place_id=cafe.place_id,
        selected_address=cafe.selected_address,
        latitude=cafe.latitude,
        longitude=cafe.longitude,
        location_status=cafe.location_status,
        location_expires_at=cafe.location_expires_at,
        description=cafe.description,
        image_url=cafe.image_url,
        visit_status=VisitStatus.VISITED if visit else VisitStatus.PENDING,
        is_favorite=cafe.is_favorite,
        coffee_rating=visit.coffee_rating if visit else None,
        food_rating=visit.food_rating if visit else None,
        ambience_rating=visit.ambience_rating if visit else None,
        service_rating=visit.service_rating if visit else None,
        created_at=cafe.created_at,
        updated_at=cafe.updated_at,
    )


@router.get("/cafes", response_model=list[CafeRead])
def list_cafes(
    session: SessionDep,
    auth: AuthDep,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    neighborhood: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
    visit_status: VisitStatus | None = None,
    is_favorite: bool | None = None,
):
    statement = select(Cafe).where(Cafe.owner_id == auth.user.id)
    if q is not None:
        normalized_q = q.strip()
        if not normalized_q:
            raise HTTPException(status_code=422, detail="La búsqueda no puede estar vacía.")
        statement = statement.where(
            func.lower(Cafe.name).like(
                f"%{escape_like(normalized_q.lower())}%", escape="\\"
            )
        )
    if neighborhood is not None:
        normalized = neighborhood.strip()
        if not normalized:
            raise HTTPException(status_code=422, detail="El barrio no puede estar vacío.")
        statement = statement.where(func.lower(Cafe.neighborhood) == normalized.lower())
    if is_favorite is not None:
        statement = statement.where(Cafe.is_favorite == is_favorite)
    cafes = session.exec(statement.order_by(Cafe.updated_at.desc(), Cafe.id.desc())).all()
    result = [serialize_cafe(session, cafe) for cafe in cafes]
    if visit_status is not None:
        result = [item for item in result if item.visit_status == visit_status]
    return result


@router.post("/cafes", response_model=CafeRead, status_code=status.HTTP_201_CREATED)
async def create_cafe(
    payload: CafeCreate, request: Request, session: SessionDep, auth: CsrfDep
):
    verified = await verify_place_selection(
        places_provider(request),
        place_id=payload.place_id,
        selected_address=payload.selected_address,
    )
    values = payload.model_dump(
        exclude=set(RATING_FIELDS)
        | {"visit_status", "neighborhood", "place_id", "selected_address"}
    )
    values.update(location_values(verified))
    values["location_status"] = "VERIFIED"
    cafe = Cafe(owner_id=auth.user.id, **values)
    try:
        session.add(cafe)
        session.flush()
        ratings = {field: getattr(payload, field) for field in RATING_FIELDS}
        if payload.visit_status == VisitStatus.VISITED or any(
            value is not None for value in ratings.values()
        ):
            session.add(Visit(owner_id=auth.user.id, cafe_id=cafe.id, **ratings))
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Esa cafetería ya está en tu atlas."
        ) from None
    session.refresh(cafe)
    return serialize_cafe(session, cafe)


@router.get("/cafes/{cafe_id}", response_model=CafeRead)
def get_cafe(cafe_id: CafeId, session: SessionDep, auth: AuthDep):
    return serialize_cafe(session, find_cafe(session, cafe_id, auth.user.id))


@router.patch("/cafes/{cafe_id}", response_model=CafeRead)
async def update_cafe(
    cafe_id: CafeId,
    payload: CafeUpdate,
    request: Request,
    session: SessionDep,
    auth: CsrfDep,
):
    cafe = find_cafe(session, cafe_id, auth.user.id)
    supplied = payload.model_dump(exclude_unset=True)
    location_supplied = "place_id" in supplied
    if location_supplied:
        verified = await verify_place_selection(
            places_provider(request),
            place_id=supplied.pop("place_id"),
            selected_address=supplied.pop("selected_address"),
        )
        cafe.sqlmodel_update(location_values(verified))
        cafe.location_status = "VERIFIED"
    cafe.sqlmodel_update(
        {
            key: value
            for key, value in supplied.items()
            if key not in RATING_FIELDS and key not in {"visit_status", "neighborhood"}
        }
    )
    visit = latest_visit(session, cafe)
    requested_status = supplied.get("visit_status")
    ratings_supplied = any(field in supplied for field in RATING_FIELDS)
    if requested_status == VisitStatus.PENDING:
        for row in session.exec(select(Visit).where(Visit.cafe_id == cafe.id)).all():
            session.delete(row)
        visit = None
    elif requested_status == VisitStatus.VISITED or ratings_supplied:
        if visit is None:
            visit = Visit(owner_id=auth.user.id, cafe_id=cafe.id)
        for field in RATING_FIELDS:
            if field in supplied:
                setattr(visit, field, supplied[field])
        visit.updated_at = utc_now()
        session.add(visit)
    cafe.updated_at = utc_now()
    session.add(cafe)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Esa cafetería ya está en tu atlas."
        ) from None
    session.refresh(cafe)
    return serialize_cafe(session, cafe)


@router.delete("/cafes/{cafe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cafe(cafe_id: CafeId, session: SessionDep, auth: CsrfDep):
    cafe = find_cafe(session, cafe_id, auth.user.id)
    for visit in session.exec(select(Visit).where(Visit.cafe_id == cafe.id)).all():
        session.delete(visit)
    session.delete(cafe)
    session.commit()
    return Response(status_code=204)


@router.get("/stats", response_model=StatsRead)
def get_stats(session: SessionDep, auth: AuthDep):
    cafes = session.exec(select(Cafe).where(Cafe.owner_id == auth.user.id)).all()
    visited_ids = set(
        session.exec(select(Visit.cafe_id).where(Visit.owner_id == auth.user.id)).all()
    )
    return StatsRead(
        total=len(cafes),
        visited=sum(cafe.id in visited_ids for cafe in cafes),
        pending=sum(cafe.id not in visited_ids for cafe in cafes),
        favorites=sum(cafe.is_favorite for cafe in cafes),
    )
