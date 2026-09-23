from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import require_dentist
from backend.db import get_db
from backend.models import User
from backend.schemas.catalog import ProductListResponse
from backend.schemas.errors import ErrorResponse
from backend.services.catalog import list_products

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get(
    "",
    response_model=ProductListResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
def products(
    q: str | None = Query(default=None, max_length=100),
    category_id: int | None = Query(default=None, ge=1),
    is_implant: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
    _: User = Depends(require_dentist),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    return list_products(
        db,
        query=q,
        category_id=category_id,
        is_implant=is_implant,
        page=page,
        page_size=page_size,
    )
