from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlmodel import SQLModel

from backend.db import DEFAULT_DATABASE_URL, build_engine
from backend.auth import Auth0Provider, AuthProvider
from backend.auth_routes import auth_router, session_router
from backend.config import Settings
from backend.routes import router
from backend.migrations import inspect_database
from backend.google_places import GooglePlacesProvider, PlacesProvider
from backend.profile_routes import router as profile_router
from backend.config_routes import router as config_router
from backend.recommendation_routes import router as recommendation_router
from backend.visit_routes import router as visit_router
from backend.photo_routes import router as photo_router
from backend.dashboard_routes import router as dashboard_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

CONTENT_SECURITY_POLICY = "; ".join(
    (
        "default-src 'self'",
        (
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://*.googleapis.com https://*.gstatic.com https://*.google.com "
            "https://*.ggpht.com https://*.googleusercontent.com blob:"
        ),
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        (
            "img-src 'self' data: http: https: https://*.googleapis.com https://*.gstatic.com "
            "https://*.google.com https://*.googleusercontent.com"
        ),
        (
            "connect-src 'self' https://*.googleapis.com https://*.google.com "
            "https://*.gstatic.com data: blob:"
        ),
        "frame-src https://*.google.com",
        "worker-src blob:",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    )
)


def create_app(
    database_url: str | None = None,
    *,
    seed_on_startup: bool = True,
    settings: Settings | None = None,
    auth_provider: AuthProvider | None = None,
    places_provider: PlacesProvider | None = None,
) -> FastAPI:
    configured = settings or Settings.from_env(load_file=False)
    engine = build_engine(database_url or configured.database_url or DEFAULT_DATABASE_URL)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine
        app.state.seed_on_startup = seed_on_startup
        if engine.url.database and engine.url.database != ":memory:":
            database_path = Path(engine.url.database)
            database_kind = (
                inspect_database(database_path).kind if database_path.exists() else "empty"
            )
            if database_kind in {"v1", "v2_geo_pending"}:
                raise RuntimeError(
                    "La base requiere una migración manual; ejecutá backend.migrations status."
                )
        SQLModel.metadata.create_all(engine)
        # V2 no crea datos personales sin un propietario autenticado.
        yield

    application = FastAPI(title="Coffee Atlas API", lifespan=lifespan)
    application.state.engine = engine
    application.state.settings = configured
    application.state.cookie_secure = configured.app_env != "development"
    application.state.auth_provider = auth_provider or Auth0Provider(configured)
    application.state.places_provider = places_provider or GooglePlacesProvider(
        configured.google_maps_server_key
    )
    application.state.upload_dir = Path(configured.upload_dir) if configured.upload_dir else (
        Path(__file__).resolve().parent.parent / "data" / "uploads"
    )
    allowed_host = urlparse(configured.app_base_url).hostname
    if not allowed_host:
        raise ValueError("APP_BASE_URL no contiene un host válido.")
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=[allowed_host])

    @application.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    application.include_router(auth_router)
    application.include_router(session_router)
    application.include_router(profile_router)
    application.include_router(config_router)
    application.include_router(recommendation_router)
    application.include_router(visit_router)
    application.include_router(photo_router)
    application.include_router(dashboard_router)
    application.include_router(router)
    application.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return application


def create_production_app() -> FastAPI:
    """Factory de ejecución real; es el único punto que carga el archivo .env."""
    settings = Settings.from_env(load_file=True).validated(require_auth0=True)
    return create_app(settings=settings)
