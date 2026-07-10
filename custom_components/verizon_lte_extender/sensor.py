"""Sensors for Verizon LTE Extender."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import clean_value
from .const import DOMAIN
from .coordinator import VerizonLteExtenderCoordinator
from .entity import VerizonLteExtenderEntity
from .entity_values import (
    cell_type_value,
    four_g_signal_value,
    gps_signal_value,
    ip_mode_value,
)

REMOVED_SENSOR_KEYS = (
    "ipsecIp",
    "paTemp",
    "FourGsignal",
    "beta_gps_endpoint",
    "beta_devices_endpoint",
    "beta_performance_endpoint",
)

@dataclass(frozen=True, kw_only=True)
class VerizonSensorDescription(SensorEntityDescription):
    """Describe a Verizon LTE Extender sensor."""

    data_key: str | None = None
    source: str | None = None
    value_fn: Callable[[Any], Any] = clean_value


def _as_int(value: Any) -> int | None:
    """Return a numeric integer sensor value."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    """Return a numeric float sensor value."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _current_downlink_bandwidth(value: Any) -> float | None:
    """Return the latest downlink bandwidth sample."""
    return _latest_bandwidth_value(value, "Downlink")


def _current_uplink_bandwidth(value: Any) -> float | None:
    """Return the latest uplink bandwidth sample."""
    return _latest_bandwidth_value(value, "Uplink")


def _latest_bandwidth_value(value: Any, key: str) -> float | None:
    """Return a numeric value from the latest bandwidth sample."""
    if not isinstance(value, list) or not value:
        return None
    latest = value[-1]
    if not isinstance(latest, Mapping):
        return None
    return _as_float(latest.get(key))


SENSORS: tuple[VerizonSensorDescription, ...] = (
    VerizonSensorDescription(
        key="gpsStatus",
        translation_key="gps_status",
        icon="mdi:crosshairs-gps",
    ),
    VerizonSensorDescription(
        key="activeUECount",
        translation_key="active_users",
        icon="mdi:account-network",
    ),
    VerizonSensorDescription(
        key="activeUECountTot",
        translation_key="total_active_users",
        icon="mdi:account-multiple",
    ),
    VerizonSensorDescription(
        key="operationMode",
        translation_key="operation_mode",
        icon="mdi:access-point-network",
    ),
    VerizonSensorDescription(
        key="uptime",
        translation_key="uptime",
        icon="mdi:timer-outline",
    ),
    VerizonSensorDescription(
        key="bhIpv4Addr",
        translation_key="backhaul_ipv4",
        icon="mdi:ip-network",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VerizonSensorDescription(
        key="bhIpv6Addr",
        translation_key="backhaul_ipv6",
        icon="mdi:ip-network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VerizonSensorDescription(
        key="SWver",
        translation_key="software_version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VerizonSensorDescription(
        key="cellType",
        translation_key="cell_type",
        icon="mdi:account-group-outline",
        value_fn=cell_type_value,
    ),
    VerizonSensorDescription(
        key="operationalStatus",
        data_key="FourGsignal",
        translation_key="operational_status",
        icon="mdi:access-point-check",
        value_fn=four_g_signal_value,
    ),
    VerizonSensorDescription(
        key="gpsSignal",
        translation_key="gps_signal",
        icon="mdi:satellite-variant",
        value_fn=gps_signal_value,
    ),
    VerizonSensorDescription(
        key="ipMode",
        translation_key="ip_mode",
        icon="mdi:network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=ip_mode_value,
    ),
    VerizonSensorDescription(
        key="gps_amount",
        data_key="gpsAmount",
        source="gps",
        translation_key="gps_amount",
        icon="mdi:satellite-uplink",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_int,
    ),
    VerizonSensorDescription(
        key="gps_amount_total",
        data_key="gpsAmountTot",
        source="gps",
        translation_key="gps_amount_total",
        icon="mdi:satellite-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_int,
    ),
    VerizonSensorDescription(
        key="peak_connected_users_last_hour",
        data_key="peakConnectedUsersLastHour",
        source="devices",
        translation_key="peak_connected_users_last_hour",
        icon="mdi:account-clock",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_int,
    ),
    VerizonSensorDescription(
        key="peak_connected_users_last_24_hours",
        data_key="peakConnectedUsersLast24Hours",
        source="devices",
        translation_key="peak_connected_users_last_24_hours",
        icon="mdi:account-clock-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_int,
    ),
    VerizonSensorDescription(
        key="peak_capacity_used_last_hour",
        data_key="peakCapacityUsedLastHour",
        source="devices",
        translation_key="peak_capacity_used_last_hour",
        icon="mdi:gauge",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_float,
    ),
    VerizonSensorDescription(
        key="peak_capacity_used_last_24_hours",
        data_key="peakCapacityUsedLast24Hours",
        source="devices",
        translation_key="peak_capacity_used_last_24_hours",
        icon="mdi:gauge-full",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_as_float,
    ),
    VerizonSensorDescription(
        key="current_downlink_bandwidth",
        data_key="CurrentBandWidth",
        source="performance",
        translation_key="current_downlink_bandwidth",
        icon="mdi:download-network",
        native_unit_of_measurement="Mbit/s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_current_downlink_bandwidth,
    ),
    VerizonSensorDescription(
        key="current_uplink_bandwidth",
        data_key="CurrentBandWidth",
        source="performance",
        translation_key="current_uplink_bandwidth",
        icon="mdi:upload-network",
        native_unit_of_measurement="Mbit/s",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_current_uplink_bandwidth,
    ),
    VerizonSensorDescription(
        key="hnbName",
        translation_key="hnb_name",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    VerizonSensorDescription(
        key="csgID",
        translation_key="csg_id",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    VerizonSensorDescription(
        key="serial",
        translation_key="serial",
        icon="mdi:barcode",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    VerizonSensorDescription(
        key="macAddress",
        translation_key="mac_address",
        icon="mdi:network-pos",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up extender sensors."""
    coordinator: VerizonLteExtenderCoordinator = hass.data[DOMAIN][entry.entry_id]
    registry = er.async_get(hass)
    for key in REMOVED_SENSOR_KEYS:
        entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_{key}"
        )
        if entity_id:
            registry.async_remove(entity_id)

    async_add_entities(
        VerizonLteExtenderSensor(coordinator, entry, description)
        for description in SENSORS
    )


class VerizonLteExtenderSensor(VerizonLteExtenderEntity, SensorEntity):
    """Representation of an extender sensor."""

    entity_description: VerizonSensorDescription

    def __init__(
        self,
        coordinator: VerizonLteExtenderCoordinator,
        entry: ConfigEntry,
        description: VerizonSensorDescription,
    ) -> None:
        """Initialize a sensor."""
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        data = (
            self.coordinator.data
            if self.entity_description.source is None
            else self.coordinator.extra_data.get(self.entity_description.source, {})
        )
        data_key = self.entity_description.data_key or self.entity_description.key
        value = data.get(data_key)
        if value in {None, "", "-"}:
            return None
        return self.entity_description.value_fn(value)
