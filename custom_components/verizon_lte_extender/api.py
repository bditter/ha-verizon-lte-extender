"""Async API client for Askey Verizon LTE Network Extenders."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import socket
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import urljoin, urlparse

import aiohttp
from yarl import URL

from .const import REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)

_AUTH_ERROR_MARKERS = (
    "token is missing",
    "empty token",
    "wrong token",
    "session",
    "sign in",
    "login",
    "unauthorized",
    "forbidden",
)
_AUTH_REDACTED_VALUE = "will display the data after login"
_AUTH_REQUIRED_STATUS_FIELDS = (
    "operationMode",
    "bhIpv4Addr",
    "macAddress",
    "SWver",
    "serial",
)


class VerizonLteExtenderError(Exception):
    """Base API error."""


class VerizonLteExtenderConnectionError(VerizonLteExtenderError):
    """The extender could not be reached."""


class VerizonLteExtenderSslError(VerizonLteExtenderConnectionError):
    """The extender certificate could not be verified."""


class VerizonLteExtenderTimeoutError(VerizonLteExtenderConnectionError):
    """The extender did not respond before the timeout."""


class VerizonLteExtenderDnsError(VerizonLteExtenderConnectionError):
    """The extender hostname could not be resolved."""


class VerizonLteExtenderNetworkError(VerizonLteExtenderConnectionError):
    """The TCP connection to the extender failed."""


class VerizonLteExtenderAuthError(VerizonLteExtenderError):
    """Authentication failed."""


class VerizonLteExtenderResponseError(VerizonLteExtenderError):
    """The extender returned an invalid response."""


def normalize_base_url(host: str) -> str:
    """Normalize a user-supplied host or base URL."""
    value = host.strip().rstrip("/")
    if not value:
        raise ValueError("Host cannot be empty")
    if "://" not in value:
        value = f"https://{value}"

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Host must be a valid HTTP or HTTPS URL")
    if parsed.username or parsed.password:
        raise ValueError("Credentials must not be included in the URL")

    path = parsed.path.rstrip("/")
    return parsed._replace(path=path, params="", query="", fragment="").geturl()


def clean_value(value: Any) -> Any:
    """Clean values returned by the extender UI API."""
    if isinstance(value, str):
        return value.replace("<br>", " ").replace("<br/>", " ").strip()
    return value


class VerizonLteExtenderApi:
    """Manage a private aiohttp session and extender authentication."""

    def __init__(
        self,
        host: str,
        password: str,
        verify_ssl: bool,
        *,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the API client."""
        self.base_url = normalize_base_url(host)
        self._password = password
        self._verify_ssl = verify_ssl
        self._session = session
        self._owns_session = session is None
        self._auth_lock = asyncio.Lock()

    async def async_close(self) -> None:
        """Close the owned HTTP session."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def async_get_status(self) -> dict[str, Any]:
        """Return SIM/device status, refreshing authentication if required."""
        return await self._async_authenticated_get("webapi/simStatus")

    async def async_get_info(self) -> dict[str, Any]:
        """Return full product and feature information."""
        return await self._async_authenticated_get("webapi/info")

    async def async_get_gps(self) -> dict[str, Any]:
        """Return the extended GPS endpoint payload."""
        return await self._async_authenticated_get("webapi/gps")

    async def async_get_devices(self) -> dict[str, Any]:
        """Return the connected-devices endpoint payload."""
        return await self._async_authenticated_get("webapi/devices")

    async def async_get_performance(self) -> dict[str, Any]:
        """Return the performance endpoint payload."""
        return await self._async_authenticated_get("webapi/performance")

    async def async_validate(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Authenticate and fetch the data needed during config flow."""
        await self.async_authenticate(force=True)
        status = await self.async_get_status()
        info = await self.async_get_info()
        return status, info

    async def async_authenticate(self, *, force: bool = False) -> None:
        """Log in and capture the session cookies set by the extender."""
        async with self._auth_lock:
            if not force and self._has_session_token():
                return
            if force:
                self._clear_session_cookies()

            password_hash = hashlib.sha256(self._password.encode()).hexdigest()
            expires = int((time.time() + (30 * 24 * 60 * 60)) * 1000)

            # The firmware's jQuery UI sends form-encoded fields while declaring
            # application/json. Reproducing that quirk is required by model 4116G.
            data = await self._async_request_json(
                "POST",
                "webapi/login",
                data={"expires": str(expires), "password": password_hash},
                authenticated=False,
            )
            if data.get("result") != 1:
                message = str(data.get("message") or "Invalid credentials")
                raise VerizonLteExtenderAuthError(message)

            if not self._has_session_token():
                raise VerizonLteExtenderAuthError(
                    "Login succeeded but the extender did not issue a session token"
                )

    async def _async_authenticated_get(self, path: str) -> dict[str, Any]:
        """Make an authenticated request and retry once after refreshing."""
        if not self._has_session_token():
            await self.async_authenticate()

        for attempt in range(2):
            try:
                data = await self._async_request_json("GET", path, authenticated=True)
            except VerizonLteExtenderAuthError:
                if attempt:
                    raise
                await self.async_authenticate(force=True)
                continue

            if self._is_auth_failure(data):
                if attempt:
                    raise VerizonLteExtenderAuthError(
                        str(data.get("message") or "Session is invalid")
                    )
                await self.async_authenticate(force=True)
                continue
            return data

        raise VerizonLteExtenderAuthError("Unable to refresh the extender session")

    async def _async_request_json(
        self,
        method: str,
        path: str,
        *,
        data: Mapping[str, str] | None = None,
        authenticated: bool,
    ) -> dict[str, Any]:
        """Send one HTTP request and return a JSON object."""
        session = self._get_session()
        url = urljoin(f"{self.base_url}/", path)
        headers = {"X-Requested-With": "XMLHttpRequest"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if authenticated:
            token = self._xsrf_token()
            if not token:
                raise VerizonLteExtenderAuthError("The session token is missing")
            headers["X-XSRF-TOKEN"] = token

        try:
            async with session.request(
                method,
                url,
                data=data,
                headers=headers,
                ssl=self._verify_ssl,
            ) as response:
                if response.status in {401, 403}:
                    raise VerizonLteExtenderAuthError(
                        f"Authentication failed with HTTP {response.status}"
                    )
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except VerizonLteExtenderAuthError:
            raise
        except aiohttp.ClientConnectorCertificateError as err:
            raise VerizonLteExtenderSslError(
                "Unable to verify the extender SSL certificate"
            ) from err
        except TimeoutError as err:
            raise VerizonLteExtenderTimeoutError(
                f"Timed out connecting to {urlparse(self.base_url).netloc}"
            ) from err
        except aiohttp.ClientConnectorError as err:
            if isinstance(err.os_error, socket.gaierror):
                raise VerizonLteExtenderDnsError(
                    f"Unable to resolve {urlparse(self.base_url).hostname}"
                ) from err
            raise VerizonLteExtenderNetworkError(
                f"Unable to open a connection to {urlparse(self.base_url).netloc}"
            ) from err
        except aiohttp.ClientError as err:
            raise VerizonLteExtenderConnectionError(
                f"Unable to communicate with {urlparse(self.base_url).netloc}"
            ) from err
        except (ValueError, TypeError) as err:
            raise VerizonLteExtenderResponseError(
                "The extender returned an invalid JSON response"
            ) from err

        if not isinstance(payload, dict):
            raise VerizonLteExtenderResponseError(
                "The extender returned an unexpected response"
            )
        return payload

    def _get_session(self) -> aiohttp.ClientSession:
        """Create the private session on first use."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            )
            self._owns_session = True
        return self._session

    def _clear_session_cookies(self) -> None:
        """Discard stale authentication state before a forced login."""
        if self._session is not None:
            # This client owns a private session in production, so no unrelated
            # integration cookies can be removed here.
            self._session.cookie_jar.clear()

    def _cookies(self) -> Mapping[str, Any]:
        """Return cookies scoped to this extender."""
        if self._session is None:
            return {}
        return self._session.cookie_jar.filter_cookies(URL(self.base_url))

    def _xsrf_token(self) -> str | None:
        """Return the current XSRF token without logging it."""
        cookie = self._cookies().get("X-XSRF-TOKEN")
        return cookie.value if cookie else None

    def _has_session_token(self) -> bool:
        """Return whether the cookie jar contains the required session state."""
        cookies = self._cookies()
        return bool(cookies.get("X-XSRF-TOKEN") and cookies.get("Authtoken"))

    @staticmethod
    def _is_auth_failure(data: Mapping[str, Any]) -> bool:
        """Recognize the firmware's HTTP-200 authentication errors."""
        if any(
            isinstance(data.get(key), str)
            and data[key].strip().lower() == _AUTH_REDACTED_VALUE
            for key in _AUTH_REQUIRED_STATUS_FIELDS
        ):
            return True
        if data.get("result") in {401, 403}:
            return True
        if data.get("result") != 0:
            return False
        message = str(data.get("message") or "").lower()
        return any(marker in message for marker in _AUTH_ERROR_MARKERS)
