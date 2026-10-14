import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from backend.models import LocalSession, User

SESSION_COOKIE_NAME = "coffee_atlas_session"
OIDC_COOKIE_NAME = "coffee_atlas_oidc"
SESSION_IDLE_TTL = timedelta(hours=8)
SESSION_ABSOLUTE_TTL = timedelta(days=7)


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def derive_csrf_token(token: str, key: str) -> str:
    return hmac.new(key.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass(frozen=True, slots=True)
class IssuedSession:
    token: str
    csrf_token: str
    record: LocalSession


def issue_session(
    session: Session,
    user: User,
    *,
    now: datetime | None = None,
    csrf_key: str = "coffee-atlas-test-csrf-key",
) -> IssuedSession:
    issued_at = now or datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    csrf_token = derive_csrf_token(token, csrf_key)
    record = LocalSession(
        token_hash=hash_secret(token),
        csrf_hash=hash_secret(csrf_token),
        user_id=user.id,
        created_at=issued_at,
        last_seen_at=issued_at,
        idle_expires_at=issued_at + SESSION_IDLE_TTL,
        absolute_expires_at=issued_at + SESSION_ABSOLUTE_TTL,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return IssuedSession(token=token, csrf_token=csrf_token, record=record)


def resolve_session(
    session: Session,
    token: str,
    *,
    now: datetime | None = None,
    touch: bool = True,
) -> tuple[LocalSession, User] | None:
    current_time = now or datetime.now(timezone.utc)
    record = session.exec(
        select(LocalSession).where(LocalSession.token_hash == hash_secret(token))
    ).first()
    if record is None:
        return None
    if current_time >= _aware(record.idle_expires_at) or current_time >= _aware(
        record.absolute_expires_at
    ):
        session.delete(record)
        session.commit()
        return None
    user = session.get(User, record.user_id)
    if user is None:
        session.delete(record)
        session.commit()
        return None
    if touch:
        record.last_seen_at = current_time
        record.idle_expires_at = min(
            current_time + SESSION_IDLE_TTL,
            _aware(record.absolute_expires_at),
        )
        session.add(record)
        session.commit()
    return record, user


def csrf_matches(record: LocalSession, candidate: str) -> bool:
    return hmac.compare_digest(record.csrf_hash, hash_secret(candidate))


def revoke_session(session: Session, token: str) -> bool:
    record = session.exec(
        select(LocalSession).where(LocalSession.token_hash == hash_secret(token))
    ).first()
    if record is None:
        return False
    session.delete(record)
    session.commit()
    return True
