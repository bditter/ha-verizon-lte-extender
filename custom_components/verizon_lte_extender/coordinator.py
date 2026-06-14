"""Data coordinator for the Verizon LTE Extender integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VerizonLteExtenderApi, VerizonLteExtenderError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class VerizonLteExtenderCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate status polling for one extender."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: VerizonLteExtenderApi,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self.info: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch current extender data."""
        try:
            status = await self.api.async_get_status()
            if not self.info:
                self.info = await self.api.async_get_info()
        except VerizonLteExtenderError as err:
            raise UpdateFailed(str(err)) from err

        if status.get("result") != 1:
            raise UpdateFailed(
                str(status.get("message") or "The extender reported an error")
            )
        return status
