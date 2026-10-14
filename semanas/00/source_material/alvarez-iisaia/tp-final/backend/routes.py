from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlmodel import Session, func, select

from backend.db import get_session
from backend.models import Cafe, VisitStatus, utc_now
from backend.schemas import CafeCreate, CafeRead, CafeUpdate, StatsRead

router = APIRouter(prefix="/api")
SessionDep = Annotated[Session, Depends(get_session)]
CafeId = Annotated[int, Path(gt=0)]


def find_cafe(session: Session, cafe_id: int) -> Cafe:
    cafe = session.get(Cafe, cafe_id)
    if cafe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cafetería no encontrada.",
        )
    return cafe


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("/cafes", response_model=list[CafeRead])
def list_cafes(
    session: SessionDep,
    q: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    neighborhood: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
    visit_status: VisitStatus | None = None,
    is_favorite: bool | None = None,
):
    statement = select(Cafe)
    if q is not None:
        normalized_q = q.strip()
        if not normalized_q:
            raise HTTPException(status_code=422, detail="La búsqueda no puede estar vacía.")
        pattern = f"%{escape_like(normalized_q.lower())}%"
        statement = statement.where(func.lower(Cafe.name).like(pattern, escape="\\"))
    if neighborhood is not None:
        normalized_neighborhood = neighborhood.strip()
        if not normalized_neighborhood:
            raise HTTPException(status_code=422, detail="El barrio no puede estar vacío.")
        statement = statement.where(
            func.lower(Cafe.neighborhood) == normalized_neighborhood.lower()
        )
    if visit_status is not None:
        statement = statement.where(Cafe.visit_status == visit_status)
    if is_favorite is not None:
        statement = statement.where(Cafe.is_favorite == is_favorite)
    statement = statement.order_by(Cafe.updated_at.desc(), Cafe.id.desc())
    return session.exec(statement).all()


@router.post("/cafes", response_model=CafeRead, status_code=status.HTTP_201_CREATED)
def create_cafe(payload: CafeCreate, session: SessionDep):
    cafe = Cafe(**payload.model_dump())
    session.add(cafe)
    session.commit()
    session.refresh(cafe)
    return cafe


@router.get("/cafes/{cafe_id}", response_model=CafeRead)
def get_cafe(cafe_id: CafeId, session: SessionDep):
    return find_cafe(session, cafe_id)


@router.patch("/cafes/{cafe_id}", response_model=CafeRead)
def update_cafe(cafe_id: CafeId, payload: CafeUpdate, session: SessionDep):
    cafe = find_cafe(session, cafe_id)
    cafe.sqlmodel_update(payload.model_dump(exclude_unset=True))
    cafe.updated_at = utc_now()
    session.add(cafe)
    session.commit()
    session.refresh(cafe)
    return cafe


@router.delete("/cafes/{cafe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cafe(cafe_id: CafeId, session: SessionDep):
    cafe = find_cafe(session, cafe_id)
    session.delete(cafe)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/stats", response_model=StatsRead)
def get_stats(session: SessionDep):
    total = session.exec(select(func.count()).select_from(Cafe)).one()
    visited = session.exec(
        select(func.count()).select_from(Cafe).where(Cafe.visit_status == VisitStatus.VISITED)
    ).one()
    pending = session.exec(
        select(func.count()).select_from(Cafe).where(Cafe.visit_status == VisitStatus.PENDING)
    ).one()
    favorites = session.exec(
        select(func.count()).select_from(Cafe).where(Cafe.is_favorite.is_(True))
    ).one()
    return StatsRead(
        total=total,
        visited=visited,
        pending=pending,
        favorites=favorites,
    )
