from pathlib import Path

import yaml

from backend.main import app


def test_openapi_contract_has_exact_v1_surface() -> None:
    contract_path = Path(__file__).resolve().parents[1] / "openapi.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    assert contract["openapi"] == "3.1.0"
    assert contract == app.openapi()
    assert set(contract["paths"]) == {
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/me",
        "/api/v1/products",
    }
    assert set(contract["paths"]["/api/v1/auth/login"]) == {"post"}
    assert set(contract["paths"]["/api/v1/auth/logout"]) == {"post"}
    assert set(contract["paths"]["/api/v1/auth/me"]) == {"get"}
    assert set(contract["paths"]["/api/v1/products"]) == {"get"}
