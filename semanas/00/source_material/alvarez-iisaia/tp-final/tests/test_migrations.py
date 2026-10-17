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
    integrity_check,
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


def create_v3(path: Path) -> None:
    with sqlite3.connect(path) as db:
        db.executescript(
            """
            PRAGMA foreign_keys=ON;
            CREATE TABLE users (
              id INTEGER PRIMARY KEY, auth0_sub VARCHAR(255) NOT NULL UNIQUE,
              identity_status VARCHAR(20) NOT NULL, email VARCHAR(320),
              display_name VARCHAR(100) NOT NULL, home_place_id VARCHAR(255),
              home_selected_address VARCHAR(500), home_latitude FLOAT,
              home_longitude FLOAT, home_location_fetched_at DATETIME,
              home_location_expires_at DATETIME, home_neighborhood VARCHAR(80),
              home_caba_verified_at DATETIME, home_caba_polygon_version VARCHAR(80),
              created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL,
              CONSTRAINT ck_users_identity_status
                CHECK (identity_status IN ('PENDING_LOGIN', 'ACTIVE'))
            );
            CREATE TABLE cafes (
              id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id),
              name VARCHAR(100) NOT NULL, neighborhood VARCHAR(80) NOT NULL,
              description VARCHAR(600) NOT NULL, image_url VARCHAR(2048),
              is_favorite BOOLEAN NOT NULL, place_id VARCHAR(255),
              place_id_checked_at DATETIME, selected_address VARCHAR(500),
              latitude FLOAT, longitude FLOAT, location_fetched_at DATETIME,
              location_expires_at DATETIME, caba_verified_at DATETIME,
              caba_polygon_version VARCHAR(80), location_status VARCHAR(14) NOT NULL,
              created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL,
              CONSTRAINT ck_cafes_name CHECK (length(trim(name)) BETWEEN 1 AND 100),
              CONSTRAINT ck_cafes_neighborhood
                CHECK (length(trim(neighborhood)) BETWEEN 1 AND 80),
              CONSTRAINT ck_cafes_description
                CHECK (length(trim(description)) BETWEEN 1 AND 600),
              CONSTRAINT ck_cafes_location_status
                CHECK (location_status IN ('VERIFIED', 'NEEDS_LOCATION', 'EXPIRED'))
            );
            CREATE INDEX ix_cafes_is_favorite ON cafes (is_favorite);
            CREATE INDEX ix_cafes_name ON cafes (name);
            CREATE INDEX ix_cafes_neighborhood ON cafes (neighborhood);
            CREATE INDEX ix_cafes_owner_id ON cafes (owner_id);
            CREATE UNIQUE INDEX ix_cafes_owner_place ON cafes (owner_id, place_id);
            CREATE TABLE visits (
              id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id),
              cafe_id INTEGER NOT NULL REFERENCES cafes(id), visited_at DATETIME NOT NULL,
              note VARCHAR(1000), coffee_rating INTEGER, food_rating INTEGER,
              ambience_rating INTEGER, service_rating INTEGER,
              date_is_estimated BOOLEAN NOT NULL, migration_key VARCHAR(255) UNIQUE,
              created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL
            );
            CREATE TABLE visit_photos (
              id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id),
              visit_id INTEGER NOT NULL REFERENCES visits(id), internal_name VARCHAR(80) UNIQUE,
              mime_type VARCHAR(40) NOT NULL, size_bytes INTEGER NOT NULL,
              width INTEGER NOT NULL, height INTEGER NOT NULL, sha256 VARCHAR(64) NOT NULL,
              caption VARCHAR(200) NOT NULL, created_at DATETIME NOT NULL
            );
            CREATE TABLE migration_imports (
              entity_type VARCHAR(20) NOT NULL, legacy_id INTEGER NOT NULL,
              new_id INTEGER NOT NULL, PRIMARY KEY(entity_type, legacy_id)
            );
            CREATE TABLE schema_migrations (
              version INTEGER PRIMARY KEY, applied_at DATETIME NOT NULL
            );
            INSERT INTO users
              (id, auth0_sub, identity_status, display_name, created_at, updated_at)
              VALUES (5, 'auth0|v3-owner', 'ACTIVE', 'Dueña V3', 'now', 'now');
            INSERT INTO cafes
              (id, owner_id, name, neighborhood, description, image_url, is_favorite,
               place_id, place_id_checked_at, selected_address, latitude, longitude,
               location_fetched_at, location_expires_at, caba_verified_at,
               caba_polygon_version, location_status, created_at, updated_at)
              VALUES
              (7, 5, 'Café V3', 'San Nicolás', 'Descripción existente', NULL, 1,
               'place-v3', 'checked', 'Av. Corrientes 1000, CABA', -34.6037, -58.3816,
               'fetched', 'expires', 'verified', 'caba-48-v1', 'VERIFIED', 'created', 'updated');
            INSERT INTO visits
              (id, owner_id, cafe_id, visited_at, note, coffee_rating, food_rating,
               ambience_rating, service_rating, date_is_estimated, migration_key,
               created_at, updated_at)
              VALUES (11, 5, 7, 'visited', 'Nota', 5, 4, 4, 5, 0, 'visit-v3', 'created', 'updated');
            INSERT INTO visit_photos
              (id, owner_id, visit_id, internal_name, mime_type, size_bytes,
               width, height, sha256, caption, created_at)
              VALUES (13, 5, 11, 'photo-v3.jpg', 'image/jpeg', 100, 10, 10,
                      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                      'Foto V3', 'created');
            INSERT INTO schema_migrations VALUES (3, 'now');
            """
        )


def cafe_indexes(database: Path) -> list[tuple[str, str]]:
    with sqlite3.connect(database) as db:
        return db.execute(
            """SELECT name, sql FROM sqlite_master
               WHERE type='index' AND tbl_name='cafes' AND sql IS NOT NULL
               ORDER BY name"""
        ).fetchall()


def test_status_backup_upgrade_verify_and_idempotence(tmp_path):
    database = tmp_path / "atlas.db"
    backup = tmp_path / "backups" / "atlas-v1.db"
    create_v1(database)

    assert inspect_database(database).kind == "v1"
    assert create_backup(database, backup) == backup
    assert upgrade_database(database, backup, "auth0|owner").startswith("Migración V4")
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
    assert inspect_database(rescue).kind == "v4"


def test_startup_refuses_v1_without_modifying_it(tmp_path):
    database = tmp_path / "atlas.db"
    create_v1(database, rows=1)
    before = database.read_bytes()
    app = create_app(database_url=f"sqlite:///{database}", seed_on_startup=False)

    with pytest.raises(RuntimeError, match="migración manual"):
        with TestClient(app):
            pass

    assert database.read_bytes() == before


def test_geo_schema_upgrade_is_explicit_transactional_and_idempotent(tmp_path):
    database = tmp_path / "atlas.db"
    v1_backup = tmp_path / "atlas-v1.db"
    phase1_backup = tmp_path / "atlas-phase1.db"
    create_v1(database, rows=0)
    create_backup(database, v1_backup)
    upgrade_database(database, v1_backup, "auth0|owner")
    with sqlite3.connect(database) as db:
        db.execute("DELETE FROM schema_migrations")
        for table in ("place_discoveries",):
            db.execute(f"DROP TABLE {table}")
        # SQLite no permite eliminar columnas de forma portable en todas las
        # versiones soportadas; recreamos sólo cafes con el esquema de Fase 1.
        db.executescript(
            """
            ALTER TABLE cafes RENAME TO cafes_current;
            CREATE TABLE cafes (
              id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id),
              name VARCHAR(100) NOT NULL, neighborhood VARCHAR(80) NOT NULL,
              description VARCHAR(600) NOT NULL, image_url VARCHAR(2048),
              is_favorite BOOLEAN NOT NULL DEFAULT 0, place_id VARCHAR(255),
              selected_address VARCHAR(500), location_status VARCHAR(20) NOT NULL,
              created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL,
              UNIQUE(owner_id, place_id));
            INSERT INTO cafes
              (id, owner_id, name, neighborhood, description, image_url,
               is_favorite, place_id, selected_address, location_status,
               created_at, updated_at)
            SELECT id, owner_id, name, neighborhood, description, image_url,
                   is_favorite, place_id, selected_address, location_status,
                   created_at, updated_at FROM cafes_current;
            DROP TABLE cafes_current;
            INSERT INTO schema_migrations(version, applied_at) VALUES (2, 'now');
            """
        )
    create_backup(database, phase1_backup)

    assert inspect_database(database).kind == "v2_geo_pending"
    before = database.read_bytes()
    app = create_app(database_url=f"sqlite:///{database}", seed_on_startup=False)
    with pytest.raises(RuntimeError, match="migración manual"):
        with TestClient(app):
            pass
    assert database.read_bytes() == before

    assert "geográfica" in upgrade_database(database, phase1_backup, "auth0|owner")
    assert inspect_database(database).kind == "v4"
    after = database.read_bytes()
    assert "ya está actualizada" in upgrade_database(
        database, phase1_backup, "auth0|owner"
    )
    assert database.read_bytes() == after


def test_v3_to_v4_preserves_schema_rows_and_relations(tmp_path):
    database = tmp_path / "v3" / "atlas.db"
    database.parent.mkdir()
    backup = tmp_path / "backups" / "atlas-v3.db"
    create_v3(database)
    indexes_before = cafe_indexes(database)
    with sqlite3.connect(database) as db:
        cafes_before = db.execute("SELECT * FROM cafes ORDER BY id").fetchall()
        visits_before = db.execute("SELECT * FROM visits ORDER BY id").fetchall()
        photos_before = db.execute("SELECT * FROM visit_photos ORDER BY id").fetchall()

    assert database.is_relative_to(tmp_path)
    assert backup.is_relative_to(tmp_path)
    assert inspect_database(database).kind == "v3_pending"
    assert create_backup(database, backup) == backup
    assert "Migración V4 completa" in upgrade_database(database, backup, "")

    assert inspect_database(database).kind == "v4"
    assert integrity_check(database) == "ok"
    assert verify_database(database) == {
        "integrity": "ok",
        "cafes_imported": 0,
        "visits_imported": 0,
    }
    assert cafe_indexes(database) == indexes_before
    with sqlite3.connect(database) as db:
        db.execute("PRAGMA foreign_keys=ON")
        description = next(
            row for row in db.execute("PRAGMA table_info(cafes)")
            if row[1] == "description"
        )
        assert description[3] == 0
        assert "description IS NULL OR" in db.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='cafes'"
        ).fetchone()[0]
        assert db.execute("SELECT * FROM cafes ORDER BY id").fetchall() == cafes_before
        assert db.execute("SELECT * FROM visits ORDER BY id").fetchall() == visits_before
        assert db.execute("SELECT * FROM visit_photos ORDER BY id").fetchall() == photos_before
        assert db.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall() == [(3,), (4,)]
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        db.execute(
            """INSERT INTO cafes
               (id, owner_id, name, neighborhood, description, is_favorite,
                location_status, created_at, updated_at)
               VALUES (8, 5, 'Sin descripción', 'Boedo', NULL, 0,
                       'NEEDS_LOCATION', 'created', 'updated')"""
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """INSERT INTO cafes
                   (id, owner_id, name, neighborhood, is_favorite, place_id,
                    location_status, created_at, updated_at)
                   VALUES (9, 5, 'Duplicada', 'Boedo', 0, 'place-v3',
                           'NEEDS_LOCATION', 'created', 'updated')"""
            )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """INSERT INTO cafes
                   (id, owner_id, name, neighborhood, description, is_favorite,
                    location_status, created_at, updated_at)
                   VALUES (10, 5, 'Vacía', 'Boedo', '   ', 0,
                           'NEEDS_LOCATION', 'created', 'updated')"""
            )

    before_idempotent = database.read_bytes()
    assert "ya está actualizada" in upgrade_database(database, backup, "")
    assert database.read_bytes() == before_idempotent


def test_v3_to_v4_failure_rolls_back_completely(tmp_path):
    database = tmp_path / "atlas-v3.db"
    backup = tmp_path / "atlas-v3-backup.db"
    create_v3(database)
    create_backup(database, backup)
    indexes_before = cafe_indexes(database)

    with pytest.raises(MigrationError, match="Fallo simulado"):
        upgrade_database(database, backup, "", fail_after_cafes=True)

    assert inspect_database(database).kind == "v3_pending"
    assert cafe_indexes(database) == indexes_before
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT id, description FROM cafes").fetchall() == [
            (7, "Descripción existente")
        ]
        assert db.execute("SELECT version FROM schema_migrations").fetchall() == [(3,)]
        assert db.execute("SELECT name FROM sqlite_master WHERE name='cafes_v4'").fetchall() == []


def test_startup_refuses_v3_without_modifying_it(tmp_path):
    database = tmp_path / "atlas-v3.db"
    create_v3(database)
    before = database.read_bytes()
    app = create_app(database_url=f"sqlite:///{database}", seed_on_startup=False)

    with pytest.raises(RuntimeError, match="migración manual"):
        with TestClient(app):
            pass

    assert database.read_bytes() == before


def test_v3_backup_upgrade_and_restore_stay_inside_tmp_path(tmp_path):
    database = tmp_path / "atlas-v3.db"
    backup = tmp_path / "atlas-v3-backup.db"
    create_v3(database)
    assert database.is_relative_to(tmp_path)
    assert backup.is_relative_to(tmp_path)

    create_backup(database, backup)
    upgrade_database(database, backup, "")
    rescue = restore_database(database, backup)

    assert rescue.is_relative_to(tmp_path)
    assert inspect_database(database).kind == "v3_pending"
    assert inspect_database(rescue).kind == "v4"
