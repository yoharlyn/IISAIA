from math import atan2, cos, radians, sin, sqrt

from backend.google_places import Coordinates


EARTH_RADIUS_KM = 6371.0088


def haversine_km(origin: Coordinates, destination: Coordinates) -> float:
    lat1 = radians(origin.latitude)
    lat2 = radians(destination.latitude)
    delta_lat = radians(destination.latitude - origin.latitude)
    delta_lng = radians(destination.longitude - origin.longitude)
    value = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * atan2(sqrt(value), sqrt(1 - value))
