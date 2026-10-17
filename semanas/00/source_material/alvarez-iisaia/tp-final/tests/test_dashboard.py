from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.models import Cafe, User, Visit
from backend.dashboard_routes import _monthly_points


def _login(client: TestClient, code: str):
    start = client.get("/auth/login", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    client.get(
        "/auth/callback",
        params={"code": code, "state": state},
        follow_redirects=False,
    )


def _visit_at(value: datetime) -> Visit:
    return Visit(owner_id=1, cafe_id=1, visited_at=value)


def test_monthly_points_are_ordered_across_a_year_change():
    points = _monthly_points([], datetime(2026, 2, 15, tzinfo=timezone.utc))

    assert [point.month for point in points] == [
        "2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08",
        "2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02",
    ]
    assert points[9].label == "diciembre 2025"
    assert points[10].label == "enero 2026"


def test_monthly_points_handle_zero_and_one_visit():
    now = datetime(2026, 2, 15, tzinfo=timezone.utc)
    empty = _monthly_points([], now)
    single = _monthly_points([_visit_at(datetime(2026, 2, 1, tzinfo=timezone.utc))], now)

    assert [point.count for point in empty] == [0] * 12
    assert [point.cumulative for point in empty] == [0] * 12
    assert [point.count for point in single] == [0] * 11 + [1]
    assert [point.cumulative for point in single] == [0] * 11 + [1]


def test_monthly_points_keep_sparse_data_and_repeated_maxima():
    now = datetime(2026, 2, 15, tzinfo=timezone.utc)
    visits = [
        _visit_at(datetime(2025, 12, 2, tzinfo=timezone.utc)),
        _visit_at(datetime(2025, 12, 20, tzinfo=timezone.utc)),
        _visit_at(datetime(2026, 1, 3, tzinfo=timezone.utc)),
        _visit_at(datetime(2026, 1, 25, tzinfo=timezone.utc)),
        _visit_at(datetime(2026, 2, 8, tzinfo=timezone.utc)),
    ]

    points = _monthly_points(visits, now)

    assert [point.count for point in points[-3:]] == [2, 2, 1]
    assert [point.cumulative for point in points[-3:]] == [2, 4, 5]
    assert max(point.count for point in points) == 2
    assert [point.month for point in points if point.count == 2] == ["2025-12", "2026-01"]


def test_dashboard_aggregates_months_ratings_and_nearby_pending(client, app):
    now = datetime.now(timezone.utc)
    cafes = client.get("/api/cafes").json()
    visited = [cafe for cafe in cafes if cafe["visit_status"] == "VISITED"]
    pending = [cafe for cafe in cafes if cafe["visit_status"] == "PENDING"]

    with Session(app.state.engine) as session:
        user = session.exec(select(User).where(User.auth0_sub == "auth0|owner")).one()
        user.home_latitude = -34.6037
        user.home_longitude = -58.3816
        user.home_location_expires_at = now + timedelta(days=10)
        nearby = session.get(Cafe, pending[0]["id"])
        nearby.latitude = -34.6040
        nearby.longitude = -58.3820
        nearby.location_expires_at = now + timedelta(days=10)
        nearby_id = nearby.id
        owner_visits = list(session.exec(select(Visit).where(Visit.owner_id == user.id)).all())
        owner_visits[0].visited_at = now.replace(day=1) - timedelta(days=40)
        session.add(user)
        session.add(nearby)
        session.add(owner_visits[0])
        session.add(
            Visit(
                owner_id=user.id,
                cafe_id=visited[0]["id"],
                visited_at=now,
                coffee_rating=3,
                food_rating=5,
                ambience_rating=3,
                service_rating=5,
            )
        )
        session.commit()

    response = client.get("/api/dashboard")
    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["summary"] == {
        "total_cafes": 7,
        "visited_cafes": 4,
        "pending_cafes": 3,
        "favorite_cafes": 3,
        "total_visits": 5,
    }
    assert len(dashboard["monthly_visits"]) == 12
    assert any(point["count"] == 0 for point in dashboard["monthly_visits"])
    assert dashboard["monthly_visits"][-1]["cumulative"] == 5
    ratings = {item["key"]: item for item in dashboard["rating_averages"]}
    assert ratings["coffee_rating"] == {
        "key": "coffee_rating",
        "label": "Café",
        "average": 4.0,
        "count": 5,
    }
    assert dashboard["top_cafes"][0]["average_rating"] <= 5
    assert dashboard["nearby_pending"][0]["cafe_id"] == nearby_id
    assert dashboard["nearby_pending"][0]["distance_km"] > 0


def test_dashboard_is_empty_for_another_user(client, app):
    with TestClient(app, base_url="http://127.0.0.1:8000") as second:
        _login(second, "second")
        response = second.get("/api/dashboard")

    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["summary"] == {
        "total_cafes": 0,
        "visited_cafes": 0,
        "pending_cafes": 0,
        "favorite_cafes": 0,
        "total_visits": 0,
    }
    assert len(dashboard["monthly_visits"]) == 12
    assert all(point["count"] == 0 for point in dashboard["monthly_visits"])
    assert all(point["cumulative"] == 0 for point in dashboard["monthly_visits"])
    assert all(item["average"] is None for item in dashboard["rating_averages"])
    assert dashboard["neighborhoods"] == []
    assert dashboard["top_cafes"] == []
    assert dashboard["nearby_pending"] == []


def test_dashboard_groups_safe_neighborhood_aliases_without_rewriting(client, app):
    owner_id = client.get("/api/session").json()["user"]["id"]
    with Session(app.state.engine) as session:
        session.add(
            Cafe(
                owner_id=owner_id,
                name="Alias sin tilde",
                neighborhood="San Nicolas",
                description="Histórica.",
            )
        )
        session.add(
            Cafe(
                owner_id=owner_id,
                name="Alias con tilde",
                neighborhood="San Nicolás",
                description="Canónica.",
            )
        )
        session.add(
            Cafe(
                owner_id=owner_id,
                name="Sin equivalencia",
                neighborhood="Centro",
                description="Histórica.",
            )
        )
        session.commit()

    neighborhoods = {
        item["neighborhood"]: item["count"]
        for item in client.get("/api/dashboard").json()["neighborhoods"]
    }

    assert neighborhoods["San Nicolás"] == 2
    assert neighborhoods["Centro"] == 1
    with Session(app.state.engine) as session:
        stored = session.exec(
            select(Cafe.neighborhood).where(Cafe.name == "Alias sin tilde")
        ).one()
    assert stored == "San Nicolas"
