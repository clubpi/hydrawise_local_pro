from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import HydrawiseLocalProConfigEntry

TO_REDACT = {"password"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HydrawiseLocalProConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data.coordinator
    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "last_update_success": coordinator.last_update_success,
        "selected_relays": sorted(coordinator.selected_relays or []),
        "zones": {
            relay: {
                "name": zone.name,
                "is_running": zone.is_running,
                "remaining_seconds": zone.remaining_seconds,
                "default_run_seconds": zone.default_run_seconds,
                "last_watered": zone.last_watered,
                "next_run": zone.next_run,
                "suspended": zone.suspended,
            }
            for relay, zone in coordinator.data.items()
        },
        "pending_relays": list(coordinator.pending_relays),
    }
