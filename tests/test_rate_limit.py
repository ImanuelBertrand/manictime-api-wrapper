API_HEADERS = {"X-API-Key": "test-api-key"}


def test_rate_limit_returns_429(app, mock_mt_client):
    mock_mt_client.get_timelines.return_value = {"timelines": []}
    test_client = app.test_client()

    for _ in range(60):
        response = test_client.get("/api/timelines", headers=API_HEADERS)
        assert response.status_code == 200

    response = test_client.get("/api/timelines", headers=API_HEADERS)
    assert response.status_code == 429
