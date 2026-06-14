"""Constants for the Verizon LTE Extender integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "verizon_lte_extender"
NAME: Final = "Verizon LTE Extender"
MANUFACTURER: Final = "Askey"
DEFAULT_MODEL: Final = "4116G"

CONF_HOST: Final = "host"
CONF_PASSWORD: Final = "password"
CONF_VERIFY_SSL: Final = "verify_ssl"
CONF_SCAN_INTERVAL: Final = "scan_interval"

DEFAULT_VERIFY_SSL: Final = False
DEFAULT_SCAN_INTERVAL: Final = 60
MIN_SCAN_INTERVAL: Final = 15
REQUEST_TIMEOUT: Final = 10

PLATFORMS: Final = ["sensor", "binary_sensor"]
