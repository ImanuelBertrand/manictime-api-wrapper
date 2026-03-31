from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.mt_client import ManicTimeAPIError, ManicTimeClient

HOME_RESPONSE = {
    "links": [
        {"rel": "self", "href": "http://mt.example/api/"},
        {"rel": "manictime/token", "href": "http://mt.example/api/token"},
        {"rel": "manictime/timelines", "href": "http://mt.example/api/timelines"},
    ]
}

TOKEN_RESPONSE = {"token": "test-access-token"}


def make_response(status_code=200, json_data=None, text=""):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


@pytest.fixture
def client():
    with patch.object(httpx.Client, "__init__", return_value=None):
        c = ManicTimeClient("http://mt.example", "user", "pass")
        c._http = MagicMock(spec=httpx.Client)
    return c


def setup_auth(client):
    """Configure mock to handle discovery + token flow."""
    client._http.get.return_value = make_response(json_data=HOME_RESPONSE)
    client._http.post.return_value = make_response(json_data=TOKEN_RESPONSE)


class TestDiscoverTokenEndpoint:
    def test_parses_token_url_from_links(self, client):
        client._http.get.return_value = make_response(json_data=HOME_RESPONSE)
        client._discover_token_endpoint()
        assert client._token_endpoint == "http://mt.example/api/token"

    def test_raises_when_token_link_missing(self, client):
        client._http.get.return_value = make_response(
            json_data={"links": [{"rel": "self", "href": "/api"}]}
        )
        with pytest.raises(ManicTimeAPIError, match="Token endpoint not found"):
            client._discover_token_endpoint()

    def test_raises_on_non_success(self, client):
        client._http.get.return_value = make_response(status_code=500, text="error")
        with pytest.raises(ManicTimeAPIError, match="Failed to discover"):
            client._discover_token_endpoint()


class TestAuthenticate:
    def test_posts_credentials_and_stores_token(self, client):
        client._token_endpoint = "http://mt.example/api/token"
        client._http.post.return_value = make_response(json_data=TOKEN_RESPONSE)

        client._authenticate()

        assert client._token == "test-access-token"
        client._http.post.assert_called_once_with(
            "http://mt.example/api/token",
            data={
                "grant_type": "password",
                "username": "user",
                "password": "pass",
            },
        )

    def test_discovers_endpoint_if_not_set(self, client):
        client._http.get.return_value = make_response(json_data=HOME_RESPONSE)
        client._http.post.return_value = make_response(json_data=TOKEN_RESPONSE)

        client._authenticate()

        assert client._token_endpoint == "http://mt.example/api/token"
        assert client._token == "test-access-token"

    def test_raises_on_auth_failure(self, client):
        client._token_endpoint = "http://mt.example/api/token"
        client._http.post.return_value = make_response(status_code=401, text="bad")

        with pytest.raises(ManicTimeAPIError, match="Authentication failed"):
            client._authenticate()


class TestRequest:
    def test_get_timelines(self, client):
        setup_auth(client)
        timelines_data = {"timelines": [{"key": "t1"}]}

        # First call: discovery GET, then auth POST, then actual GET
        client._http.get.side_effect = [
            make_response(json_data=HOME_RESPONSE),  # discovery
            make_response(json_data=timelines_data),  # actual request
        ]
        client._http.post.return_value = make_response(json_data=TOKEN_RESPONSE)

        result = client.get_timelines()
        assert result == timelines_data

    def test_get_activities_passes_params(self, client):
        client._token = "existing-token"
        activities_data = {"entities": []}
        client._http.get.return_value = make_response(json_data=activities_data)

        result = client.get_activities("key1", "2026-03-01", "2026-03-31")

        assert result == activities_data
        call_kwargs = client._http.get.call_args
        assert call_kwargs.kwargs["params"] == {
            "fromTime": "2026-03-01",
            "toTime": "2026-03-31",
        }

    def test_retries_on_401(self, client):
        client._token = "expired-token"
        client._token_endpoint = "http://mt.example/api/token"

        client._http.get.side_effect = [
            make_response(status_code=401),  # first attempt
            make_response(json_data={"ok": True}),  # retry after re-auth
        ]
        client._http.post.return_value = make_response(json_data=TOKEN_RESPONSE)

        result = client._request("/api/test")
        assert result == {"ok": True}
        assert client._token == "test-access-token"

    def test_raises_on_non_success(self, client):
        client._token = "valid-token"
        client._http.get.return_value = make_response(status_code=404, text="Not Found")

        with pytest.raises(ManicTimeAPIError) as exc_info:
            client._request("/api/missing")
        assert exc_info.value.status_code == 404

    def test_get_tag_combinations_with_get_all(self, client):
        client._token = "valid-token"
        client._http.get.return_value = make_response(json_data={"tagCombinations": []})

        client.get_tag_combinations(get_all=True)

        call_kwargs = client._http.get.call_args
        assert call_kwargs.kwargs["params"] == {"getAll": "true"}

    def test_get_tag_combinations_default(self, client):
        client._token = "valid-token"
        client._http.get.return_value = make_response(json_data={"tagCombinations": []})

        client.get_tag_combinations()

        call_kwargs = client._http.get.call_args
        assert call_kwargs.kwargs["params"] is None
