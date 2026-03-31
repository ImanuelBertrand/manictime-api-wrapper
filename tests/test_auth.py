def test_missing_api_key_returns_401(client):
    response = client.get("/api/timelines")
    assert response.status_code == 401


def test_wrong_api_key_returns_401(client):
    response = client.get("/api/timelines", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


def test_empty_api_key_returns_401(client):
    response = client.get("/api/timelines", headers={"X-API-Key": ""})
    assert response.status_code == 401


def test_health_without_api_key(client):
    response = client.get("/health")
    assert response.status_code == 200
