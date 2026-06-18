"""Tests for the Verizon LTE Extender API client."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
import types
import unittest
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import parse_qs

from aiohttp import web

PACKAGE_NAME = "custom_components.verizon_lte_extender"
PACKAGE_PATH = Path(__file__).parents[1] / "custom_components" / "verizon_lte_extender"
package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(PACKAGE_PATH)]
sys.modules[PACKAGE_NAME] = package


def load_module(name: str):
    """Load one integration module without importing Home Assistant."""
    module_name = f"{PACKAGE_NAME}.{name}"
    spec = importlib.util.spec_from_file_location(
        module_name, PACKAGE_PATH / f"{name}.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


load_module("const")
api_module = load_module("api")
VerizonLteExtenderApi = api_module.VerizonLteExtenderApi
clean_value = api_module.clean_value
normalize_base_url = api_module.normalize_base_url


@asynccontextmanager
async def extender_server(
    expired_response: dict | None = None,
) -> AsyncIterator[tuple[str, dict[str, int]]]:
    """Run a minimal extender API server."""
    state = {"logins": 0, "status_requests": 0}

    async def login(request: web.Request) -> web.Response:
        data = parse_qs(await request.text())
        assert request.content_type == "application/json"
        assert len(data["password"][0]) == 64
        assert data["password"][0] == hashlib.sha256(b"secret").hexdigest()
        state["logins"] += 1
        response = web.json_response({"result": 1, "message": ""})
        response.set_cookie("wfx_unq", f"session-{state['logins']}")
        response.set_cookie("X-XSRF-TOKEN", f"xsrf-{state['logins']}")
        response.set_cookie("Authtoken", f"auth-{state['logins']}")
        return response

    async def sim_status(request: web.Request) -> web.Response:
        state["status_requests"] += 1
        expected = f"xsrf-{state['logins']}"
        assert request.headers["X-Requested-With"] == "XMLHttpRequest"
        assert request.headers["X-XSRF-TOKEN"] == expected
        if state["status_requests"] == 1:
            return web.json_response(
                expired_response
                or {"result": 0, "message": "Sign in session is expired"}
            )
        return web.json_response(
            {
                "result": 1,
                "gpsStatus": "Location Acquired",
                "FourGsignal": 1,
                "SWver": "GA5.19<br>V0.5.019.2041",
            }
        )

    async def info(request: web.Request) -> web.Response:
        return web.json_response(
            {
                "result": 1,
                "feature": {
                    "base": {
                        "product": "4G LTE Network Extender",
                        "md": "4116G",
                    }
                },
            }
        )

    app = web.Application()
    app.router.add_post("/webapi/login", login)
    app.router.add_get("/webapi/simStatus", sim_status)
    app.router.add_get("/webapi/info", info)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    try:
        yield f"http://127.0.0.1:{port}", state
    finally:
        await runner.cleanup()


class ApiTests(unittest.IsolatedAsyncioTestCase):
    """Test API behavior."""

    async def test_authentication_refreshes_and_retries_once(self) -> None:
        """An expired session triggers one fresh login and request retry."""
        async with extender_server() as (host, state):
            api = VerizonLteExtenderApi(host, "secret", verify_ssl=False)
            try:
                status, info = await api.async_validate()
            finally:
                await api.async_close()

        self.assertEqual(status["result"], 1)
        self.assertEqual(info["feature"]["base"]["md"], "4116G")
        self.assertEqual(state["logins"], 2)
        self.assertEqual(state["status_requests"], 2)

    async def test_redacted_status_refreshes_authentication(self) -> None:
        """Protected placeholder values also trigger a fresh login."""
        redacted = {
            "result": 1,
            "operationMode": "Will display the data after login",
            "SWver": "Will display the data after login",
        }
        async with extender_server(redacted) as (host, state):
            api = VerizonLteExtenderApi(host, "secret", verify_ssl=False)
            try:
                status = await api.async_get_status()
            finally:
                await api.async_close()

        self.assertEqual(status["gpsStatus"], "Location Acquired")
        self.assertEqual(state["logins"], 2)
        self.assertEqual(state["status_requests"], 2)

    def test_url_and_value_cleanup(self) -> None:
        """URLs and UI-formatted values are normalized."""
        self.assertEqual(
            normalize_base_url("extender.example.net/"),
            "https://extender.example.net",
        )
        self.assertEqual(
            clean_value("GA5.19<br>V0.5.019.2041"),
            "GA5.19 V0.5.019.2041",
        )
