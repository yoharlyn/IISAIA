from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from backend.main import create_app
from backend.models import Cafe


def count_cafes(engine) -> int:
    with Session(engine) as session:
        return session.exec(select(func.count()).select_from(Cafe)).one()


def test_seed_inserts_seven_cafes_on_first_start(client, app):
    assert count_cafes(app.state.engine) == 7


def test_seed_is_idempotent(database_url):
    first_app = create_app(database_url=database_url)
    with TestClient(first_app):
        assert count_cafes(first_app.state.engine) == 7

    second_app = create_app(database_url=database_url)
    with TestClient(second_app):
        assert count_cafes(second_app.state.engine) == 7


def test_seed_does_not_restore_deleted_rows(database_url):
    first_app = create_app(database_url=database_url)
    with TestClient(first_app):
        with Session(first_app.state.engine) as session:
            cafe = session.exec(select(Cafe).order_by(Cafe.id)).first()
            session.delete(cafe)
            session.commit()
        assert count_cafes(first_app.state.engine) == 6

    second_app = create_app(database_url=database_url)
    with TestClient(second_app):
        assert count_cafes(second_app.state.engine) == 6
