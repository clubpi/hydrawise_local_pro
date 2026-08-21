from __future__ import annotations
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HydrawiseLocalProConfigEntry
from .entity import ZoneEntity


async def async_setup_entry(hass: HomeAssistant, entry: HydrawiseLocalProConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    c = entry.runtime_data.coordinator
    ents = []
    for relay in c.data:
        ents += [Remaining(c, relay), LastWatered(c, relay), NextRun(c, relay)]
    async_add_entities(ents)


class Remaining(ZoneEntity, SensorEntity):
    _attr_name = "Verbleibende Laufzeit"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION

    def __init__(self, coordinator, relay):
        super().__init__(coordinator, relay)
        self._attr_unique_id = f"{coordinator.api.host}_{relay}_remaining"

    @property
    def native_value(self):
        z = self.zone
        return 0 if z is None or not z.is_running else z.remaining_seconds


class LastWatered(ZoneEntity, SensorEntity):
    _attr_name = "Zuletzt bewässert"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, relay):
        super().__init__(coordinator, relay)
        self._attr_unique_id = f"{coordinator.api.host}_{relay}_last_watered"

    @property
    def native_value(self):
        z = self.zone
        return z.last_watered if z else None


class NextRun(ZoneEntity, SensorEntity):
    _attr_name = "Nächster Lauf"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, relay):
        super().__init__(coordinator, relay)
        self._attr_unique_id = f"{coordinator.api.host}_{relay}_next_run"

    @property
    def native_value(self):
        z = self.zone
        return z.next_run if z else None
