import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def database_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def app(database_url):
    return create_app(database_url=database_url)


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client

