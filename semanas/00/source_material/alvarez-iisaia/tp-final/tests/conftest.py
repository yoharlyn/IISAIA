from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": "sqlite:///:memory:",
        "SESSION_SECRET": "test-session-secret-at-least-32-characters",
        "SESSION_COOKIE_SECURE": "false",
        "ALLOWED_ORIGINS": "http://testserver",
        "TRUSTED_ORIGINS": "http://testserver",
    }
)

from backend.db import get_db  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import Base, Category, ImplantSpecs, Product, User, UserRole  # noqa: E402
from backend.services.auth import hash_password  # noqa: E402
from backend.services.rate_limit import login_rate_limiter  # noqa: E402


@pytest.fixture
def db_session(tmp_path: Path) -> Session:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    now = datetime.now(UTC)
    dentist = User(
        username="dentista.demo",
        email="dentista@example.test",
        password_hash=hash_password("DemoSegura123!"),
        first_name="Marina",
        last_name="Álvarez",
        role=UserRole.DENTIST,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    other = User(
        username="admin.demo",
        email="admin@example.test",
        password_hash=hash_password("AdminSegura123!"),
        first_name="Ana",
        last_name="Admin",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    inactive = User(
        username="inactivo.demo",
        email="inactive@example.test",
        password_hash=hash_password("Inactiva123!"),
        first_name="Ivo",
        last_name="Inactivo",
        role=UserRole.DENTIST,
        is_active=False,
        created_at=now,
        updated_at=now,
    )
    category = Category(name="Implantes", is_active=True)
    other_category = Category(name="Instrumental", is_active=True)
    session.add_all([dentist, other, inactive, category, other_category])
    session.flush()
    implant = Product(
        sku="IMP-001",
        name="Implante cónico",
        description="Titanio",
        brand="NovaDent",
        category_id=category.id,
        manufacturer_name="BioImplant",
        price_cents=120000,
        stock=5,
        is_active=True,
        is_implant=True,
        created_at=now,
        updated_at=now,
    )
    implant.implant_specs = ImplantSpecs(
        diameter_mm=Decimal("3.50"),
        length_mm=Decimal("10.00"),
        connection_type="Cono Morse",
        material="Titanio",
        surface_treatment="SLA",
    )
    session.add_all(
        [
            implant,
            Product(
                sku="INS-001",
                name="Fresa piloto",
                description=None,
                brand="OralTech",
                category_id=other_category.id,
                manufacturer_name="OralTech Medical",
                price_cents=45000,
                stock=8,
                is_active=True,
                is_implant=False,
                created_at=now,
                updated_at=now,
            ),
            Product(
                sku="OLD-001",
                name="Producto oculto",
                description=None,
                brand=None,
                category_id=other_category.id,
                manufacturer_name="Legacy",
                price_cents=100,
                stock=0,
                is_active=False,
                is_implant=False,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    login_rate_limiter.clear()
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def csrf_headers() -> dict[str, str]:
    return {
        "Origin": "http://testserver",
        "X-CSRF-Protection": "1",
        "Content-Type": "application/json",
    }


@pytest.fixture
def authenticated_client(client: TestClient, csrf_headers: dict[str, str]) -> TestClient:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "dentista.demo", "password": "DemoSegura123!"},
        headers=csrf_headers,
    )
    assert response.status_code == 200
    return client
