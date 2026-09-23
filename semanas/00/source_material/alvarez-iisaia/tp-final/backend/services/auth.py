from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import User, UserRole

password_hasher = PasswordHasher()
DUMMY_HASH = password_hasher.hash("dummy-password-used-only-for-timing")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def authenticate_dentist(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(func.lower(User.username) == username.lower()))
    valid_password = verify_password(user.password_hash if user else DUMMY_HASH, password)
    if not user or not valid_password or not user.is_active or user.role != UserRole.DENTIST:
        return None
    return user


def session_serializer(secret: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=secret, salt="dentist-session-v1")


def create_session_token(user_id: int, secret: str) -> str:
    return session_serializer(secret).dumps({"user_id": user_id})


def read_session_token(token: str, secret: str, max_age: int) -> int | None:
    try:
        payload = session_serializer(secret).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    user_id = payload.get("user_id") if isinstance(payload, dict) else None
    return user_id if isinstance(user_id, int) else None
