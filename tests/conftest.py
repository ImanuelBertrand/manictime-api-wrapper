import os

import pytest

# Set required env vars before importing the app
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("MT_SERVER_URL", "http://localhost")
os.environ.setdefault("MT_USERNAME", "test")
os.environ.setdefault("MT_PASSWORD", "test")
os.environ.setdefault("API_KEY", "test-api-key")


from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()
