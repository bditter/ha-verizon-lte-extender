"""Shared entities for Verizon LTE Extender."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import clean_value
from .const import DEFAULT_MODEL, DOMAIN, MANUFACTURER, NAME
from .coordinator import VerizonLteExtenderCoordinator


class VerizonLteExtenderEntity(CoordinatorEntity[VerizonLteExtenderCoordinator]):
    """Base entity for a Verizon LTE Extender."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VerizonLteExtenderCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return extender device information."""
        status = self.coordinator.data or {}
        base: dict[str, Any] = self.coordinator.info.get("feature", {}).get("base", {})
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=base.get("md") or DEFAULT_MODEL,
            name=NAME,
            serial_number=status.get("serial") or None,
            sw_version=clean_value(status.get("SWver")) or None,
            configuration_url=self._entry.options.get(
                "host", self._entry.data.get("host")
            ),
        )
