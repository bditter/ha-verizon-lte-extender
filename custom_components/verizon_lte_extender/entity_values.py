"""Human-readable values for Verizon LTE Extender entities."""

from __future__ import annotations

from typing import Any

CELL_TYPE_VALUES = {
    1: "All users allowed",
    2: "Members have priority",
    3: "Only members allowed",
}

GPS_SIGNAL_VALUES = {
    0: "Not acquired",
    1: "Acquired",
    2: "Time and location acquired from time server",
    3: "Time acquired; acquiring location",
    4: "Location acquired; acquiring time",
    5: "Acquiring time and location",
    6: "Time server synchronized",
    7: "Acquiring time from time server",
}

IP_MODE_VALUES = {
    0: "IPv4 only",
    1: "IPv6 only",
    2: "IPv4/IPv6",
}


def _as_int(value: Any) -> int | None:
    """Return an integer for numeric API values."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def four_g_signal_value(value: Any) -> str:
    """Translate the extender's service flag."""
    return "In Service" if _as_int(value) == 1 else "Not In Service"


def cell_type_value(value: Any) -> str:
    """Translate the extender's access policy."""
    number = _as_int(value)
    return CELL_TYPE_VALUES.get(number, f"Unknown ({value})")


def gps_signal_value(value: Any) -> str:
    """Translate the extender's GPS acquisition state."""
    number = _as_int(value)
    return GPS_SIGNAL_VALUES.get(number, f"Unknown ({value})")


def ip_mode_value(value: Any) -> str:
    """Translate the extender's enabled IP stack."""
    number = _as_int(value)
    return IP_MODE_VALUES.get(number, f"Unknown ({value})")
