"""Binary sensors for Verizon LTE Extender."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VerizonLteExtenderCoordinator
from .entity import VerizonLteExtenderEntity


@dataclass(frozen=True, kw_only=True)
class VerizonBinarySensorDescription(BinarySensorEntityDescription):
    """Describe an extender binary sensor."""


BINARY_SENSORS: tuple[VerizonBinarySensorDescription, ...] = (
    VerizonBinarySensorDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    VerizonBinarySensorDescription(
        key="gps_acquired",
        translation_key="gps_acquired",
        icon="mdi:crosshairs-gps",
    ),
    VerizonBinarySensorDescription(
        key="in_service",
        translation_key="in_service",
        icon="mdi:signal-4g",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up extender binary sensors."""
    coordinator: VerizonLteExtenderCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VerizonLteExtenderBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class VerizonLteExtenderBinarySensor(VerizonLteExtenderEntity, BinarySensorEntity):
    """Representation of an extender binary sensor."""

    entity_description: VerizonBinarySensorDescription

    def __init__(
        self,
        coordinator: VerizonLteExtenderCoordinator,
        entry: ConfigEntry,
        description: VerizonBinarySensorDescription,
    ) -> None:
        """Initialize a binary sensor."""
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Keep the online entity available so it can report failures."""
        if self.entity_description.key == "online":
            return True
        return super().available

    @property
    def is_on(self) -> bool:
        """Return the binary sensor state."""
        data = self.coordinator.data or {}
        result_ok = data.get("result") == 1
        if self.entity_description.key == "online":
            return self.coordinator.last_update_success and result_ok
        if self.entity_description.key == "gps_acquired":
            return data.get("gpsStatus") == "Location Acquired"
        return result_ok and data.get("FourGsignal") == 1
