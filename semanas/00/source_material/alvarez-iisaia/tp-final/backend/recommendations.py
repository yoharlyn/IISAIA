from collections import defaultdict
from math import log

from sqlmodel import Session, select

from backend.distance import haversine_km
from backend.google_places import Coordinates, PlaceCandidate
from backend.models import Cafe, Visit
from backend.neighborhoods import display_neighborhood


BASE_WEIGHTS = {
    "proximity": 0.35,
    "google_rating": 0.30,
    "review_confidence": 0.15,
    "novelty": 0.10,
    "personal_affinity": 0.10,
}
RATINGS = ("coffee_rating", "food_rating", "ambience_rating", "service_rating")


def novelty_for(candidate: PlaceCandidate, cafes_by_place: dict[str, Cafe], visited_ids: set[int]):
    cafe = cafes_by_place.get(candidate.place_id)
    if cafe is None:
        return 1.0, "No guardada"
    if cafe.id in visited_ids:
        return 0.20, "Visitada"
    return 0.65, "Pendiente"


def personal_affinity_by_neighborhood(
    session: Session, owner_id: int
) -> dict[str, float] | None:
    visits = session.exec(select(Visit).where(Visit.owner_id == owner_id)).all()
    cafes = {
        cafe.id: cafe
        for cafe in session.exec(select(Cafe).where(Cafe.owner_id == owner_id)).all()
    }
    samples = defaultdict(list)
    rated_visits = 0
    for visit in visits:
        values = [getattr(visit, field) for field in RATINGS if getattr(visit, field) is not None]
        cafe = cafes.get(visit.cafe_id)
        if not values or cafe is None:
            continue
        rated_visits += 1
        samples[display_neighborhood(cafe.neighborhood)].append(sum(values) / len(values))
    if rated_visits < 5 or len(samples) < 2:
        return None
    global_values = [value for values in samples.values() for value in values]
    global_mean = sum(global_values) / len(global_values)
    return {
        neighborhood: ((sum(values) + global_mean * 3) / (len(values) + 3)) / 5
        for neighborhood, values in samples.items()
    }


def score_candidate(
    candidate: PlaceCandidate,
    *,
    distance_km: float,
    radius_km: float,
    novelty: float,
    affinity: float | None,
) -> tuple[float, dict[str, float]]:
    values = {
        "proximity": max(0.0, 1 - distance_km / radius_km),
        "google_rating": candidate.rating / 5 if candidate.rating is not None else None,
        "review_confidence": (
            log(1 + min(candidate.user_rating_count, 1000)) / log(1001)
            if candidate.user_rating_count is not None
            else None
        ),
        "novelty": novelty,
        "personal_affinity": affinity,
    }
    active_weight = sum(
        BASE_WEIGHTS[name] for name, value in values.items() if value is not None
    )
    factors = {
        name: value * BASE_WEIGHTS[name] / active_weight
        for name, value in values.items()
        if value is not None
    }
    return sum(factors.values()), factors


def candidate_distance(candidate: PlaceCandidate, origin: Coordinates) -> float:
    return haversine_km(origin, candidate.location)
