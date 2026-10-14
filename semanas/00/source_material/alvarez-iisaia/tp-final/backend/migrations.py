import argparse
import os
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 2


class MigrationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DatabaseStatus:
    kind: str
    message: str


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def integrity_check(path: Path) -> str:
    if not path.is_file():
        raise MigrationError(f"No existe la base: {path}")
    with _connect(path) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        raise MigrationError("La comprobación de integridad SQLite falló.")
    return result


def inspect_database(path: Path) -> DatabaseStatus:
    if not path.exists() or path.stat().st_size == 0:
        return DatabaseStatus("empty", "Base inexistente o vacía; se puede crear V2.")
    integrity_check(path)
    with _connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "schema_migrations" in tables:
            row = connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
            ).fetchone()
            if row and row[0] == SCHEMA_VERSION:
                return DatabaseStatus("v2", "La base ya está actualizada a V2.")
        if "cafes" in tables:
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(cafes)")
            }
            if "owner_id" in columns:
                return DatabaseStatus("v2", "La base usa el esquema V2.")
            if {"visit_status", "coffee_rating"}.issubset(columns):
                return DatabaseStatus("v1", "La base usa el esquema V1 y requiere migración manual.")
        return DatabaseStatus("unknown", "El esquema SQLite no es reconocido.")


def create_backup(database: Path, output: Path) -> Path:
    if output.exists():
        raise MigrationError(f"El backup ya existe: {output}")
    integrity_check(database)
    output.parent.mkdir(parents=True, exist_ok=True)
    with _connect(database) as source, sqlite3.connect(output) as destination:
        source.backup(destination)
    integrity_check(output)
    return output


def _create_v2_tables(connection: sqlite3.Connection) -> None:
    script = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            auth0_sub VARCHAR(255) NOT NULL UNIQUE,
            identity_status VARCHAR(20) NOT NULL,
            email VARCHAR(320),
            display_name VARCHAR(100) NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            CONSTRAINT ck_users_identity_status
              CHECK (identity_status IN ('PENDING_LOGIN', 'ACTIVE'))
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY,
            token_hash VARCHAR(64) NOT NULL UNIQUE,
            csrf_hash VARCHAR(64) NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id),
            created_at DATETIME NOT NULL,
            last_seen_at DATETIME NOT NULL,
            idle_expires_at DATETIME NOT NULL,
            absolute_expires_at DATETIME NOT NULL
        );
        CREATE TABLE cafes (
            id INTEGER PRIMARY KEY,
            owner_id INTEGER NOT NULL REFERENCES users(id),
            name VARCHAR(100) NOT NULL,
            neighborhood VARCHAR(80) NOT NULL,
            description VARCHAR(600) NOT NULL,
            image_url VARCHAR(2048),
            is_favorite BOOLEAN NOT NULL DEFAULT 0,
            place_id VARCHAR(255),
            selected_address VARCHAR(500),
            location_status VARCHAR(20) NOT NULL DEFAULT 'NEEDS_LOCATION',
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            UNIQUE(owner_id, place_id)
        );
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY,
            owner_id INTEGER NOT NULL REFERENCES users(id),
            cafe_id INTEGER NOT NULL REFERENCES cafes(id),
            visited_at DATETIME NOT NULL,
            note VARCHAR(1000),
            coffee_rating INTEGER CHECK(coffee_rating IS NULL OR coffee_rating BETWEEN 1 AND 5),
            food_rating INTEGER CHECK(food_rating IS NULL OR food_rating BETWEEN 1 AND 5),
            ambience_rating INTEGER CHECK(ambience_rating IS NULL OR ambience_rating BETWEEN 1 AND 5),
            service_rating INTEGER CHECK(service_rating IS NULL OR service_rating BETWEEN 1 AND 5),
            date_is_estimated BOOLEAN NOT NULL DEFAULT 0,
            migration_key VARCHAR(255) UNIQUE,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        );
        CREATE TABLE IF NOT EXISTS migration_imports (
            entity_type VARCHAR(20) NOT NULL,
            legacy_id INTEGER NOT NULL,
            new_id INTEGER NOT NULL,
            PRIMARY KEY(entity_type, legacy_id)
        );
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at DATETIME NOT NULL
        );
        """
    for statement in script.split(";"):
        if statement.strip():
            connection.execute(statement)


def upgrade_database(
    database: Path,
    backup: Path,
    owner_sub: str,
    *,
    fail_after_cafes: bool = False,
) -> str:
    current = inspect_database(database)
    if current.kind == "v2":
        return "La base ya está actualizada; no se realizó ninguna escritura."
    if current.kind != "v1":
        raise MigrationError(current.message)
    if not owner_sub.strip():
        raise MigrationError("LEGACY_OWNER_AUTH0_SUB es obligatorio.")
    integrity_check(backup)
    now = datetime.now(timezone.utc).isoformat()
    connection = _connect(database)
    try:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("ALTER TABLE cafes RENAME TO legacy_cafes_v1")
        _create_v2_tables(connection)
        owner = connection.execute(
            "SELECT id FROM users WHERE auth0_sub = ?", (owner_sub.strip(),)
        ).fetchone()
        if owner is None:
            cursor = connection.execute(
                """INSERT INTO users
                   (auth0_sub, identity_status, email, display_name, created_at, updated_at)
                   VALUES (?, 'PENDING_LOGIN', NULL, 'Usuario', ?, ?)""",
                (owner_sub.strip(), now, now),
            )
            owner_id = cursor.lastrowid
        else:
            owner_id = owner["id"]
        legacy_rows = connection.execute(
            "SELECT * FROM legacy_cafes_v1 ORDER BY id"
        ).fetchall()
        for row in legacy_rows:
            connection.execute(
                """INSERT INTO cafes
                   (id, owner_id, name, neighborhood, description, image_url,
                    is_favorite, place_id, selected_address, location_status,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, 'NEEDS_LOCATION', ?, ?)""",
                (
                    row["id"], owner_id, row["name"], row["neighborhood"],
                    row["description"], row["image_url"], row["is_favorite"],
                    row["created_at"], row["updated_at"],
                ),
            )
            connection.execute(
                "INSERT INTO migration_imports VALUES ('cafe', ?, ?)",
                (row["id"], row["id"]),
            )
            if row["visit_status"] == "VISITED":
                visit = connection.execute(
                    """INSERT INTO visits
                       (owner_id, cafe_id, visited_at, note, coffee_rating,
                        food_rating, ambience_rating, service_rating,
                        date_is_estimated, migration_key, created_at, updated_at)
                       VALUES (?, ?, ?, NULL, ?, ?, ?, ?, 1, ?, ?, ?)""",
                    (
                        owner_id, row["id"], row["created_at"],
                        row["coffee_rating"], row["food_rating"],
                        row["ambience_rating"], row["service_rating"],
                        f"v1-visit-{row['id']}", now, now,
                    ),
                )
                connection.execute(
                    "INSERT INTO migration_imports VALUES ('visit', ?, ?)",
                    (row["id"], visit.lastrowid),
                )
        if fail_after_cafes:
            raise MigrationError("Fallo simulado para comprobar rollback.")
        connection.execute("DROP TABLE legacy_cafes_v1")
        connection.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, now),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    verify_database(database)
    return f"Migración V2 completa: {len(legacy_rows)} cafeterías importadas."


def verify_database(database: Path) -> dict[str, int | str]:
    integrity_check(database)
    status = inspect_database(database)
    if status.kind != "v2":
        raise MigrationError("La base no quedó en esquema V2.")
    with _connect(database) as connection:
        cafes = connection.execute(
            "SELECT COUNT(*) FROM migration_imports WHERE entity_type='cafe'"
        ).fetchone()[0]
        visits = connection.execute(
            "SELECT COUNT(*) FROM migration_imports WHERE entity_type='visit'"
        ).fetchone()[0]
        orphan_cafes = connection.execute(
            "SELECT COUNT(*) FROM cafes c LEFT JOIN users u ON u.id=c.owner_id WHERE u.id IS NULL"
        ).fetchone()[0]
        orphan_visits = connection.execute(
            """SELECT COUNT(*) FROM visits v
               LEFT JOIN cafes c ON c.id=v.cafe_id
               LEFT JOIN users u ON u.id=v.owner_id
               WHERE c.id IS NULL OR u.id IS NULL OR c.owner_id != v.owner_id"""
        ).fetchone()[0]
    if orphan_cafes or orphan_visits:
        raise MigrationError("La verificación encontró relaciones huérfanas.")
    return {"integrity": "ok", "cafes_imported": cafes, "visits_imported": visits}


def restore_database(database: Path, source: Path) -> Path:
    integrity_check(source)
    rescue = database.with_suffix(database.suffix + ".before-restore")
    if database.exists():
        if rescue.exists():
            raise MigrationError(f"El backup de rescate ya existe: {rescue}")
        create_backup(database, rescue)
    temporary = database.with_suffix(database.suffix + ".restoring")
    shutil.copy2(source, temporary)
    integrity_check(temporary)
    os.replace(temporary, database)
    return rescue


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Migraciones manuales de Coffee Atlas")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("status", "verify"):
        child = subparsers.add_parser(command)
        child.add_argument("--database", type=Path, required=True)
    backup = subparsers.add_parser("backup")
    backup.add_argument("--database", type=Path, required=True)
    backup.add_argument("--output", type=Path, required=True)
    upgrade = subparsers.add_parser("upgrade")
    upgrade.add_argument("--database", type=Path, required=True)
    upgrade.add_argument("--backup", type=Path, required=True)
    restore = subparsers.add_parser("restore")
    restore.add_argument("--database", type=Path, required=True)
    restore.add_argument("--from", dest="source", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "status":
            result = inspect_database(args.database).message
        elif args.command == "backup":
            result = f"Backup íntegro creado en {create_backup(args.database, args.output)}"
        elif args.command == "upgrade":
            result = upgrade_database(
                args.database,
                args.backup,
                os.environ.get("LEGACY_OWNER_AUTH0_SUB", ""),
            )
        elif args.command == "verify":
            result = str(verify_database(args.database))
        else:
            result = f"Restauración completa. Backup de rescate: {restore_database(args.database, args.source)}"
    except MigrationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
