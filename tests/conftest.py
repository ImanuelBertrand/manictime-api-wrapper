import os
from unittest.mock import MagicMock

import pytest

# Force test env vars (overrides any .env values from Docker)
os.environ["SECRET_KEY"] = "test-secret"
os.environ["MT_SERVER_URL"] = "http://localhost"
os.environ["MT_USERNAME"] = "test"
os.environ["MT_PASSWORD"] = "test"
os.environ["API_KEY"] = "test-api-key"


from app import create_app
from app.mt_client import ManicTimeClient


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def mock_mt_client(app):
    mock = MagicMock(spec=ManicTimeClient)
    app.extensions["mt_client"] = mock
    return mock


@pytest.fixture
def client(app, mock_mt_client):
    return app.test_client()
