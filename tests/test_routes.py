from app.mt_client import ManicTimeAPIError

API_HEADERS = {"X-API-Key": "test-api-key"}


class TestTimelines:
    def test_returns_timelines(self, client, mock_mt_client):
        mock_mt_client.get_timelines.return_value = {"timelines": [{"key": "t1"}]}
        response = client.get("/api/timelines", headers=API_HEADERS)
        assert response.status_code == 200
        assert response.json["timelines"][0]["key"] == "t1"

    def test_requires_auth(self, client):
        response = client.get("/api/timelines")
        assert response.status_code == 401


class TestActivities:
    def test_returns_activities(self, client, mock_mt_client):
        mock_mt_client.get_activities.return_value = {"entities": []}
        response = client.get(
            "/api/timelines/key1/activities?fromTime=2026-03-01&toTime=2026-03-31",
            headers=API_HEADERS,
        )
        assert response.status_code == 200
        mock_mt_client.get_activities.assert_called_once_with(
            "key1", "2026-03-01", "2026-03-31"
        )

    def test_missing_params_returns_400(self, client):
        response = client.get(
            "/api/timelines/key1/activities",
            headers=API_HEADERS,
        )
        assert response.status_code == 400

    def test_missing_to_time_returns_400(self, client):
        response = client.get(
            "/api/timelines/key1/activities?fromTime=2026-03-01",
            headers=API_HEADERS,
        )
        assert response.status_code == 400


class TestTags:
    def test_returns_tags(self, client, mock_mt_client):
        mock_mt_client.get_tag_combinations.return_value = {"tagCombinations": ["tag1"]}
        response = client.get("/api/tags", headers=API_HEADERS)
        assert response.status_code == 200
        assert response.json["tagCombinations"] == ["tag1"]

    def test_passes_get_all(self, client, mock_mt_client):
        mock_mt_client.get_tag_combinations.return_value = {"tagCombinations": []}
        client.get("/api/tags?all=true", headers=API_HEADERS)
        mock_mt_client.get_tag_combinations.assert_called_once_with(get_all=True)

    def test_default_no_get_all(self, client, mock_mt_client):
        mock_mt_client.get_tag_combinations.return_value = {"tagCombinations": []}
        client.get("/api/tags", headers=API_HEADERS)
        mock_mt_client.get_tag_combinations.assert_called_once_with(get_all=False)


class TestScreenshots:
    def test_returns_screenshots(self, client, mock_mt_client):
        mock_mt_client.get_screenshots.return_value = {"screenshots": []}
        response = client.get("/api/screenshots", headers=API_HEADERS)
        assert response.status_code == 200
        assert response.json["screenshots"] == []


class TestErrorHandling:
    def test_mt_api_error_returns_upstream_status(self, client, mock_mt_client):
        mock_mt_client.get_timelines.side_effect = ManicTimeAPIError(404, "Not Found")
        response = client.get("/api/timelines", headers=API_HEADERS)
        assert response.status_code == 404
        assert response.json["error"] == "Not Found"
