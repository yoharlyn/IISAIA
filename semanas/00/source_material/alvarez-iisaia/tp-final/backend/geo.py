import json
import math
import unicodedata
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timedelta, timezone

from backend.google_places import AddressComponent, Coordinates


DATA_DIR = Path(__file__).resolve().parent / "data"
PERIMETER_PATH = DATA_DIR / "caba_perimeter.geojson"
NEIGHBORHOODS_PATH = DATA_DIR / "caba_neighborhoods.geojson"
CABA_POLYGON_VERSION = "gcba-2026-07-29"
LOCATION_TTL = timedelta(days=29)


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def components_indicate_caba(components: tuple[AddressComponent, ...]) -> bool:
    for component in components:
        if "administrative_area_level_1" not in component.types:
            continue
        values = {_normalized(component.long_text), _normalized(component.short_text)}
        if "caba" in values or "ciudad autonoma de buenos aires" in values:
            return True
    return False


def location_expiry(fetched_at: datetime) -> datetime:
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    return fetched_at.astimezone(timezone.utc) + LOCATION_TTL


def location_is_fresh(expires_at: datetime | None, *, now: datetime | None = None) -> bool:
    if expires_at is None:
        return False
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > reference


@lru_cache(maxsize=2)
def _features(path: Path) -> tuple[dict, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection":
        raise ValueError("El archivo geográfico no es un FeatureCollection.")
    return tuple(payload.get("features", ()))


def _on_segment(point, start, end, *, epsilon=1e-10) -> bool:
    px, py = point
    ax, ay = start
    bx, by = end
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    if abs(cross) > epsilon:
        return False
    return (
        min(ax, bx) - epsilon <= px <= max(ax, bx) + epsilon
        and min(ay, by) - epsilon <= py <= max(ay, by) + epsilon
    )


def _in_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    inside = False
    px, py = point
    for index, current in enumerate(ring):
        previous = ring[index - 1]
        if _on_segment(point, previous, current):
            return True
        ax, ay = previous
        bx, by = current
        if (ay > py) != (by > py):
            intersection_x = (bx - ax) * (py - ay) / (by - ay) + ax
            if math.isclose(intersection_x, px, abs_tol=1e-12):
                return True
            if intersection_x > px:
                inside = not inside
    return inside


def _in_polygon(point: tuple[float, float], polygon: list[list[list[float]]]) -> bool:
    return bool(polygon and _in_ring(point, polygon[0])) and not any(
        _in_ring(point, hole) for hole in polygon[1:]
    )


def _in_geometry(point: tuple[float, float], geometry: dict) -> bool:
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])
    if geometry_type == "Polygon":
        return _in_polygon(point, coordinates)
    if geometry_type == "MultiPolygon":
        return any(_in_polygon(point, polygon) for polygon in coordinates)
    return False


def is_in_caba(location: Coordinates) -> bool:
    point = (location.longitude, location.latitude)
    return any(
        _in_geometry(point, feature.get("geometry", {}))
        for feature in _features(PERIMETER_PATH)
    )


def neighborhood_for(location: Coordinates) -> str | None:
    point = (location.longitude, location.latitude)
    for feature in _features(NEIGHBORHOODS_PATH):
        if _in_geometry(point, feature.get("geometry", {})):
            properties = feature.get("properties", {})
            name = properties.get("BARRIO")
            return str(name).title() if name else None
    return None


def validate_caba_location(
    location: Coordinates, components: tuple[AddressComponent, ...]
) -> str:
    if not components_indicate_caba(components) or not is_in_caba(location):
        raise ValueError("La ubicación debe estar dentro de CABA.")
    neighborhood = neighborhood_for(location)
    if not neighborhood:
        raise ValueError("No se pudo determinar el barrio de la ubicación.")
    return neighborhood
