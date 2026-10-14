from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


class VisitStatus(str, Enum):
    PENDING = "PENDING"
    VISITED = "VISITED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Cafe(SQLModel, table=True):
    __tablename__ = "cafes"
    __table_args__ = (
        CheckConstraint("length(trim(name)) BETWEEN 1 AND 100", name="ck_cafes_name"),
        CheckConstraint(
            "length(trim(neighborhood)) BETWEEN 1 AND 80",
            name="ck_cafes_neighborhood",
        ),
        CheckConstraint(
            "length(trim(description)) BETWEEN 1 AND 600",
            name="ck_cafes_description",
        ),
        CheckConstraint(
            "visit_status IN ('PENDING', 'VISITED')",
            name="ck_cafes_visit_status",
        ),
        CheckConstraint(
            "coffee_rating IS NULL OR coffee_rating BETWEEN 1 AND 5",
            name="ck_cafes_coffee_rating",
        ),
        CheckConstraint(
            "food_rating IS NULL OR food_rating BETWEEN 1 AND 5",
            name="ck_cafes_food_rating",
        ),
        CheckConstraint(
            "ambience_rating IS NULL OR ambience_rating BETWEEN 1 AND 5",
            name="ck_cafes_ambience_rating",
        ),
        CheckConstraint(
            "service_rating IS NULL OR service_rating BETWEEN 1 AND 5",
            name="ck_cafes_service_rating",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, index=True)
    neighborhood: str = Field(max_length=80, index=True)
    description: str = Field(max_length=600)
    image_url: str | None = Field(default=None, max_length=2048)
    visit_status: VisitStatus = Field(default=VisitStatus.PENDING, index=True)
    is_favorite: bool = Field(default=False, index=True)
    coffee_rating: int | None = Field(default=None, ge=1, le=5)
    food_rating: int | None = Field(default=None, ge=1, le=5)
    ambience_rating: int | None = Field(default=None, ge=1, le=5)
    service_rating: int | None = Field(default=None, ge=1, le=5)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

