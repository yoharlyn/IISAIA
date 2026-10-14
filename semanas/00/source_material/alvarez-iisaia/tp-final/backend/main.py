from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel

from backend.db import DEFAULT_DATABASE_URL, build_engine
from backend.seed import seed_cafes

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app(
    database_url: str | None = None,
    *,
    seed_on_startup: bool = True,
) -> FastAPI:
    engine = build_engine(database_url or DEFAULT_DATABASE_URL)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine
        app.state.seed_on_startup = seed_on_startup
        SQLModel.metadata.create_all(engine)
        if seed_on_startup:
            seed_cafes(engine)
        yield

    application = FastAPI(title="Coffee Atlas API", lifespan=lifespan)
    application.state.engine = engine
    application.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return application


app = create_app()
