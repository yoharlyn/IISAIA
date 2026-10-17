from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from backend.auth_routes import AuthContext, require_auth
from backend.db import get_session
from backend.distance import haversine_km
from backend.geo import location_is_fresh
from backend.google_places import Coordinates
from backend.models import Cafe, Visit, utc_now
from backend.neighborhoods import display_neighborhood
from backend.schemas import (
    DashboardRead,
    DashboardSummary,
    MonthlyVisitPoint,
    NearbyPendingCafe,
    NeighborhoodCount,
    RatingAverage,
    TopCafe,
)


router = APIRouter(prefix="/api")
SessionDep = Annotated[Session, Depends(get_session)]
AuthDep = Annotated[AuthContext, Depends(require_auth)]
RATINGS = (
    ("coffee_rating", "Café"),
    ("food_rating", "Comida"),
    ("ambience_rating", "Ambiente"),
    ("service_rating", "Atención"),
)
MONTH_LABELS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _shift_month(month: datetime, amount: int) -> datetime:
    absolute = month.year * 12 + month.month - 1 + amount
    return datetime(absolute // 12, absolute % 12 + 1, 1, tzinfo=timezone.utc)


def _monthly_points(visits: list[Visit], now: datetime) -> list[MonthlyVisitPoint]:
    current = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    first = _shift_month(current, -11)
    counts = Counter(
        (_as_utc(visit.visited_at).year, _as_utc(visit.visited_at).month)
        for visit in visits
        if _as_utc(visit.visited_at) >= first
    )
    cumulative = sum(_as_utc(visit.visited_at) < first for visit in visits)
    points = []
    for offset in range(12):
        month = _shift_month(first, offset)
        count = counts[(month.year, month.month)]
        cumulative += count
        points.append(
            MonthlyVisitPoint(
                month=month.strftime("%Y-%m"),
                label=f"{MONTH_LABELS[month.month - 1]} {month.year}",
                count=count,
                cumulative=cumulative,
            )
        )
    return points


def _rating_averages(visits: list[Visit]) -> list[RatingAverage]:
    result = []
    for field, label in RATINGS:
        values = [getattr(visit, field) for visit in visits if getattr(visit, field) is not None]
        result.append(
            RatingAverage(
                key=field,
                label=label,
                average=round(sum(values) / len(values), 2) if values else None,
                count=len(values),
            )
        )
    return result


def _top_cafes(cafes: list[Cafe], visits: list[Visit]) -> list[TopCafe]:
    cafes_by_id = {cafe.id: cafe for cafe in cafes}
    by_cafe: dict[int, list[Visit]] = defaultdict(list)
    for visit in visits:
        by_cafe[visit.cafe_id].append(visit)
    ranked = []
    for cafe_id, cafe_visits in by_cafe.items():
        ratings = [
            getattr(visit, field)
            for visit in cafe_visits
            for field, _ in RATINGS
            if getattr(visit, field) is not None
        ]
        cafe = cafes_by_id.get(cafe_id)
        if cafe is None or not ratings:
            continue
        ranked.append(
            TopCafe(
                cafe_id=cafe.id,
                name=cafe.name,
                visit_count=len(cafe_visits),
                average_rating=round(sum(ratings) / len(ratings), 2),
            )
        )
    return sorted(
        ranked,
        key=lambda item: (-item.average_rating, -item.visit_count, item.name.casefold()),
    )[:5]


def _nearby_pending(
    cafes: list[Cafe], visits: list[Visit], auth: AuthContext
) -> list[NearbyPendingCafe]:
    user = auth.user
    if (
        user.home_latitude is None
        or user.home_longitude is None
        or not location_is_fresh(user.home_location_expires_at)
    ):
        return []
    visited_ids = {visit.cafe_id for visit in visits}
    origin = Coordinates(user.home_latitude, user.home_longitude)
    result = []
    for cafe in cafes:
        if (
            cafe.id in visited_ids
            or cafe.latitude is None
            or cafe.longitude is None
            or not location_is_fresh(cafe.location_expires_at)
        ):
            continue
        result.append(
            NearbyPendingCafe(
                cafe_id=cafe.id,
                name=cafe.name,
                neighborhood=display_neighborhood(cafe.neighborhood),
                distance_km=round(
                    haversine_km(origin, Coordinates(cafe.latitude, cafe.longitude)),
                    2,
                ),
            )
        )
    return sorted(result, key=lambda item: (item.distance_km, item.name.casefold()))[:5]


@router.get("/dashboard", response_model=DashboardRead)
def get_dashboard(session: SessionDep, auth: AuthDep):
    cafes = list(
        session.exec(select(Cafe).where(Cafe.owner_id == auth.user.id)).all()
    )
    visits = list(
        session.exec(select(Visit).where(Visit.owner_id == auth.user.id)).all()
    )
    visited_ids = {visit.cafe_id for visit in visits}
    neighborhoods = Counter(display_neighborhood(cafe.neighborhood) for cafe in cafes)
    return DashboardRead(
        summary=DashboardSummary(
            total_cafes=len(cafes),
            visited_cafes=sum(cafe.id in visited_ids for cafe in cafes),
            pending_cafes=sum(cafe.id not in visited_ids for cafe in cafes),
            favorite_cafes=sum(cafe.is_favorite for cafe in cafes),
            total_visits=len(visits),
        ),
        monthly_visits=_monthly_points(visits, utc_now()),
        rating_averages=_rating_averages(visits),
        neighborhoods=[
            NeighborhoodCount(neighborhood=name, count=count)
            for name, count in sorted(
                neighborhoods.items(), key=lambda item: (-item[1], item[0].casefold())
            )
        ],
        top_cafes=_top_cafes(cafes, visits),
        nearby_pending=_nearby_pending(cafes, visits, auth),
    )
