import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.auth import AuthIdentity
from backend.config import Settings
from backend.main import create_app
from backend.migrations import (
    MigrationError,
    create_backup,
    inspect_database,
    restore_database,
    upgrade_database,
    verify_database,
)


def create_v1(path: Path, *, rows: int = 7) -> None:
    with sqlite3.connect(path) as db:
        db.executescript(
            """
            CREATE TABLE cafes (
              id INTEGER PRIMARY KEY, name TEXT NOT NULL, neighborhood TEXT NOT NULL,
              description TEXT NOT NULL, image_url TEXT, visit_status TEXT NOT NULL,
              is_favorite BOOLEAN NOT NULL, coffee_rating INTEGER, food_rating INTEGER,
              ambience_rating INTEGER, service_rating INTEGER,
              created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
            );
            """
        )
        for cafe_id in range(1, rows + 1):
            visited = cafe_id <= 4
            db.execute(
                "INSERT INTO cafes VALUES (?, ?, 'Palermo', 'Descripción', NULL, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    cafe_id, f"Café {cafe_id}", "VISITED" if visited else "PENDING",
                    cafe_id % 2, 5 if visited else None, 4 if visited else None,
                    4 if visited else None, 5 if visited else None,
                    "2025-01-01T00:00:00+00:00", "2025-01-01T00:00:00+00:00",
                ),
            )


def test_status_backup_upgrade_verify_and_idempotence(tmp_path):
    database = tmp_path / "atlas.db"
    backup = tmp_path / "backups" / "atlas-v1.db"
    create_v1(database)

    assert inspect_database(database).kind == "v1"
    assert create_backup(database, backup) == backup
    assert upgrade_database(database, backup, "auth0|owner").startswith("Migración V2")
    assert verify_database(database) == {
        "integrity": "ok",
        "cafes_imported": 7,
        "visits_imported": 4,
    }
    before = database.read_bytes()
    assert "ya está actualizada" in upgrade_database(database, backup, "auth0|owner")
    assert database.read_bytes() == before


def test_partial_failure_rolls_back_every_change(tmp_path):
    database = tmp_path / "atlas.db"
    backup = tmp_path / "atlas-v1.db"
    create_v1(database)
    create_backup(database, backup)

    with pytest.raises(MigrationError, match="Fallo simulado"):
        upgrade_database(database, backup, "auth0|owner", fail_after_cafes=True)

    assert inspect_database(database).kind == "v1"
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT COUNT(*) FROM cafes").fetchone()[0] == 7


def test_migration_creates_pending_placeholder_activated_on_first_login(tmp_path):
    database = tmp_path / "atlas.db"
    backup = tmp_path / "atlas-v1.db"
    create_v1(database)
    create_backup(database, backup)
    upgrade_database(database, backup, "auth0|owner")
    with sqlite3.connect(database) as db:
        assert db.execute(
            "SELECT identity_status FROM users WHERE auth0_sub='auth0|owner'"
        ).fetchone()[0] == "PENDING_LOGIN"

    class Provider:
        def authorization_url(self, *, state, nonce, screen_hint=None):
            return f"https://identity.test/?state={state}"
        async def exchange_code(self, *, code, nonce):
            return AuthIdentity("auth0|owner", "owner@example.test", "Propietaria")
        def logout_url(self):
            return "https://identity.test/logout"

    app = create_app(
        database_url=f"sqlite:///{database}", seed_on_startup=False,
        settings=Settings(session_secret="m" * 32).validated(), auth_provider=Provider(),
    )
    from urllib.parse import parse_qs, urlparse
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        start = client.get("/auth/login", follow_redirects=False)
        state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
        client.get("/auth/callback", params={"code": "ok", "state": state}, follow_redirects=False)
    with sqlite3.connect(database) as db:
        rows = db.execute("SELECT identity_status FROM users WHERE auth0_sub='auth0|owner'").fetchall()
        assert rows == [("ACTIVE",)]


def test_migration_reuses_preexisting_active_user(tmp_path):
    database = tmp_path / "atlas.db"
    backup = tmp_path / "atlas-v1.db"
    create_v1(database, rows=1)
    with sqlite3.connect(database) as db:
        db.execute(
            """CREATE TABLE users (
              id INTEGER PRIMARY KEY, auth0_sub TEXT UNIQUE NOT NULL,
              identity_status TEXT NOT NULL, email TEXT, display_name TEXT NOT NULL,
              created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"""
        )
        db.execute(
            "INSERT INTO users VALUES (42, 'auth0|owner', 'ACTIVE', NULL, 'Dueña', 'now', 'now')"
        )
    create_backup(database, backup)
    upgrade_database(database, backup, "auth0|owner")
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert db.execute("SELECT owner_id FROM cafes").fetchone()[0] == 42


def test_restore_is_reproducible_and_keeps_rescue_copy(tmp_path):
    database = tmp_path / "atlas.db"
    backup = tmp_path / "atlas-v1.db"
    create_v1(database, rows=1)
    create_backup(database, backup)
    upgrade_database(database, backup, "auth0|owner")

    rescue = restore_database(database, backup)

    assert rescue.exists()
    assert inspect_database(database).kind == "v1"
    assert inspect_database(rescue).kind == "v2"


def test_startup_refuses_v1_without_modifying_it(tmp_path):
    database = tmp_path / "atlas.db"
    create_v1(database, rows=1)
    before = database.read_bytes()
    app = create_app(database_url=f"sqlite:///{database}", seed_on_startup=False)

    with pytest.raises(RuntimeError, match="migración manual"):
        with TestClient(app):
            pass

    assert database.read_bytes() == before
