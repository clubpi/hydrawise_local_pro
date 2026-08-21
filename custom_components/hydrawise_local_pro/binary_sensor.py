from __future__ import annotations
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HydrawiseLocalProConfigEntry
from .entity import ZoneEntity


async def async_setup_entry(hass: HomeAssistant, entry: HydrawiseLocalProConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    c = entry.runtime_data.coordinator
    async_add_entities(Running(c, relay) for relay in c.data)


class Running(ZoneEntity, BinarySensorEntity):
    _attr_name = "Bewässerung"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator, relay):
        super().__init__(coordinator, relay)
        self._attr_unique_id = f"{coordinator.api.host}_{relay}_running"

    @property
    def is_on(self):
        z = self.zone
        return None if z is None else z.is_running
