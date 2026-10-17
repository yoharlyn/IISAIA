import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Iterable


NEIGHBORHOODS_PATH = Path(__file__).resolve().parent / "data" / "caba_neighborhoods.geojson"
EXPECTED_NEIGHBORHOOD_COUNT = 48

# El GeoJSON conserva varios nombres en ASCII. Estos ajustes agregan únicamente
# los diacríticos de presentación; el catálogo de nombres sigue derivándose de
# las features del recurso versionado.
DISPLAY_OVERRIDES = {
    "AGRONOMIA": "Agronomía",
    "CONSTITUCION": "Constitución",
    "NUÑEZ": "Núñez",
    "SAN CRISTOBAL": "San Cristóbal",
    "SAN NICOLAS": "San Nicolás",
    "VELEZ SARSFIELD": "Vélez Sarsfield",
    "VILLA ORTUZAR": "Villa Ortúzar",
    "VILLA PUEYRREDON": "Villa Pueyrredón",
}


def _display_name(raw_name: str) -> str:
    normalized = " ".join(raw_name.split())
    if normalized in DISPLAY_OVERRIDES:
        return DISPLAY_OVERRIDES[normalized]
    words = normalized.title().split()
    connectors = {"De", "Del", "La", "Las", "Los", "Y"}
    return " ".join(
        word.lower() if index and word in connectors else word
        for index, word in enumerate(words)
    )


def neighborhood_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", without_accents).split())


def spanish_sort_key(value: str) -> tuple:
    prepared = value.casefold().replace("ñ", "n~")
    normalized = unicodedata.normalize("NFKD", prepared)
    return tuple(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


@lru_cache(maxsize=1)
def official_neighborhoods() -> tuple[str, ...]:
    payload = json.loads(NEIGHBORHOODS_PATH.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection":
        raise RuntimeError("El catálogo de barrios no es un FeatureCollection.")
    features = payload.get("features", [])
    if len(features) != EXPECTED_NEIGHBORHOOD_COUNT:
        raise RuntimeError("El catálogo oficial debe contener exactamente 48 features.")

    raw_names = []
    for feature in features:
        properties = feature.get("properties", {})
        raw_name = properties.get("BARRIO")
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise RuntimeError("Cada feature oficial debe tener un BARRIO válido.")
        raw_names.append(" ".join(raw_name.split()))

    if len(set(raw_names)) != EXPECTED_NEIGHBORHOOD_COUNT:
        raise RuntimeError("Los nombres BARRIO del catálogo oficial deben ser únicos.")

    names = tuple(_display_name(name) for name in raw_names)
    keys = tuple(neighborhood_key(name) for name in names)
    if len(set(keys)) != EXPECTED_NEIGHBORHOOD_COUNT:
        raise RuntimeError("La canonicalización oficial produjo nombres ambiguos.")
    return tuple(sorted(names, key=spanish_sort_key))


@lru_cache(maxsize=1)
def _official_by_key() -> dict[str, str]:
    return {neighborhood_key(name): name for name in official_neighborhoods()}


def canonical_neighborhood(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    return _official_by_key().get(neighborhood_key(value))


def display_neighborhood(value: str) -> str:
    return canonical_neighborhood(value) or value.strip()


def neighborhood_matches(stored: str, requested: str) -> bool:
    requested_canonical = canonical_neighborhood(requested)
    if requested_canonical is not None:
        return canonical_neighborhood(stored) == requested_canonical
    return stored.strip().casefold() == requested.strip().casefold()


def historical_neighborhoods(values: Iterable[str]) -> tuple[str, ...]:
    historical: dict[str, str] = {}
    for value in values:
        cleaned = value.strip()
        if cleaned and canonical_neighborhood(cleaned) is None:
            historical.setdefault(cleaned.casefold(), cleaned)
    return tuple(sorted(historical.values(), key=spanish_sort_key))
