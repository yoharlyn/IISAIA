from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import CheckConstraint, Column, Index, String, UniqueConstraint
from sqlmodel import Field, SQLModel


class VisitStatus(str, Enum):
    PENDING = "PENDING"
    VISITED = "VISITED"


class IdentityStatus(str, Enum):
    PENDING_LOGIN = "PENDING_LOGIN"
    ACTIVE = "ACTIVE"


class LocationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    NEEDS_LOCATION = "NEEDS_LOCATION"
    EXPIRED = "EXPIRED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "identity_status IN ('PENDING_LOGIN', 'ACTIVE')",
            name="ck_users_identity_status",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    auth0_sub: str = Field(
        sa_column=Column(String(255), unique=True, index=True, nullable=False)
    )
    identity_status: IdentityStatus = Field(default=IdentityStatus.ACTIVE, index=True)
    email: str | None = Field(default=None, max_length=320)
    display_name: str = Field(default="Usuario", max_length=100)
    home_place_id: str | None = Field(default=None, max_length=255)
    home_selected_address: str | None = Field(default=None, max_length=500)
    home_latitude: float | None = Field(default=None)
    home_longitude: float | None = Field(default=None)
    home_location_fetched_at: datetime | None = Field(default=None)
    home_location_expires_at: datetime | None = Field(default=None)
    home_neighborhood: str | None = Field(default=None, max_length=80)
    home_caba_verified_at: datetime | None = Field(default=None)
    home_caba_polygon_version: str | None = Field(default=None, max_length=80)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class LocalSession(SQLModel, table=True):
    __tablename__ = "sessions"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
    )

    id: int | None = Field(default=None, primary_key=True)
    token_hash: str = Field(max_length=64, index=True)
    csrf_hash: str = Field(max_length=64)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utc_now)
    last_seen_at: datetime = Field(default_factory=utc_now)
    idle_expires_at: datetime
    absolute_expires_at: datetime


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
            "location_status IN ('VERIFIED', 'NEEDS_LOCATION', 'EXPIRED')",
            name="ck_cafes_location_status",
        ),
        Index("ix_cafes_owner_place", "owner_id", "place_id", unique=True),
    )

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100, index=True)
    neighborhood: str = Field(max_length=80, index=True)
    description: str = Field(max_length=600)
    image_url: str | None = Field(default=None, max_length=2048)
    is_favorite: bool = Field(default=False, index=True)
    place_id: str | None = Field(default=None, max_length=255)
    place_id_checked_at: datetime | None = Field(default=None)
    selected_address: str | None = Field(default=None, max_length=500)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)
    location_fetched_at: datetime | None = Field(default=None)
    location_expires_at: datetime | None = Field(default=None)
    caba_verified_at: datetime | None = Field(default=None)
    caba_polygon_version: str | None = Field(default=None, max_length=80)
    location_status: LocationStatus = Field(default=LocationStatus.NEEDS_LOCATION)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Visit(SQLModel, table=True):
    __tablename__ = "visits"
    __table_args__ = (
        CheckConstraint("coffee_rating IS NULL OR coffee_rating BETWEEN 1 AND 5"),
        CheckConstraint("food_rating IS NULL OR food_rating BETWEEN 1 AND 5"),
        CheckConstraint("ambience_rating IS NULL OR ambience_rating BETWEEN 1 AND 5"),
        CheckConstraint("service_rating IS NULL OR service_rating BETWEEN 1 AND 5"),
    )

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    cafe_id: int = Field(foreign_key="cafes.id", index=True)
    visited_at: datetime = Field(default_factory=utc_now, index=True)
    note: str | None = Field(default=None, max_length=1000)
    coffee_rating: int | None = Field(default=None, ge=1, le=5)
    food_rating: int | None = Field(default=None, ge=1, le=5)
    ambience_rating: int | None = Field(default=None, ge=1, le=5)
    service_rating: int | None = Field(default=None, ge=1, le=5)
    date_is_estimated: bool = Field(default=False)
    migration_key: str | None = Field(default=None, max_length=255, unique=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VisitPhoto(SQLModel, table=True):
    __tablename__ = "visit_photos"
    __table_args__ = (
        CheckConstraint("size_bytes > 0 AND size_bytes <= 5242880"),
        CheckConstraint("width > 0 AND height > 0 AND width * height <= 20000000"),
    )

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    visit_id: int = Field(foreign_key="visits.id", index=True)
    internal_name: str = Field(max_length=80, unique=True)
    mime_type: str = Field(max_length=40)
    size_bytes: int
    width: int
    height: int
    sha256: str = Field(max_length=64, index=True)
    caption: str = Field(max_length=200)
    created_at: datetime = Field(default_factory=utc_now)


class PlaceDiscovery(SQLModel, table=True):
    __tablename__ = "place_discoveries"
    __table_args__ = (
        UniqueConstraint("owner_id", "place_id", name="uq_discoveries_owner_place"),
    )

    id: int | None = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="users.id", index=True)
    place_id: str = Field(max_length=255, index=True)
    first_seen_at: datetime = Field(default_factory=utc_now)
    last_seen_at: datetime = Field(default_factory=utc_now)
