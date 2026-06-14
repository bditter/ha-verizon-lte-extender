"""Verizon LTE Extender integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import VerizonLteExtenderApi
from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import VerizonLteExtenderCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Verizon LTE Extender from a config entry."""
    config = {**entry.data, **entry.options}
    api = VerizonLteExtenderApi(
        config[CONF_HOST],
        config[CONF_PASSWORD],
        config.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
    )
    coordinator = VerizonLteExtenderCoordinator(
        hass,
        api,
        config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False

    coordinator: VerizonLteExtenderCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.api.async_close()
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload an entry after its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
