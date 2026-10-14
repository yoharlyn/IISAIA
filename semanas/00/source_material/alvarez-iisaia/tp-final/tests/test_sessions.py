from datetime import datetime, timedelta, timezone

from sqlmodel import Session

from backend.models import LocalSession, User
from backend.security import (
    SESSION_ABSOLUTE_TTL,
    csrf_matches,
    hash_secret,
    issue_session,
    resolve_session,
    revoke_session,
)


def create_user(app) -> User:
    with Session(app.state.engine) as db:
        user = User(auth0_sub="auth0|session-user", display_name="Ana")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def test_session_persists_only_hashes(client, app):
    user = create_user(app)
    with Session(app.state.engine) as db:
        issued = issue_session(db, db.get(User, user.id))
        row = db.get(LocalSession, issued.record.id)

        assert row.token_hash == hash_secret(issued.token)
        assert row.csrf_hash == hash_secret(issued.csrf_token)
        assert issued.token not in row.token_hash
        assert issued.csrf_token not in row.csrf_hash


def test_idle_expiration_deletes_the_local_session(client, app):
    user = create_user(app)
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with Session(app.state.engine) as db:
        issued = issue_session(db, db.get(User, user.id), now=started)
        resolved = resolve_session(
            db, issued.token, now=started + timedelta(hours=8, seconds=1)
        )

        assert resolved is None
        assert db.get(LocalSession, issued.record.id) is None


def test_touch_never_extends_the_absolute_expiration(client, app):
    user = create_user(app)
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with Session(app.state.engine) as db:
        issued = issue_session(db, db.get(User, user.id), now=started)
        issued.record.idle_expires_at = issued.record.absolute_expires_at
        db.add(issued.record)
        db.commit()
        resolved = resolve_session(
            db, issued.token, now=started + timedelta(days=6, hours=23)
        )

        assert resolved is not None
        assert resolved[0].absolute_expires_at.replace(tzinfo=timezone.utc) == (
            started + SESSION_ABSOLUTE_TTL
        )
        assert resolved[0].idle_expires_at.replace(tzinfo=timezone.utc) == (
            started + SESSION_ABSOLUTE_TTL
        )


def test_csrf_uses_the_issued_random_value(client, app):
    user = create_user(app)
    with Session(app.state.engine) as db:
        issued = issue_session(db, db.get(User, user.id))
        assert csrf_matches(issued.record, issued.csrf_token)
        assert not csrf_matches(issued.record, "incorrecto")


def test_revocation_is_idempotent(client, app):
    user = create_user(app)
    with Session(app.state.engine) as db:
        issued = issue_session(db, db.get(User, user.id))
        assert revoke_session(db, issued.token) is True
        assert revoke_session(db, issued.token) is False
