from datetime import datetime, timezone
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    TypeAdapter,
    field_validator,
    model_validator,
)

from backend.models import VisitStatus

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Neighborhood = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=80),
]
Description = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=600),
]
Rating = Annotated[int, Field(ge=1, le=5)]
IMAGE_ADAPTER = TypeAdapter(HttpUrl)


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CafeCreate(StrictSchema):
    name: Name
    neighborhood: Neighborhood
    description: Description
    image_url: str | None = None
    visit_status: VisitStatus = VisitStatus.PENDING
    is_favorite: bool = False
    coffee_rating: Rating | None = None
    food_rating: Rating | None = None
    ambience_rating: Rating | None = None
    service_rating: Rating | None = None

    @field_validator("image_url", mode="before")
    @classmethod
    def normalize_image_url(cls, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        normalized = str(IMAGE_ADAPTER.validate_python(value.strip()))
        if len(normalized) > 2048:
            raise ValueError("La URL no puede superar los 2048 caracteres.")
        return normalized


class CafeUpdate(StrictSchema):
    name: Name | None = None
    neighborhood: Neighborhood | None = None
    description: Description | None = None
    image_url: str | None = None
    visit_status: VisitStatus | None = None
    is_favorite: bool | None = None
    coffee_rating: Rating | None = None
    food_rating: Rating | None = None
    ambience_rating: Rating | None = None
    service_rating: Rating | None = None

    @field_validator("image_url", mode="before")
    @classmethod
    def normalize_image_url(cls, value):
        return CafeCreate.normalize_image_url(value)

    @model_validator(mode="after")
    def validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Debés enviar al menos un campo para actualizar.")
        required_fields = {
            "name",
            "neighborhood",
            "description",
            "visit_status",
            "is_favorite",
        }
        for field_name in required_fields & self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} no puede ser null.")
        return self


class CafeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    neighborhood: str
    description: str
    image_url: str | None
    visit_status: VisitStatus
    is_favorite: bool
    coffee_rating: int | None
    food_rating: int | None
    ambience_rating: int | None
    service_rating: int | None
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class StatsRead(BaseModel):
    total: int
    visited: int
    pending: int
    favorites: int

