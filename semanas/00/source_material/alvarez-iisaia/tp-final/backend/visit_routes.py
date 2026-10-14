from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path as ApiPath, Request, Response, status
from sqlmodel import Session, select

from backend.auth_routes import AuthContext, require_auth, require_csrf
from backend.db import get_session
from backend.models import Cafe, Visit, VisitPhoto, utc_now
from backend.schemas import VisitCreate, VisitPhotoRead, VisitRead, VisitUpdate
from backend.uploads import purge_quarantined, quarantine_photos, restore_quarantined


router = APIRouter(prefix="/api")
SessionDep = Annotated[Session, Depends(get_session)]
AuthDep = Annotated[AuthContext, Depends(require_auth)]
CsrfDep = Annotated[AuthContext, Depends(require_csrf)]
PositiveId = Annotated[int, ApiPath(gt=0)]


def _find_cafe(session: Session, cafe_id: int, owner_id: int) -> Cafe:
    cafe = session.exec(
        select(Cafe).where(Cafe.id == cafe_id, Cafe.owner_id == owner_id)
    ).first()
    if cafe is None:
        raise HTTPException(status_code=404, detail="Cafetería no encontrada.")
    return cafe


def _find_visit(session: Session, visit_id: int, owner_id: int) -> Visit:
    visit = session.exec(
        select(Visit).where(Visit.id == visit_id, Visit.owner_id == owner_id)
    ).first()
    if visit is None:
        raise HTTPException(status_code=404, detail="Visita no encontrada.")
    return visit


def _serialize_visit(session: Session, visit: Visit) -> VisitRead:
    photos = session.exec(
        select(VisitPhoto)
        .where(
            VisitPhoto.visit_id == visit.id,
            VisitPhoto.owner_id == visit.owner_id,
        )
        .order_by(VisitPhoto.created_at, VisitPhoto.id)
    ).all()
    return VisitRead(
        **visit.model_dump(),
        photos=[
            VisitPhotoRead(**photo.model_dump(), url=f"/api/photos/{photo.id}")
            for photo in photos
        ],
    )


@router.get("/cafes/{cafe_id}/visits", response_model=list[VisitRead])
def list_visits(cafe_id: PositiveId, session: SessionDep, auth: AuthDep):
    _find_cafe(session, cafe_id, auth.user.id)
    visits = session.exec(
        select(Visit)
        .where(Visit.cafe_id == cafe_id, Visit.owner_id == auth.user.id)
        .order_by(Visit.visited_at.desc(), Visit.id.desc())
    ).all()
    return [_serialize_visit(session, visit) for visit in visits]


@router.post(
    "/cafes/{cafe_id}/visits",
    response_model=VisitRead,
    status_code=status.HTTP_201_CREATED,
)
def create_visit(
    cafe_id: PositiveId,
    payload: VisitCreate,
    session: SessionDep,
    auth: CsrfDep,
):
    cafe = _find_cafe(session, cafe_id, auth.user.id)
    values = payload.model_dump(exclude={"visited_at"})
    visit = Visit(
        owner_id=auth.user.id,
        cafe_id=cafe.id,
        visited_at=payload.visited_at or utc_now(),
        **values,
    )
    session.add(visit)
    cafe.updated_at = utc_now()
    session.add(cafe)
    session.commit()
    session.refresh(visit)
    return _serialize_visit(session, visit)


@router.patch("/visits/{visit_id}", response_model=VisitRead)
def update_visit(
    visit_id: PositiveId,
    payload: VisitUpdate,
    session: SessionDep,
    auth: CsrfDep,
):
    visit = _find_visit(session, visit_id, auth.user.id)
    visit.sqlmodel_update(payload.model_dump(exclude_unset=True))
    visit.updated_at = utc_now()
    session.add(visit)
    session.commit()
    session.refresh(visit)
    return _serialize_visit(session, visit)


@router.delete("/visits/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_visit(
    visit_id: PositiveId,
    request: Request,
    session: SessionDep,
    auth: CsrfDep,
):
    visit = _find_visit(session, visit_id, auth.user.id)
    cafe = _find_cafe(session, visit.cafe_id, auth.user.id)
    photos = list(session.exec(select(VisitPhoto).where(VisitPhoto.visit_id == visit.id)).all())
    moved = quarantine_photos(Path(request.app.state.upload_dir), photos)
    try:
        for photo in photos:
            session.delete(photo)
        session.delete(visit)
        cafe.updated_at = utc_now()
        session.add(cafe)
        session.commit()
    except Exception:
        session.rollback()
        restore_quarantined(moved)
        raise HTTPException(status_code=500, detail="No se pudo eliminar la visita.") from None
    purge_quarantined(moved)
    return Response(status_code=204)
