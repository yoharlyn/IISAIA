from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def _alembic(project_root: Path, db_path: Path, *args: str) -> None:
    env = os.environ | {
        "DATABASE_URL": f"sqlite:///{db_path}",
        "APP_ENV": "test",
        "SESSION_SECRET": "migration-test-secret-at-least-32-characters",
    }
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=project_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def test_migration_upgrade_constraints_and_downgrade(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    database = tmp_path / "migration.db"
    _alembic(project_root, database, "upgrade", "head")
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if not row[0].startswith("sqlite_")
        }
        assert tables == {"alembic_version", "users", "categories", "products", "implant_specs"}
        connection.execute("PRAGMA foreign_keys=ON")
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        indexes = {row[1] for row in connection.execute("PRAGMA index_list('products')")}
        assert {
            "ix_products_active_name",
            "ix_products_active_category",
            "ix_products_active_implant",
        } <= indexes
        product_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='products'"
        ).fetchone()[0]
        assert "price_cents >= 0" in product_sql
        assert "stock >= 0" in product_sql
        product_fks = connection.execute("PRAGMA foreign_key_list('products')").fetchall()
        assert any(row[2] == "categories" and row[6] == "RESTRICT" for row in product_fks)

    _alembic(project_root, database, "downgrade", "base")
    with sqlite3.connect(database) as connection:
        remaining = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if not row[0].startswith("sqlite_")
        }
        assert remaining == {"alembic_version"}
