import logging
from http import HTTPStatus

import httpx

MT_ACCEPT_HEADER = "application/vnd.manictime.v3+json"

_logger = logging.getLogger(__name__)


class ManicTimeAPIError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"ManicTime API error {status_code}: {detail}")


class ManicTimeClient:
    def __init__(self, server_url: str, username: str, password: str) -> None:
        self._server_url = server_url.rstrip("/")
        self._username = username
        self._password = password
        self._token: str | None = None
        self._token_endpoint: str | None = None
        self._http = httpx.Client(timeout=30.0)

    def check_health(self) -> bool:
        try:
            self._request("/api/timelines")
        except ManicTimeAPIError, httpx.HTTPError:
            return False
        return True

    def get_timelines(self) -> dict:
        return self._request("/api/timelines")

    def get_activities(self, timeline_key: str, from_time: str, to_time: str) -> dict:
        return self._request(
            f"/api/timelines/{timeline_key}/activities",
            params={"fromTime": from_time, "toTime": to_time},
        )

    def get_tag_combinations(self, *, get_all: bool = False) -> dict:
        params = {"getAll": "true"} if get_all else None
        return self._request("/api/tagcombinationlist", params=params)

    def get_screenshots(self) -> dict:
        return self._request("/api/screenshots")

    def _request(self, path: str, *, params: dict | None = None) -> dict:
        if self._token is None:
            self._authenticate()

        response = self._send(path, params=params)

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            self._authenticate()
            response = self._send(path, params=params)

        if not response.is_success:
            raise ManicTimeAPIError(response.status_code, response.text)

        return response.json()

    def _send(self, path: str, *, params: dict | None = None) -> httpx.Response:
        _logger.info("Sending request to %s%s", self._server_url, path)
        return self._http.get(
            f"{self._server_url}{path}",
            params=params,
            headers={
                "Accept": MT_ACCEPT_HEADER,
                "Authorization": f"Bearer {self._token}",
            },
        )

    def _authenticate(self) -> None:
        if self._token_endpoint is None:
            self._discover_token_endpoint()

        token_endpoint = self._token_endpoint
        if token_endpoint is None:
            msg = "Token endpoint not discovered"
            raise ManicTimeAPIError(0, msg)

        _logger.info("Authenticating with %s", token_endpoint)
        response = self._http.post(
            token_endpoint,
            data={
                "grant_type": "password",
                "username": self._username,
                "password": self._password,
            },
        )

        if not response.is_success:
            raise ManicTimeAPIError(response.status_code, "Authentication failed")

        self._token = response.json()["token"]

    def _discover_token_endpoint(self) -> None:
        url = f"{self._server_url}/api"
        _logger.info("Discovering token endpoint from %s", url)
        response = self._http.get(url, headers={"Accept": MT_ACCEPT_HEADER})

        try:
            body = response.json()
        except Exception as e:
            _logger.exception(
                "Failed to parse discovery response (status %d): %s",
                response.status_code,
                response.text,
            )
            raise ManicTimeAPIError(502, "Failed to discover API endpoints") from e

        for link in body.get("links", []):
            if link.get("rel") == "manictime/token":
                self._token_endpoint = link["href"]
                _logger.info("Discovered token endpoint: %s", self._token_endpoint)
                return

        _logger.error(
            "Token endpoint not found in discovery response (status %d): %s",
            response.status_code,
            response.text,
        )
        raise ManicTimeAPIError(502, "Token endpoint not found in API response")
