from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from backend.api.dependencies import require_dentist, verify_csrf
from backend.config import Settings, get_settings
from backend.db import get_db
from backend.errors import APIError
from backend.models import User
from backend.schemas.auth import LoginRequest, LoginResponse, PublicUser
from backend.schemas.errors import ErrorResponse
from backend.services.auth import authenticate_dentist, create_session_token
from backend.services.rate_limit import login_rate_limiter

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
ERROR_RESPONSES = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
}


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        200: {
            "headers": {
                "Set-Cookie": {
                    "description": (
                        "Cookie dentist_session; HttpOnly; SameSite=Lax; Path=/; "
                        "Secure in production."
                    ),
                    "schema": {"type": "string"},
                }
            }
        },
        **ERROR_RESPONSES,
    },
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    _: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{payload.username}:{client_ip}"
    if retry_after := login_rate_limiter.retry_after(key):
        raise APIError(
            429,
            "TOO_MANY_ATTEMPTS",
            "Demasiados intentos. Intente nuevamente más tarde.",
            headers={"Retry-After": str(retry_after)},
        )
    user = authenticate_dentist(db, payload.username, payload.password)
    if user is None:
        login_rate_limiter.fail(key)
        raise APIError(401, "INVALID_CREDENTIALS", "Usuario o contraseña incorrectos.")
    login_rate_limiter.success(key)
    response.set_cookie(
        key="dentist_session",
        value=create_session_token(user.id, settings.session_secret),
        max_age=settings.session_max_age_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return LoginResponse(user=PublicUser.model_validate(user))


@router.post(
    "/logout",
    status_code=204,
    response_class=Response,
    responses={
        204: {
            "headers": {
                "Set-Cookie": {
                    "description": (
                        "Expires the dentist_session cookie using the original attributes."
                    ),
                    "schema": {"type": "string"},
                }
            }
        },
        403: {"model": ErrorResponse},
    },
)
def logout(
    response: Response,
    _: None = Depends(verify_csrf),
    settings: Settings = Depends(get_settings),
) -> Response:
    response.delete_cookie(
        key="dentist_session",
        path="/",
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )
    response.status_code = 204
    return response


@router.get(
    "/me",
    response_model=PublicUser,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def me(user: User = Depends(require_dentist)) -> PublicUser:
    return PublicUser.model_validate(user)
