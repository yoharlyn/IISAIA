from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ImplantSpecsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    diameter_mm: Decimal
    length_mm: Decimal
    connection_type: str | None
    material: str | None
    surface_treatment: str | None

    @field_serializer("diameter_mm", "length_mm")
    def serialize_decimal(self, value: Decimal) -> str:
        return format(value, "f")


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    name: str
    description: str | None
    brand: str | None
    category: CategoryResponse
    manufacturer_name: str
    price_cents: int
    stock: int
    is_implant: bool
    implant_specs: ImplantSpecsResponse | None


class PaginationResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    pagination: PaginationResponse
    available_categories: list[CategoryResponse]
