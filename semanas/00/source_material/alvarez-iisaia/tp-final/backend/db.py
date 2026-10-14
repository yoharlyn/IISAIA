from collections.abc import Generator
from pathlib import Path

from fastapi import Request
from sqlmodel import Session, create_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data' / 'coffee_atlas.db'}"


def build_engine(database_url: str = DEFAULT_DATABASE_URL):
    """Crea un engine SQLite apto para FastAPI y TestClient."""
    return create_engine(database_url, connect_args={"check_same_thread": False})


def get_session(request: Request) -> Generator[Session, None, None]:
    with Session(request.app.state.engine) as session:
        yield session

