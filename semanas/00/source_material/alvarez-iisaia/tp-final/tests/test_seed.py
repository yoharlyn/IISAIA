from sqlmodel import Session, func, select

from backend.models import Cafe
from backend.seed import seed_cafes


def count_cafes(engine) -> int:
    with Session(engine) as session:
        return session.exec(select(func.count()).select_from(Cafe)).one()


def test_seed_inserts_seven_cafes_on_first_start(client, app):
    assert count_cafes(app.state.engine) == 7


def test_seed_is_idempotent(client, app):
    user_id = client.get("/api/session").json()["user"]["id"]
    seed_cafes(app.state.engine, user_id)
    assert count_cafes(app.state.engine) == 7


def test_seed_does_not_restore_deleted_rows(client, app):
    user_id = client.get("/api/session").json()["user"]["id"]
    with Session(app.state.engine) as session:
        cafe = session.exec(select(Cafe).order_by(Cafe.id)).first()
        session.delete(cafe)
        session.commit()
    seed_cafes(app.state.engine, user_id)
    assert count_cafes(app.state.engine) == 6
