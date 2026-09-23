from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "openapi.yaml"


def generated_schema() -> dict:
    schema = app.openapi()
    schema["openapi"] = "3.1.0"
    return schema


def main() -> None:
    parser = argparse.ArgumentParser(description="Write or verify the versioned OpenAPI contract")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = generated_schema()
    if args.write:
        CONTRACT.write_text(
            yaml.safe_dump(generated, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        print(f"Wrote {CONTRACT}")
        return
    if not CONTRACT.exists() or yaml.safe_load(CONTRACT.read_text(encoding="utf-8")) != generated:
        raise SystemExit("openapi.yaml is not synchronized with the FastAPI application")
    print("openapi.yaml is synchronized with the FastAPI application")


if __name__ == "__main__":
    main()
