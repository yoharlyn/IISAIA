import pytest

from backend.config import CANONICAL_BASE_URL, ConfigurationError, Settings


def valid_settings(**overrides) -> Settings:
    values = {
        "app_base_url": CANONICAL_BASE_URL,
        "session_secret": "s" * 32,
        "auth0_domain": "coffee-atlas.example.auth0.com",
        "auth0_client_id": "client-id",
        "auth0_client_secret": "client-secret",
    }
    values.update(overrides)
    return Settings(**values)


def test_accepts_only_the_canonical_development_origin():
    assert valid_settings().validated().app_base_url == "http://127.0.0.1:8000"

    with pytest.raises(ConfigurationError, match="APP_BASE_URL"):
        valid_settings(app_base_url="http://localhost:8000").validated()


def test_real_auth0_configuration_reports_missing_variable_names_only():
    with pytest.raises(ConfigurationError) as error:
        Settings(session_secret="s" * 32).validated(require_auth0=True)

    message = str(error.value)
    assert "AUTH0_DOMAIN" in message
    assert "AUTH0_CLIENT_SECRET" in message
    assert "s" * 32 not in message


def test_rejects_short_session_secrets():
    with pytest.raises(ConfigurationError, match="al menos 32"):
        valid_settings(session_secret="short").validated()


def test_public_summary_never_contains_secret_values():
    settings = valid_settings()
    summary = settings.validated().public_summary()

    assert summary == {
        "app_base_url": CANONICAL_BASE_URL,
        "app_env": "development",
        "auth0_configured": "true",
    }
    assert settings.auth0_client_secret not in repr(summary)
