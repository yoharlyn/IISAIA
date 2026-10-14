from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel

from backend.db import DEFAULT_DATABASE_URL, build_engine
from backend.auth import Auth0Provider, AuthProvider
from backend.auth_routes import auth_router, session_router
from backend.config import Settings
from backend.routes import router
from backend.migrations import inspect_database

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app(
    database_url: str | None = None,
    *,
    seed_on_startup: bool = True,
    settings: Settings | None = None,
    auth_provider: AuthProvider | None = None,
) -> FastAPI:
    configured = settings or Settings.from_env()
    engine = build_engine(database_url or DEFAULT_DATABASE_URL)

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
    application.include_router(auth_router)
    application.include_router(session_router)
    application.include_router(router)
    application.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return application


app = create_app()
