from __future__ import annotations
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HydrawiseLocalProConfigEntry
from .entity import ZoneEntity


async def async_setup_entry(hass: HomeAssistant, entry: HydrawiseLocalProConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    c = entry.runtime_data.coordinator
    async_add_entities(RunDuration(c, relay) for relay in c.data)


class RunDuration(ZoneEntity, NumberEntity):
    _attr_name = "Laufzeit"
    _attr_native_min_value = 1
    _attr_native_max_value = 180
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, relay):
        super().__init__(coordinator, relay)
        self._attr_unique_id = f"{coordinator.api.host}_{relay}_duration"

    @property
    def native_value(self):
        return round(self.coordinator.get_duration(self.relay) / 60)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_duration(self.relay, int(value * 60))
        self.async_write_ha_state()
