"""Async commercetools REST client with OAuth token management."""

import asyncio
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.config.constants import OAUTH_TOKEN_PATH
from app.config.settings import Settings, get_settings
from app.models.errors import CommerceToolsError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class CommerceToolsClient:
    """Shared async client used by every commercetools tool."""

    def __init__(self, settings: Settings | None = None, http_client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings or get_settings()
        self._http_client = http_client
        self._access_token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send an authenticated GET request to the commercetools API."""

        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send an authenticated POST request to the commercetools API."""

        return await self._request("POST", path, json=json)

    async def close(self) -> None:
        """Close the underlying HTTP client if this service created it."""

        if self._http_client is not None:
            await self._http_client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an authenticated request with basic retry for transient failures."""

        token = await self._get_access_token()
        url = f"{self.settings.ctp_api_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {token}"}

        last_error: Exception | None = None
        for attempt in range(1, 3):
            started = time.perf_counter()
            try:
                client = self._client()
                response = await client.request(method, url, params=params, json=json, headers=headers)
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                logger.info("ct_api method=%s path=%s status=%s duration_ms=%s", method, path, response.status_code, elapsed_ms)
                if response.status_code >= 500 and attempt == 1:
                    continue
                if response.status_code == 404:
                    raise CommerceToolsError("RESOURCE_NOT_FOUND", "The requested commercetools resource was not found.")
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as exc:
                last_error = exc
                logger.error("ct_timeout method=%s path=%s attempt=%s", method, path, attempt)
                if attempt == 1:
                    continue
            except httpx.HTTPStatusError as exc:
                message = self._extract_error_message(exc.response)
                logger.error("ct_http_error status=%s path=%s message=%s", exc.response.status_code, path, message)
                raise CommerceToolsError("COMMERCETOOLS_API_ERROR", message) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                logger.error("ct_transport_error path=%s error=%s", path, str(exc))
                if attempt == 1:
                    continue

        raise CommerceToolsError("COMMERCETOOLS_UNAVAILABLE", "Commercetools did not respond in time.") from last_error

    async def _get_access_token(self) -> str:
        """Return a cached OAuth token, refreshing before expiry."""

        now = time.time()
        if self._access_token and now < self._token_expires_at:
            return self._access_token

        async with self._token_lock:
            now = time.time()
            if self._access_token and now < self._token_expires_at:
                return self._access_token

            if not all([self.settings.ctp_auth_url, self.settings.ctp_client_id, self.settings.ctp_client_secret]):
                raise CommerceToolsError("COMMERCETOOLS_AUTH_NOT_CONFIGURED", "Commercetools authentication is not configured.")

            url = f"{self.settings.ctp_auth_url.rstrip('/')}{OAUTH_TOKEN_PATH}"
            data = {"grant_type": "client_credentials"}
            if self.settings.ctp_scopes:
                data["scope"] = self.settings.ctp_scopes

            try:
                response = await self._client().post(
                    url,
                    data=data,
                    auth=(self.settings.ctp_client_id, self.settings.ctp_client_secret),
                )
                logger.info("ct_auth status=%s", response.status_code)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise CommerceToolsError("COMMERCETOOLS_AUTH_FAILED", "Commercetools authentication failed.") from exc
            except httpx.HTTPError as exc:
                raise CommerceToolsError("COMMERCETOOLS_AUTH_UNAVAILABLE", "Commercetools authentication service is unavailable.") from exc

            payload = response.json()
            access_token = payload.get("access_token")
            expires_in = int(payload.get("expires_in", 0))
            if not access_token or expires_in <= 0:
                raise CommerceToolsError("COMMERCETOOLS_AUTH_INVALID", "Commercetools returned an invalid token response.")

            self._access_token = access_token
            self._token_expires_at = time.time() + max(1, expires_in - self.settings.ctp_token_refresh_skew_seconds)
            return self._access_token

    def _client(self) -> httpx.AsyncClient:
        """Return a reusable async HTTP client."""

        if self._http_client is None:
            timeout = httpx.Timeout(self.settings.ctp_timeout_seconds)
            self._http_client = httpx.AsyncClient(timeout=timeout)
        return self._http_client

    @staticmethod
    def encode_path_value(value: str) -> str:
        """Encode dynamic path values without escaping commercetools path separators."""

        return quote(value, safe="")

    @staticmethod
    def _extract_error_message(response: httpx.Response) -> str:
        """Create a clean error message from a commercetools error response."""

        try:
            payload = response.json()
        except ValueError:
            return f"Commercetools request failed with status {response.status_code}."
        return payload.get("message") or f"Commercetools request failed with status {response.status_code}."
