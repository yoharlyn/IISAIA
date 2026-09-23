from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from argon2 import PasswordHasher


def test_seed_is_idempotent_and_complete(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    database = tmp_path / "seed.db"
    env = os.environ | {
        "APP_ENV": "test",
        "DATABASE_URL": f"sqlite:///{database}",
        "SESSION_SECRET": "seed-test-secret-at-least-32-characters",
        "SEED_DENTIST_USERNAME": "dentista.demo",
        "SEED_DENTIST_PASSWORD": "DemoLocal123!",
    }
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=project_root,
        env=env,
        check=True,
        capture_output=True,
    )
    for _ in range(2):
        subprocess.run(
            [sys.executable, "-m", "backend.scripts.seed"],
            cwd=project_root,
            env=env,
            check=True,
            capture_output=True,
        )
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM users").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM categories").fetchone()[0] >= 3
        assert connection.execute("SELECT count(*) FROM products").fetchone()[0] >= 10
        assert connection.execute("SELECT count(*) FROM implant_specs").fetchone()[0] >= 4
        password_hash = connection.execute("SELECT password_hash FROM users").fetchone()[0]
        assert password_hash.startswith("$argon2id$")
        assert "DemoLocal123!" not in password_hash
        assert PasswordHasher().verify(password_hash, "DemoLocal123!")
