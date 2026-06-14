"""Config flow for Verizon LTE Extender."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult

from .api import (
    VerizonLteExtenderApi,
    VerizonLteExtenderAuthError,
    VerizonLteExtenderConnectionError,
    VerizonLteExtenderDnsError,
    VerizonLteExtenderError,
    VerizonLteExtenderNetworkError,
    VerizonLteExtenderSslError,
    VerizonLteExtenderTimeoutError,
    normalize_base_url,
)
from .const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    NAME,
)

_LOGGER = logging.getLogger(__name__)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    """Return the shared setup/options schema."""
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")): str,
            vol.Required(
                CONF_VERIFY_SSL,
                default=defaults.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
            ): bool,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
        }
    )


async def _validate_input(data: dict[str, Any]) -> dict[str, Any]:
    """Validate credentials and return discovered device information."""
    normalized = {**data, CONF_HOST: normalize_base_url(data[CONF_HOST])}
    api = VerizonLteExtenderApi(
        normalized[CONF_HOST],
        normalized[CONF_PASSWORD],
        normalized[CONF_VERIFY_SSL],
    )
    try:
        status, info = await api.async_validate()
    finally:
        await api.async_close()

    feature_base = info.get("feature", {}).get("base", {})
    return {
        "data": normalized,
        "serial": status.get("serial"),
        "title": feature_base.get("product") or NAME,
    }


class VerizonLteExtenderConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Verizon LTE Extender."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                validated = await _validate_input(user_input)
            except ValueError:
                errors["base"] = "invalid_host"
            except VerizonLteExtenderAuthError:
                errors["base"] = "invalid_auth"
            except VerizonLteExtenderSslError:
                errors["base"] = "ssl_error"
            except VerizonLteExtenderTimeoutError:
                errors["base"] = "timeout"
            except VerizonLteExtenderDnsError:
                errors["base"] = "dns_error"
            except VerizonLteExtenderNetworkError:
                errors["base"] = "network_error"
            except VerizonLteExtenderConnectionError:
                errors["base"] = "cannot_connect"
            except VerizonLteExtenderError:
                _LOGGER.exception("Unexpected extender response during setup")
                errors["base"] = "unknown"
            except Exception:
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(validated["data"][CONF_HOST])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=validated["title"],
                    data=validated["data"],
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input or {}),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return VerizonLteExtenderOptionsFlow()


class VerizonLteExtenderOptionsFlow(OptionsFlow):
    """Handle editable extender settings."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit connection and polling settings."""
        errors: dict[str, str] = {}
        current = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            try:
                validated = await _validate_input(user_input)
            except ValueError:
                errors["base"] = "invalid_host"
            except VerizonLteExtenderAuthError:
                errors["base"] = "invalid_auth"
            except VerizonLteExtenderSslError:
                errors["base"] = "ssl_error"
            except VerizonLteExtenderTimeoutError:
                errors["base"] = "timeout"
            except VerizonLteExtenderDnsError:
                errors["base"] = "dns_error"
            except VerizonLteExtenderNetworkError:
                errors["base"] = "network_error"
            except VerizonLteExtenderConnectionError:
                errors["base"] = "cannot_connect"
            except VerizonLteExtenderError:
                _LOGGER.exception("Unexpected extender response while saving options")
                errors["base"] = "unknown"
            except Exception:
                _LOGGER.exception("Unexpected error while saving options")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="",
                    data=validated["data"],
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(user_input or current),
            errors=errors,
        )
