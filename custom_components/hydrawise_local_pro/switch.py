from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HydrawiseLocalProConfigEntry
from .entity import ZoneEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HydrawiseLocalProConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([AutomaticSwitch(entry.runtime_data.coordinator)])


class AutomaticSwitch(ZoneEntity, SwitchEntity):
    _attr_name = "Bewässerungsautomatik"
    _attr_icon = "mdi:calendar-sync"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, next(iter(coordinator.data)))
        self._attr_unique_id = f"{coordinator.api.host}_automatic"

    @property
    def is_on(self) -> bool:
        return self.coordinator.automatic_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_automatic(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_automatic(False)
        self.async_write_ha_state()