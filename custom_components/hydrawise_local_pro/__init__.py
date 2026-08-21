from __future__ import annotations

from dataclasses import dataclass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HydrawiseLocalProApi
from .const import CONF_RELAYS, CONF_USERNAME, DEFAULT_USERNAME, DOMAIN, PLATFORMS
from .coordinator import HydrawiseLocalProCoordinator


@dataclass
class RuntimeData:
    coordinator: HydrawiseLocalProCoordinator


type HydrawiseLocalProConfigEntry = ConfigEntry[RuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: HydrawiseLocalProConfigEntry) -> bool:
    api = HydrawiseLocalProApi(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data.get(CONF_USERNAME, DEFAULT_USERNAME),
        entry.data[CONF_PASSWORD],
    )
    selected_relays = entry.options.get(CONF_RELAYS, entry.data.get(CONF_RELAYS))
    selected_relays_set = {int(relay) for relay in selected_relays} if selected_relays else None
    coordinator = HydrawiseLocalProCoordinator(hass, api, selected_relays_set)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = RuntimeData(coordinator)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: HydrawiseLocalProConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: HydrawiseLocalProConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.coordinator.async_shutdown()
    return unload_ok
