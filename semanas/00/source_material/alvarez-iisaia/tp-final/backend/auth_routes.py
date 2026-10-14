import secrets
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlmodel import Session, select

from backend.auth import AuthError, AuthIdentity, AuthProvider
from backend.db import get_session
from backend.models import IdentityStatus, LocalSession, User, utc_now
from backend.security import (
    OIDC_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    csrf_matches,
    derive_csrf_token,
    issue_session,
    resolve_session,
    revoke_session,
)

auth_router = APIRouter(prefix="/auth")
session_router = APIRouter(prefix="/api")


@dataclass(slots=True)
class AuthContext:
    user: User
    local_session: LocalSession
    raw_token: str


def _serializer(request: Request) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(request.app.state.settings.session_secret)


def _auth_provider(request: Request) -> AuthProvider:
    return request.app.state.auth_provider


def _start_auth(request: Request, *, screen_hint: str | None = None):
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    payload = _serializer(request).dumps({"state": state, "nonce": nonce})
    try:
        location = _auth_provider(request).authorization_url(
            state=state, nonce=nonce, screen_hint=screen_hint
        )
    except (AuthError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La autenticación no está disponible en este momento.",
        ) from None
    response = RedirectResponse(location, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        OIDC_COOKIE_NAME,
        payload,
        httponly=True,
        samesite="lax",
        secure=request.app.state.cookie_secure,
        max_age=600,
        path="/auth",
    )
    return response


@auth_router.get("/login")
def login(request: Request):
    return _start_auth(request)


@auth_router.get("/signup")
def signup(request: Request):
    return _start_auth(request, screen_hint="signup")


def _load_oidc_transaction(request: Request, state: str) -> dict[str, str]:
    encoded = request.cookies.get(OIDC_COOKIE_NAME)
    if not encoded:
        raise HTTPException(status_code=400, detail="La transacción de login venció.")
    try:
        payload = _serializer(request).loads(encoded, max_age=600)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=400, detail="La transacción de login no es válida.") from None
    if not secrets.compare_digest(payload.get("state", ""), state):
        raise HTTPException(status_code=400, detail="El estado OIDC no coincide.")
    return payload


def reconcile_user(db: Session, identity: AuthIdentity) -> User:
    user = db.exec(select(User).where(User.auth0_sub == identity.sub)).first()
    if user is None:
        user = User(
            auth0_sub=identity.sub,
            identity_status=IdentityStatus.ACTIVE,
            email=identity.email,
            display_name=identity.name or "Usuario",
        )
    else:
        user.identity_status = IdentityStatus.ACTIVE
        user.email = identity.email
        if identity.name and user.display_name == "Usuario":
            user.display_name = identity.name
        user.updated_at = utc_now()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@auth_router.get("/callback")
async def callback(
    request: Request,
    code: str = Query(min_length=1),
    state: str = Query(min_length=1),
    db: Session = Depends(get_session),
):
    transaction = _load_oidc_transaction(request, state)
    try:
        identity = await _auth_provider(request).exchange_code(
            code=code, nonce=transaction["nonce"]
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo completar la autenticación.",
        ) from None
    previous = request.cookies.get(SESSION_COOKIE_NAME)
    if previous:
        revoke_session(db, previous)
    user = reconcile_user(db, identity)
    issued = issue_session(db, user, csrf_key=request.app.state.settings.session_secret)
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(OIDC_COOKIE_NAME, path="/auth")
    response.set_cookie(
        SESSION_COOKIE_NAME,
        issued.token,
        httponly=True,
        samesite="lax",
        secure=request.app.state.cookie_secure,
        max_age=7 * 24 * 60 * 60,
        path="/",
    )
    return response


def require_auth(request: Request, db: Session = Depends(get_session)) -> AuthContext:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Necesitás iniciar sesión.")
    resolved = resolve_session(db, token)
    if resolved is None:
        raise HTTPException(status_code=401, detail="La sesión venció o no es válida.")
    local_session, user = resolved
    return AuthContext(user=user, local_session=local_session, raw_token=token)


def require_csrf(
    request: Request,
    context: AuthContext = Depends(require_auth),
) -> AuthContext:
    origin = request.headers.get("Origin")
    if origin != request.app.state.settings.app_base_url:
        raise HTTPException(status_code=403, detail="Origen no permitido.")
    candidate = request.headers.get("X-CSRF-Token", "")
    if not candidate or not csrf_matches(context.local_session, candidate):
        raise HTTPException(status_code=403, detail="Token CSRF inválido.")
    return context


@session_router.get("/session")
def session_status(
    request: Request,
    context: AuthContext = Depends(require_auth),
):
    csrf_token = derive_csrf_token(
        context.raw_token, request.app.state.settings.session_secret
    )
    return {
        "authenticated": True,
        "csrf_token": csrf_token,
        "user": {
            "id": context.user.id,
            "email": context.user.email,
            "display_name": context.user.display_name,
        },
    }


@auth_router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_session),
    context: AuthContext = Depends(require_csrf),
):
    revoke_session(db, context.raw_token)
    try:
        location = _auth_provider(request).logout_url()
    except (AuthError, ValueError):
        location = "/"
    response = RedirectResponse(location, status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response
