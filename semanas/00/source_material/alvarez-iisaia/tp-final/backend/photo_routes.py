from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path as ApiPath, Request, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from backend.auth_routes import AuthContext, require_auth, require_csrf
from backend.db import get_session
from backend.models import Visit, VisitPhoto
from backend.schemas import VisitPhotoRead
from backend.uploads import (
    MAX_FILE_BYTES,
    MAX_PHOTOS_PER_VISIT,
    MAX_VISIT_BYTES,
    UploadValidationError,
    new_internal_name,
    photo_path,
    process_image,
    purge_quarantined,
    quarantine_photos,
    restore_quarantined,
    write_photo,
)


router = APIRouter(prefix="/api")
SessionDep = Annotated[Session, Depends(get_session)]
AuthDep = Annotated[AuthContext, Depends(require_auth)]
CsrfDep = Annotated[AuthContext, Depends(require_csrf)]
PositiveId = Annotated[int, ApiPath(gt=0)]


def _root(request: Request) -> Path:
    return Path(request.app.state.upload_dir)


def _find_visit(session: Session, visit_id: int, owner_id: int) -> Visit:
    visit = session.exec(
        select(Visit).where(Visit.id == visit_id, Visit.owner_id == owner_id)
    ).first()
    if visit is None:
        raise HTTPException(status_code=404, detail="Visita no encontrada.")
    return visit


def _find_photo(session: Session, photo_id: int, owner_id: int) -> VisitPhoto:
    photo = session.exec(
        select(VisitPhoto).where(
            VisitPhoto.id == photo_id,
            VisitPhoto.owner_id == owner_id,
        )
    ).first()
    if photo is None:
        raise HTTPException(status_code=404, detail="Fotografía no encontrada.")
    return photo


def photo_read(photo: VisitPhoto) -> VisitPhotoRead:
    return VisitPhotoRead(
        **photo.model_dump(),
        url=f"/api/photos/{photo.id}",
    )


@router.post(
    "/visits/{visit_id}/photos",
    response_model=VisitPhotoRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_photo(
    visit_id: PositiveId,
    request: Request,
    session: SessionDep,
    auth: CsrfDep,
    file: Annotated[UploadFile, File()],
    caption: Annotated[str, Form(min_length=1, max_length=200)],
):
    visit = _find_visit(session, visit_id, auth.user.id)
    normalized_caption = caption.strip()
    if not normalized_caption:
        raise HTTPException(status_code=422, detail="Describí la fotografía.")
    photos = session.exec(
        select(VisitPhoto).where(
            VisitPhoto.visit_id == visit.id,
            VisitPhoto.owner_id == auth.user.id,
        )
    ).all()
    if len(photos) >= MAX_PHOTOS_PER_VISIT:
        raise HTTPException(status_code=409, detail="Cada visita admite hasta 5 fotografías.")
    content = await file.read(MAX_FILE_BYTES + 1)
    await file.close()
    try:
        processed = process_image(content, file.content_type)
    except UploadValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None
    used_bytes = sum(photo.size_bytes for photo in photos)
    if used_bytes + len(processed.content) > MAX_VISIT_BYTES:
        raise HTTPException(
            status_code=409,
            detail="Las fotografías de la visita superan el límite acumulado de 20 MiB.",
        )
    photo = VisitPhoto(
        owner_id=auth.user.id,
        visit_id=visit.id,
        internal_name=new_internal_name(processed.extension),
        mime_type=processed.mime_type,
        size_bytes=len(processed.content),
        width=processed.width,
        height=processed.height,
        sha256=processed.sha256,
        caption=normalized_caption,
    )
    destination = write_photo(_root(request), photo, processed.content)
    try:
        session.add(photo)
        session.commit()
        session.refresh(photo)
    except Exception:
        session.rollback()
        if destination.exists():
            destination.unlink()
        raise HTTPException(
            status_code=500,
            detail="No se pudo guardar la fotografía.",
        ) from None
    return photo_read(photo)


@router.get("/photos/{photo_id}")
def get_photo(
    photo_id: PositiveId,
    request: Request,
    session: SessionDep,
    auth: AuthDep,
):
    photo = _find_photo(session, photo_id, auth.user.id)
    try:
        stored = photo_path(_root(request), photo)
    except ValueError:
        raise HTTPException(status_code=404, detail="Archivo de fotografía no disponible.") from None
    if not stored.is_file():
        raise HTTPException(status_code=404, detail="Archivo de fotografía no disponible.")
    return FileResponse(
        stored,
        media_type=photo.mime_type,
        headers={"Cache-Control": "private, no-store"},
    )


@router.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    photo_id: PositiveId,
    request: Request,
    session: SessionDep,
    auth: CsrfDep,
):
    photo = _find_photo(session, photo_id, auth.user.id)
    moved = quarantine_photos(_root(request), [photo])
    try:
        session.delete(photo)
        session.commit()
    except Exception:
        session.rollback()
        restore_quarantined(moved)
        raise HTTPException(
            status_code=500,
            detail="No se pudo eliminar la fotografía.",
        ) from None
    purge_quarantined(moved)
    return Response(status_code=204)
