import math

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.models import Category, Product
from backend.schemas.catalog import PaginationResponse, ProductListResponse, ProductResponse


def list_products(
    db: Session,
    *,
    query: str | None,
    category_id: int | None,
    is_implant: bool | None,
    page: int,
    page_size: int,
) -> ProductListResponse:
    filters = [Product.is_active.is_(True)]
    if query and (term := query.strip()):
        pattern = f"%{term.lower()}%"
        filters.append(
            or_(
                func.lower(Product.name).like(pattern),
                func.lower(Product.sku).like(pattern),
                func.lower(Product.brand).like(pattern),
                func.lower(Product.manufacturer_name).like(pattern),
            )
        )
    if category_id is not None:
        filters.append(Product.category_id == category_id)
    if is_implant is not None:
        filters.append(Product.is_implant.is_(is_implant))

    total = db.scalar(select(func.count(Product.id)).where(*filters)) or 0
    products = (
        db.scalars(
            select(Product)
            .where(*filters)
            .order_by(func.lower(Product.name), Product.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .unique()
        .all()
    )
    categories = db.scalars(
        select(Category)
        .join(Product, Product.category_id == Category.id)
        .where(Product.is_active.is_(True))
        .distinct()
        .order_by(Category.name)
    ).all()
    return ProductListResponse(
        items=[ProductResponse.model_validate(product) for product in products],
        pagination=PaginationResponse(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
        available_categories=categories,
    )
